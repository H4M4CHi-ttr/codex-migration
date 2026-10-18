#!/usr/bin/env python3
"""Read-only path and SQLite probes. No persistence editing or file transfer."""

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import sqlite3
import sys


def absolute_path(value, style):
    if not isinstance(value, str) or not value or "\0" in value:
        raise ValueError("Expected a nonempty path without NUL characters")
    if style == "windows":
        value = value.replace("/", "\\")
        if value.startswith("\\\\.\\"):
            raise ValueError("Windows device paths are not supported")
        if value[:8].lower() == "\\\\?\\unc\\":
            value = "\\\\" + value[8:]
        elif value.startswith("\\\\?\\"):
            value = value[4:]
        parts = value.split("\\")
        parsed = PureWindowsPath(value)
    elif style == "posix":
        parts = value.split("/")
        parsed = PurePosixPath(value)
    else:
        raise ValueError("Path style must be windows or posix")
    if any(part in {".", ".."} for part in parts) or not parsed.is_absolute():
        raise ValueError("Expected an absolute path without dot segments")
    return parsed


def path_key(path, style, case_sensitive):
    if style == "windows" and not case_sensitive:
        return tuple(part.casefold() for part in path.parts)
    return path.parts


def is_under(candidate, root):
    return candidate[:len(root)] == root


def map_path(value, mappings, *, style, case_sensitive=False, exclude=()):
    """Preview one structural replacement; never cascade a mapped result."""
    path = absolute_path(value, style)
    key = path_key(path, style, case_sensitive)
    compiled = {}
    for source, destination in mappings:
        src = absolute_path(source, style)
        dst = absolute_path(destination, style)
        src_key = path_key(src, style, case_sensitive)
        if src_key in compiled:
            previous = compiled[src_key][1]
            if path_key(previous, style, case_sensitive) != path_key(dst, style, case_sensitive):
                raise ValueError("One source has conflicting destination mappings")
        compiled[src_key] = (src, dst)
    if not compiled:
        raise ValueError("At least one mapping is required")
    excluded = [
        path_key(absolute_path(root, style), style, case_sensitive) for root in exclude
    ]
    result = {
        "path": value, "mapped_path": value, "matched_source": None,
        "excluded": any(is_under(key, root) for root in excluded),
    }
    if not result["excluded"]:
        for src_key in sorted(compiled, key=len, reverse=True):
            if is_under(key, src_key):
                src, dst = compiled[src_key]
                result["matched_source"] = str(src)
                result["mapped_path"] = str(dst.joinpath(*path.parts[len(src.parts):]))
                break
    return result


def quote_identifier(name):
    return '"' + name.replace('"', '""') + '"'


def inspect_state(database, roots, *, style, case_sensitive=False):
    if not roots:
        raise ValueError("At least one old root is required to bound inspection")
    root_keys = [path_key(absolute_path(root, style), style, case_sensitive) for root in roots]
    database = Path(database).expanduser().resolve(strict=True)
    if not database.is_file():
        raise ValueError("Expected an existing SQLite database file")
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5)) as connection:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        schema = connection.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name"
        ).fetchall()
        tables = []
        for kind, name, _, _ in schema:
            if kind != "table" or name.startswith("sqlite_"):
                continue
            identifier = quote_identifier(name)
            columns = [row[1] for row in connection.execute(f"PRAGMA table_info({identifier})")]
            count = connection.execute(f"SELECT COUNT(*) FROM {identifier}").fetchone()[0]
            tables.append({"name": name, "columns": columns, "row_count": count})
        report = {
            "inspection_only": True,
            "scope_complete": False,
            "database": str(database),
            "user_version": connection.execute("PRAGMA user_version").fetchone()[0],
            "schema_sha256": hashlib.sha256(json.dumps(schema, ensure_ascii=True).encode()).hexdigest(),
            "tables": tables,
            "candidate_query_available": False,
            "candidates": [],
            "unclassified_thread_ids": [],
        }
        columns = next((table["columns"] for table in tables if table["name"] == "threads"), [])
        if not {"id", "cwd"}.issubset(columns):
            report["reason"] = "Candidate query requires threads.id and threads.cwd; inspect this build's schema"
            return report
        report["candidate_query_available"] = True
        selected = [
            name for name in ("id", "cwd", "rollout_path", "parent_thread_id", "forked_from_id")
            if name in columns
        ]
        fields = ",".join(quote_identifier(name) for name in selected)
        scanned = 0
        for values in connection.execute(f"SELECT {fields} FROM threads ORDER BY id"):
            scanned += 1
            row = dict(zip(selected, values))
            try:
                key = path_key(absolute_path(row["cwd"], style), style, case_sensitive)
            except ValueError:
                report["unclassified_thread_ids"].append(row["id"])
                continue
            if any(is_under(key, root) for root in root_keys):
                report["candidates"].append(row)
        report["thread_rows_scanned"] = scanned
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    mapper = commands.add_parser("map-path", help="Preview structural mappings without touching files")
    mapper.add_argument("--mapping", nargs=2, action="append", required=True, metavar=("SOURCE", "DESTINATION"))
    mapper.add_argument("--path", action="append", required=True)
    mapper.add_argument("--exclude", action="append", default=[])
    inspector = commands.add_parser("inspect-state", help="Inspect an explicit DB, preferably a consistent snapshot")
    inspector.add_argument("--database", required=True)
    inspector.add_argument("--old-root", action="append", required=True)
    for command in (mapper, inspector):
        command.add_argument("--style", choices=("windows", "posix"), required=True)
        command.add_argument("--case-sensitive", action="store_true", help="Use case-sensitive Windows path comparison")
    args = parser.parse_args(argv)
    try:
        if args.command == "map-path":
            result = [
                map_path(path, args.mapping, style=args.style,
                         case_sensitive=args.case_sensitive, exclude=args.exclude)
                for path in args.path
            ]
        else:
            result = inspect_state(args.database, args.old_root, style=args.style,
                                   case_sensitive=args.case_sensitive)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        if args.command == "inspect-state" and not result["candidate_query_available"]:
            return 2
        return 0
    except (ValueError, OSError, sqlite3.Error) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
