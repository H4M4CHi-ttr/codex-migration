# Evidence behind this method

This is a sanitized synthesis of a private Windows migration archive dated
2026-10-04. The final report and selected implementation sections were reviewed
when authoring this skill on 2026-10-18. Original conversations, state, manifests,
account identifiers, personal paths and credentials are not distributed here.
Historical results below were reported by that archive; this repository's tests
do not rerun the historical production migration.

## What the archive established

- Workspace copy and reference migration were separate operations. A first
  directory/junction migration used a different source from the later correct
  OneDrive migration. Directory identity mattered more than similar names.
- The later workspace copy covered 143,990 files and 7,448,479,714 bytes.
  Live updates required a second pass: 79 additions and 34 changed destination
  files, with old destination versions retained. No mirror deletion was needed.
- A proposed API migration encountered child-setting restrictions and parent
  permission inheritance. The initial 175 chats included 61 children; handling
  only ordinary chats would not have satisfied the scope.
- The API pilot was restored to the required cwd/write/network behavior, but
  appended metadata, some read-only protections and four millisecond timestamps
  were not identical to the pre-pilot state. Later comparisons used the fresh
  post-pilot backup and disclosed that difference.
- The final authorized scope was 180 chats and eight project roots. On Codex
  App Server 0.160.0, an offline adapter appended thread-owned settings, changed
  scoped state DB fields and UI/config tokens, and retained existing history.
- Writers were stopped and files/databases excluded. SQLite backup APIs,
  expected-before SQL checks, staged hashes and a durable journal guarded writes.
- The archive reported 14 final tests, failure injection, idempotence, guarded
  rollback, native parsing, and 609 turns / 11,898 items with matching signatures.
  The user confirmed existing projects appeared. This was not a test of every
  chat's tools or a guarantee about future parent permission inheritance.
- Later evidence relocation preserved original records and used a separate path
  map. Previous absolute paths were not rewritten inside historical proof.

No count, folder exclusion, process exception, path, or version from this case is
a requirement for a new migration. Reuse the decision criteria and invariants.

## Version-pinned upstream references from the archive

These identify the implementation that was investigated in that historical case.
Read the corresponding source for the actually installed build before adapting it.

- [Owned settings and resume behavior](https://github.com/openai/codex/blob/rust-v0.160.0/codex-rs/app-server/src/request_processors/thread_processor.rs)
- [Protocol event definitions](https://github.com/openai/codex/blob/rust-v0.160.0/codex-rs/protocol/src/protocol.rs)
- [State metadata extraction](https://github.com/openai/codex/blob/rust-v0.160.0/codex-rs/state/src/extract.rs)
- [Daemon update loop](https://github.com/openai/codex/blob/rust-v0.160.0/codex-rs/app-server-daemon/src/update_loop.rs)

## Official documentation checked when authoring

- [Configuration and state locations](https://learn.chatgpt.com/docs/config-file/config-advanced): `CODEX_HOME` defaults to `~/.codex`; configuration, optional file credentials, history, and other local state live there.
- [Build skills](https://learn.chatgpt.com/docs/build-skills): skills are folders with `SKILL.md` and optional resources; the built-in installer can install from other repositories.

These pages establish the general storage/skill conventions, not a supported
all-version chat migration API or an offline editing contract.
