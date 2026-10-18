# Saved-state edits and validation

## Determine the contract for the installed build

Inspect installed command help, API schemas and the matching official source or
native parser. Record version/hash and schema fingerprints. APIs that change
cwd or project roots are not automatically migration APIs. Test their side
effects and every relevant class: ordinary, child, forked, archived, multi-root,
and any missing-settings fallback actually present in the scope.

Probe on disposable data. `thread/resume`, settings updates, and even some read
workflows may load sessions, append metadata, inherit permissions, or rebuild
state. Suppressing returned turns is not a guarantee of no side effects. No model
turn or tool execution is needed for structural/history validation.

If a supported API preserves all required invariants, use it with scoped backups
and read-back validation. Otherwise continue investigating a version-specific
offline adapter. The historical 0.160.0 technique below is evidence, not a generic
apply algorithm or a promise for newer versions.

## Build and validate only the adapter this migration needs

Discover actual DB locations/table columns, JSONL event fields and settings
ownership. Do not assume `state_5.sqlite`, a particular permission schema, or
`thread_settings_applied` exists. Treat unknown policy forms or required settings
as unresolved; do not normalize them to a less restrictive format.

For the observed 0.160.0 format:

- Locate the latest `thread_settings_applied` belonging to the target thread ID,
  rather than blindly taking the last settings event in a copied/forked rollout.
- A `turn_context` fallback is usable only when all required saved settings can
  be reconstructed and matched to DB settings. Preserve optional/non-path values.
- A new owned settings event can express the new paths without rewriting earlier
  JSONL bytes. Validate its ordinal, required fields and native recognition.
- Update only authorized `threads.cwd`, path-bearing policy fields, selected
  `project_roots.path`, and necessary scoped UI/config references. Keep history
  projection DBs/byte-offset indexes intact and let a verified native path handle
  any derived refresh.

For other builds, establish the equivalent supported behavior before writing.
If no safe adapter can be proven, finish copy/plan/recovery preparation and report
the exact missing evidence. Do not downgrade permissions or ignore child chats
to claim a complete migration.

Parse known settings structures. Apply component-aware mapping only to authorized
path fields and scoped keys, including dictionary keys where the format uses
paths as keys. Preserve comments, BOM/newline style, drafts/prompts, unrelated
strings, and non-path settings. Avoid rewriting an entire JSON/TOML file when a
validated token/section edit preserves unrelated bytes.

Permission checks cover both allow and deny rules, network rules, special roots,
read-only protections, and multiple writable roots. Map only roots inside scope;
extra visualization or work directories may need to remain unchanged. If the
mapping merges distinct roots, broadens access, crosses account boundaries, or
changes effective deny precedence, resolve that consequence explicitly.

## Backups and live application

Use SQLite's backup API or an established consistent snapshot facility. Copying
only a live DB file can lose committed WAL data; copying/removing WAL/SHM files
piecemeal is not a recovery method. Separate DB snapshots do not establish a
consistent snapshot of several DBs, rollouts, and configuration files. For that,
quiesce writers and hold the relevant exclusion through final capture/apply.

An adapter must enforce these preconditions in code, not only instructions:

- Exact scope, executable/schema and validated implementation hashes match.
- Paths and rollout references stay inside declared physical roots; symlink or
  junction resolution cannot escape into the live home from a lab.
- Before values, file hashes and history prefixes still match the final backup.
- Shared file/coordination locks and SQLite transactions establish exclusion;
  a process list by itself does not establish it.
- SQL changes compare expected old values and affect exactly the intended rows.
- Each file replacement or append is durable and journaled, including partial
  writes and a crash before/after the SQL commit.
- Re-running a completed manifest verifies the post-state and adds nothing.
  Partial state requires recognized recovery; it is not treated as a fresh run.

## Isolated testing must not reach live state

Use a fresh home and isolated settings/config directory. Repoint all copied DB
rollout references to copied files; inspect links, attachments, and other absolute
references. Set every relevant process's home explicitly. Do not assume a fresh
environment variable overrides a launcher's settings path.

Exclude credentials, OAuth state, runnable queues/automations/goals and live
integration configuration. Disable MCP/plugins, hooks, model calls, tools, and
network via controls supported by that build and an isolation boundary where
available. A dummy model name or dead endpoint alone is insufficient isolation.
Do not resume a live child chat to test permission preservation.

## Checks required before live state editing

| Check | Required evidence |
| --- | --- |
| Scope/path mapping | Exclusions, neighboring names, slash/case/Unicode, nested roots, collision rejection, and outside-scope stability. |
| Policies/settings | Original semantics after only the intended path map; unchanged model/provider/effort/approvals and extra roots. |
| Relationships | Target-owned session metadata plus native parent/fork interpretation; do not infer all parent kinds from `threads.source`. |
| History | Original rollout prefix bytes, stable IDs/counts/content signatures, complete pagination, and fork-inherited history against a native baseline. |
| Native reconstruction | DB-free parsing when that build supports it, plus copied-DB reads; a warmed cache must not hide missing persisted settings. |
| Unrelated data | Target IDs/membership/timestamps and unrelated rows/columns/config/history indexes unchanged from the final backup. |
| Recovery | Injected failure during append/settings writes, before commit and after commit; recognized partial writes restore, unknown changes are retained/refused. |
| Idempotence | A second apply produces no duplicate events or drift. |

Hash history signatures locally instead of exposing message text. A native API
baseline for forked history can include ancestor items absent from the fork's own
index rows; compare equivalent views. Distinguish original byte preservation from
newly appended metadata. If an earlier API pilot already changed data, identify
that baseline and residual differences rather than claiming pre-pilot identity.

After cutover, validate a fresh isolated snapshot of the actual migrated data,
then restart the relevant app/server and inspect requested UI behavior. Record
whether representative chats can open and which roots they show. A user-confirmed
project list, full native history read, and actual tool operation are different
checks; report each at its real coverage. Do not execute tools merely to make a
structural migration test appear more complete.
