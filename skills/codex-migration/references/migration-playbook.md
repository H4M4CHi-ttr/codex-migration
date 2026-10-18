# Migration playbook

## Inventory before choosing a route

Record the source/destination OS and host, physical directory identity, link and
mount targets, sync provider, active Codex home/settings directories, executable
version/hash, and relevant writers. Discover the real home from launch arguments,
environment and product evidence; `~/.codex` is a documented default, not proof.
The project workspace can live somewhere entirely different from the home.

Inspect the requested paths and known storage locations. Avoid scanning all disks
or printing environment variables, auth files, and raw process arguments that may
contain secrets. Check available space for the copy, a retained destination
version, and backups. Keep evidence outside the source/destination trees.

Prepare a scope record with:

| Field | Purpose |
| --- | --- |
| Source and destination physical roots | Prevent aliases, accidental self-copy, and destination-inside-source recursion. |
| Explicit path mappings and exclusions | Support selected folders, multiple roots, and different disks/hosts. |
| Fixed chat IDs and project root keys | Keep unrelated and excluded records unchanged. |
| Destination conflicts | Separate identical duplicates, new files, changed files, and missing source entries. |
| Version/schema/format and executable hashes | Bind the validation to the eventual live implementation. |
| Preserved properties and planned writes | Make cutover and recovery reviewable. |
| Backup, staging, and journal locations | Keep original evidence available after interruption. |

Path matching must be structural: `project` does not include `project-old`.
Handle slash style, case rules, drive roots, UNC paths, namespace prefixes, Unicode,
and nested mappings. Never apply mappings repeatedly to their own results. Check
destination collisions, case-only names, links, and unsupported filenames on the
target filesystem. The bundled mapper helps with lexical matching only.

## Transfer workspace files without losing either side

1. Enumerate included files, directories, links, and cloud placeholders without
   following directory links blindly. Review excludes before copying; generated
   files, ignored files, or dependencies may still be needed for continuation.
2. Retain source data. Copy into a new destination or reconcile existing data
   without silent overwrite. Back up each changed destination version before an
   authorized replacement. A source deletion does not authorize target deletion.
3. Record size, mtime, and SHA-256. Detect changes during hashing/copying and rerun
   the delta after writers quiet down. The final comparison must detect new,
   changed, unreadable, and disappearing files, not just count successful copies.
4. Verify SHA-256 for ordinary files, link type/target for links, directory
   structure including empty directories, required timestamps, permissions,
   executable bits/ACLs, and platform-specific metadata relevant to this request.
   If ACL inheritance differs but effective rights match, report both facts.

On Windows, use literal paths and native PowerShell/.NET or a copy tool with
explicitly reviewed flags. With robocopy, evaluate its documented exit code and
file comparison results; do not use `/MIR`, `/PURGE`, `/MOVE`, or broad exclusions
as an unreviewed migration shortcut. Do not treat a nonzero robocopy result alone
as proof of failure or success. Hashing verifies content, not ACLs or link targets.

OneDrive/Google Drive placeholders can have reparse tags without being ordinary
symlinks. Inspect tag/type and availability; do not skip every reparse point or
recursively follow every one. Reading/hashing can hydrate content and affect disk
space or sync traffic. If that action is outside authorization, inventory first
and resolve it. Do not start a sync client just to make a test pass. Report
unavailable bytes as a blocker. A destination in another synced folder is still a
synced destination; do not claim the user has left cloud storage.

For cross-host transfer, verify the receiving copy independently. Check path
syntax, case collisions, symlink support, owner identities and trust settings.
Do not assume a successful Windows copy is executable or semantically equivalent
on Linux/macOS.

## Compatibility junction or symlink

Use when keeping the old path satisfies the request and the host/filesystem/sync
provider supports the arrangement. It does not update persisted paths or remove
the old namespace.

After verified copy and quiescence, journal the exact paths, rename the original
directory to a unique backup, then create the link. Verify the link type, target,
and filesystem identity, and that the backup is a separate original. On link
creation failure, restore the original name only when the original location is
still absent and all identities match. Never recursively remove a path that may
resolve to the destination. Do not create a junction inside a sync provider's
managed tree without understanding its behavior and the user's intended outcome.

## Relocate CODEX_HOME or move to another computer

Determine whether the destination is empty or already has Codex state. Relocating
one home is different from merging two homes. Never overwrite or concatenate DBs,
session indexes, or JSONL files to merge accounts/histories. Detect duplicate IDs
and mismatched account/host ownership; use an established import path if available,
otherwise prepare a scoped, validated migration instead of inventing a merge.

Inventory actual sessions/archived sessions, state and history DBs, indexes,
settings, skills/plugins, external workspace paths, and necessary assets. Names
and layouts vary; do not invent a required catalog. Copying `history.jsonl` alone
does not prove full chat recovery. Use consistent SQLite snapshots and matched
rollouts. Capture live backups only under the state-editing rules.

Treat credentials, keyring items, OAuth grants, tokens, queued jobs, automations,
goals, and local integrations separately. Do not transfer or activate them merely
because the home is moving. Reauthenticate on the destination when appropriate.
Use restrictive backup permissions; do not publish data as diagnostic artifacts.

Changing `CODEX_HOME` for a shell is not proof that the desktop app, IDE, daemon,
or another launcher now uses it. Verify each launcher in scope using the installed
version's documented configuration and an observable source of state. Check
rollout paths stored in DBs as well as workspace references. Ensure the first
launch cannot rebuild indexes against missing or live source files. Keep source
state intact until native reads and the requested UI behavior pass.

## Cutover, interruption, and recovery

For file-only copy, a preliminary live copy is acceptable when final deltas are
checked. For live metadata edits, coordinate all writers sharing those files:
desktop/CLI/IDE/server and relevant jobs. Identify by home/executable/role;
matching process names alone is insufficient. Do not kill an updater, sandbox
service, isolated runtime, or unrelated application by name.

Use supported stop/start commands verified for the installed version. If the
current chat needs that backend, prepare a separate runner with a durable status
file and tested recovery before requesting the shutdown. Obtain any consequential
missing interruption authorization after preparation, without repeating approval
already supplied by the user.

Keep a durable journal with planned/applied file hashes, DB expected-before/after
values, append lengths/hashes, completion stages, and implementation identity.
Multi-file edits and a SQLite transaction are not one atomic operation. A restart
must distinguish unstarted, partial, committed, verified, and restored states.

Before recovery, stop writers again and compare the current state with the
journal. Restore only your exact recognized writes. Unknown appends, new turns,
different indexes, replaced files, or unrelated DB changes stop automatic
rollback. A whole-DB restore is suitable only when it cannot erase any newer
state and that fact is established under exclusion. Otherwise preserve the
current state and prepare a surgical reconciliation. Never truncate unknown
history or overwrite the live DB simply because a backup exists.

Retain original manifests and logs after moving evidence to an archive. Use an
external relocation map for old evidence paths; do not rewrite historical proof
or reuse an old passing test result for edited scripts.
