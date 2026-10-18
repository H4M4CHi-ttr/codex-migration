from contextlib import closing, redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/codex-migration/scripts/migration_probe.py"
spec = importlib.util.spec_from_file_location("migration_probe", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class PathMappingTests(unittest.TestCase):
    def mapped(self, path, mappings=None, **kwargs):
        return probe.map_path(path, mappings or [(r"C:\old\project", r"D:\work\project")],
                              style=kwargs.pop("style", "windows"), **kwargs)

    def test_component_descendant(self):
        self.assertEqual(self.mapped(r"C:\old\project\src")["mapped_path"], r"D:\work\project\src")

    def test_equal_root_and_slash_case(self):
        self.assertEqual(self.mapped("c:/OLD/project/")["mapped_path"], r"D:\work\project")

    def test_neighbor_is_not_a_descendant(self):
        original = r"C:\old\project-other\src"
        self.assertEqual(self.mapped(original)["mapped_path"], original)
        self.assertIsNone(self.mapped(original)["matched_source"])

    def test_exclusion_overrides_more_specific_mapping(self):
        original = r"C:\old\project\keep\file"
        result = self.mapped(original, [(r"C:\old\project\keep", r"D:\special")],
                             exclude=[r"C:\old\project"])
        self.assertTrue(result["excluded"])
        self.assertEqual(result["mapped_path"], original)

    def test_exclusion_boundary(self):
        result = self.mapped(r"C:\old\project\keep-other", exclude=[r"C:\old\project\keep"])
        self.assertFalse(result["excluded"])
        self.assertEqual(result["mapped_path"], r"D:\work\project\keep-other")

    def test_longest_source_wins(self):
        result = self.mapped(r"C:\old\project\nested\src", [
            (r"C:\old\project", r"D:\main"),
            (r"C:\old\project\nested", r"E:\nested"),
        ])
        self.assertEqual(result["mapped_path"], r"E:\nested\src")

    def test_mapping_is_not_cascaded(self):
        result = self.mapped(r"C:\old\project\x", [
            (r"C:\old\project", r"D:\next"), (r"D:\next", r"E:\last"),
        ])
        self.assertEqual(result["mapped_path"], r"D:\next\x")

    def test_posix_is_case_sensitive(self):
        result = self.mapped("/old/Project/src", [("/old/project", "/new/project")], style="posix")
        self.assertIsNone(result["matched_source"])
        result = self.mapped("/old/project/src", [("/old/project", "/new/project")], style="posix")
        self.assertEqual(result["mapped_path"], "/new/project/src")

    def test_windows_can_be_case_sensitive(self):
        result = self.mapped(r"C:\old\Project\src", case_sensitive=True)
        self.assertIsNone(result["matched_source"])

    def test_unicode_and_spaces(self):
        result = self.mapped(r"C:\旧 フォルダ\記事\図.png", [(r"C:\旧 フォルダ", r"D:\新 保存先")])
        self.assertEqual(result["mapped_path"], r"D:\新 保存先\記事\図.png")

    def test_unc(self):
        result = self.mapped(r"\\server\share\old\src", [(r"\\server\share\old", r"\\other\share\new")])
        self.assertEqual(result["mapped_path"], r"\\other\share\new\src")

    def test_extended_drive_namespace(self):
        self.assertEqual(self.mapped(r"\\?\C:\old\project\src")["mapped_path"], r"D:\work\project\src")

    def test_extended_unc_namespace(self):
        result = self.mapped(r"\\?\UNC\server\share\old\src", [(r"\\server\share\old", r"D:\new")])
        self.assertEqual(result["mapped_path"], r"D:\new\src")

    def test_drive_and_posix_roots(self):
        self.assertEqual(self.mapped("C:/src", [("C:/", "D:/")])["mapped_path"], r"D:\src")
        self.assertEqual(self.mapped("/src", [("/", "/new")], style="posix")["mapped_path"], "/new/src")

    def test_rejects_relative_device_and_dot_paths(self):
        for value in ["relative", "C:relative", r"\rooted", r"C:\old\..\project", r"C:\old\.\project",
                      "C:/nul\0path", r"\\.\PhysicalDrive0"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.mapped(value)

    def test_rejects_posix_parent_path(self):
        with self.assertRaises(ValueError):
            self.mapped("/old/../project", [("/old", "/new")], style="posix")

    def test_rejects_conflicting_duplicate_mapping(self):
        with self.assertRaises(ValueError):
            self.mapped(r"C:\old\project", [(r"C:\old\project", r"D:\one"),
                                                ("c:/old/project", r"D:\two")])

    def test_validates_destination_and_exclusion(self):
        with self.assertRaises(ValueError):
            self.mapped(r"C:\old\project", [(r"C:\old\project", "relative")])
        with self.assertRaises(ValueError):
            self.mapped(r"C:\old\project", exclude=["relative"])


class StateInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "snapshot.sqlite"
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("CREATE TABLE threads (id TEXT, cwd TEXT, rollout_path TEXT, title TEXT, sandbox_policy TEXT)")
            connection.executemany("INSERT INTO threads VALUES (?,?,?,?,?)", [
                ("included", r"C:\old\project\src", "copied/session.jsonl", "PRIVATE_TITLE", "PRIVATE_POLICY"),
                ("neighbor", r"C:\old\project-other", "other/session.jsonl", "PRIVATE_TITLE", "PRIVATE_POLICY"),
                ("second", r"E:\selected", "second/session.jsonl", "PRIVATE_TITLE", "PRIVATE_POLICY"),
                ("unknown", None, None, "PRIVATE_TITLE", "PRIVATE_POLICY"),
            ])
            connection.execute('CREATE TABLE "odd""table" (message TEXT)')
            connection.execute('INSERT INTO "odd""table" VALUES (?)', ("PRIVATE_MESSAGE",))

    def inspect(self, **kwargs):
        return probe.inspect_state(self.db, [r"C:\old\project"], style="windows", **kwargs)

    def test_candidates_use_boundaries(self):
        report = self.inspect()
        self.assertEqual([row["id"] for row in report["candidates"]], ["included"])
        self.assertEqual(report["unclassified_thread_ids"], ["unknown"])
        self.assertEqual(report["thread_rows_scanned"], 4)
        self.assertFalse(report["scope_complete"])

    def test_multiple_roots(self):
        report = probe.inspect_state(self.db, [r"C:\old\project", r"E:\selected"], style="windows")
        self.assertEqual([row["id"] for row in report["candidates"]], ["included", "second"])

    def test_no_message_title_or_policy_values(self):
        serialized = json.dumps(self.inspect())
        for secret in ["PRIVATE_TITLE", "PRIVATE_POLICY", "PRIVATE_MESSAGE"]:
            self.assertNotIn(secret, serialized)

    def test_database_bytes_and_mtime_unchanged(self):
        before = (self.db.read_bytes(), self.db.stat().st_mtime_ns)
        self.inspect()
        self.assertEqual((self.db.read_bytes(), self.db.stat().st_mtime_ns), before)

    def test_schema_fingerprint_changes_on_schema_change(self):
        before = self.inspect()["schema_sha256"]
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("ALTER TABLE threads ADD COLUMN new_field TEXT")
        self.assertNotEqual(self.inspect()["schema_sha256"], before)

    def test_missing_database_is_not_created(self):
        missing = self.db.with_name("missing.sqlite")
        with self.assertRaises(FileNotFoundError):
            probe.inspect_state(missing, ["/old"], style="posix")
        self.assertFalse(missing.exists())

    def test_unrecognized_schema_reports_unavailable(self):
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("DROP TABLE threads")
        report = self.inspect()
        self.assertFalse(report["candidate_query_available"])
        self.assertIn("schema_sha256", report)

    def test_empty_scope_rejected(self):
        with self.assertRaises(ValueError):
            probe.inspect_state(self.db, [], style="windows")

    def test_reads_committed_wal_rows(self):
        with closing(sqlite3.connect(self.db)) as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("INSERT INTO threads VALUES (?,?,?,?,?)", (
                "wal-row", r"C:\old\project\new", None, "PRIVATE_TITLE", "PRIVATE_POLICY",
            ))
            connection.commit()
            self.assertTrue(Path(str(self.db) + "-wal").exists())
            self.assertEqual([row["id"] for row in self.inspect()["candidates"]], ["included", "wal-row"])

    def test_database_uri_handles_hash_and_spaces(self):
        renamed = self.db.with_name("snapshot # copy.sqlite")
        self.db.rename(renamed)
        report = probe.inspect_state(renamed, [r"C:\old\project"], style="windows")
        self.assertEqual(len(report["candidates"]), 1)

    def test_cli_unrecognized_schema_has_nonzero_exit(self):
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("DROP TABLE threads")
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = probe.main(["inspect-state", "--database", str(self.db), "--old-root", r"C:\old", "--style", "windows"])
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(stdout.getvalue())["candidate_query_available"])

    def test_cli_and_failure_exit_codes(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = probe.main(["inspect-state", "--database", str(self.db), "--old-root", r"C:\old\project", "--style", "windows"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(stdout.getvalue())["inspection_only"])
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(probe.main(["map-path", "--mapping", "/old", "/new", "--path", "relative", "--style", "posix"]), 2)


if __name__ == "__main__":
    unittest.main()
