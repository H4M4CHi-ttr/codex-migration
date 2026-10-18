---
name: codex-migration
description: Migrate or recover local Codex chat workspaces, project paths, and CODEX_HOME data while preserving history, permissions, and relationships. Use for moving Codex files out of OneDrive or another synced folder, relocating selected chats or projects, moving between disks or computers, and investigating incomplete migrations (Codexチャット移行・保存先変更・移行復旧). Does not convert ChatGPT cloud conversations into local Codex chats.
---

# Codex Migration

Treat migration as two linked operations: transferring files and making Codex
resolve the intended workspace and saved state. A successful copy alone does not
prove that existing chats can use the destination.

## Establish what this request means

Resolve these from the request and current environment before asking questions:

- Source and destination host, operating system, actual paths, and account.
- Whether to move workspace files, change existing chat/project references,
  relocate `CODEX_HOME`, recover a previous attempt, or combine these.
- Included projects/chats, excluded subtrees, existing destination data, and
  whether the source should remain as a backup or a compatibility link.
- Whether the request authorizes execution or only investigation/a plan.

State important assumptions. Continue work that is already authorized; ask only
about unresolved consequential choices. A migration request does not authorize
discarding conflicting destination files, deleting source backups, copying
credentials to another account, or broadening access permissions.

This skill does not make filesystem access or a remote/cloud runtime available.
Use the tools actually available on the source host. If only exported ChatGPT
cloud history is available, explain the boundary instead of creating fake local
Codex records.

## Choose the smallest method that meets the requested outcome

| Situation | Route |
| --- | --- |
| Only workspace files need moving | Verified copy; references may remain unchanged only if that meets the request. |
| The old workspace path may remain usable | Consider a local compatibility junction/symlink after copy verification. Explain that stored paths remain old. |
| Existing chats/projects must point to new paths | Probe installed APIs and persistence; test every relevant chat class on isolated data. Use the validated API or a version-specific offline adapter. |
| `CODEX_HOME` or another computer is involved | Copy consistent state, inventory external dependencies, and configure the actual launchers. Follow the home/host section in the playbook. |
| An earlier migration is incomplete | Read its scope, manifest, journal, and current state first; resume or recover only recognized changes. |

Read [the migration playbook](references/migration-playbook.md) for the selected
route, file transfer, cloud folders, cutover, and recovery. Read
[state and validation](references/state-and-validation.md) before any saved-state
or permission edits. The [historical case](references/observed-case.md) explains
the evidence behind the method; it is not a current compatibility guarantee.

## Work through evidence gates

1. **Discover.** Identify the actual source, link targets, active `CODEX_HOME`,
   settings location, Codex executable/version, DB schemas, rollout format, and
   processes writing shared state. Distinguish workspace storage from chat state.
   Read names and metadata first; do not dump conversations or credentials.
2. **Fix the scope.** Record exact path mappings, exclusions, chat IDs, project
   root keys, intended edits, preservation invariants, and source/destination
   conflicts. Counts come from this request's inventory. New candidates must fit
   the existing authorization; leave excluded or ambiguous ones untouched.
3. **Copy and verify.** Preserve originals. Use stable source/destination hashes,
   handle links and cloud placeholders deliberately, and retain overwritten
   destination versions when an authorized update needs them. Recheck deltas.
4. **Prove the reference method.** Test on an isolated snapshot using the exact
   executable and schema. When no verified migration API exists, inspect the
   installed version's parser/source and build the smallest guarded adapter for
   this migration. Do not port an old state editor by changing its version string.
5. **Prepare cutover.** Save a reviewable scope and manifest, tested recovery,
   consistent backups, hashes, and journal. If shared writers include this chat's
   backend, prepare an external runner/handoff before stopping them. Do not stop
   the only controller and assume this turn will continue.
6. **Apply within authorization.** Quiesce relevant writers, acquire version- and
   platform-appropriate exclusion, capture the final consistent backup, and check
   all preconditions again. Apply only the prepared changes. An inability to
   exclude writers blocks live state editing, not independent preparation.
7. **Validate and restart.** Check files, persistence, native parsing/history,
   relationship/permission invariants, and representative UI behavior separately.
   Mark completion only for checks actually performed. Retain backups and record
   any remaining old paths that belong to historical text.

Preserve model/provider/effort, approval/reviewer settings, access allow/deny
rules, network rules, extra writable roots, IDs, project membership, relationships,
timestamps, and unrelated state unless the user requested their change. Map only
authorized path fields. Never globally replace a path in transcripts or state.

## Use the bundled probe when it helps

`scripts/migration_probe.py` needs Python 3.11+ and only the standard library.
It has **no apply, move, delete, or rollback command**. Resolve script paths from
this skill's directory; do not assume the current working directory.

```text
python <skill-dir>/scripts/migration_probe.py map-path --style windows --mapping "C:\old\project" "D:\work\project" --path "C:\old\project\src"
python <skill-dir>/scripts/migration_probe.py inspect-state --database <snapshot>/state_5.sqlite --old-root "C:\old\project" --style windows
```

The mapper is lexical and single-pass: it uses component boundaries, chooses the
longest mapping, and gives exclusions precedence. It does not resolve links or
prove disk identity. Windows comparisons ignore case by default; use
`--case-sensitive` for case-sensitive Windows directories. POSIX comparisons are
case-sensitive. `--mapping`, `--path`, `--exclude`, and `--old-root` can repeat.

The inspector opens the explicitly selected SQLite DB in read-only mode and
reports schema, counts, and candidate `threads.cwd` paths without titles, messages,
or policy values. Prefer a consistent snapshot: a live read is not a frozen
multi-file inventory, and SQLite may need WAL/SHM coordination. Candidate cwd
matches are **not complete scope**: inspect project roots, permissions, UI/config,
archived rollouts, and any references outside cwd separately. A successful probe
does not establish write compatibility. Do not select the newest `state_*.sqlite`
by filename alone when multiple databases exist.

## Report the actual result

Give the chosen method, included/excluded scope, backup and journal locations,
changes made, checks passed/failed/not run, remaining blockers, and next concrete
action. Separate byte-preserved history, effective saved settings, native read
results, and UI confirmation. Do not call an API read a tool-execution test.
Do not delete the source or migration evidence as automatic cleanup.
