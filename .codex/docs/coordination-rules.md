# Agent coordination

Read `codex-runtime.md` for the platform contract. A role supplies domain
expertise; it does not require spawning an agent for every small task.

1. Choose the smallest useful team using `team.size` and task complexity.
2. Directors own cross-domain decisions; leads coordinate specialists. The parent
   may delegate directly when a task is already well-defined.
3. Give each worker owned files and outputs. Serialize edits to the same files.
4. Spawn independent work together, collect results, then run dependent work.
   Respect host depth and concurrency limits; queue or work sequentially.
5. Escalate design disagreements to `creative-director`, technical disagreements
   to `technical-director`, and scheduling issues to `producer`.
6. Read large documents by heading using `rg` and bounded reads. The helper
   `.codex/scripts/read-guard.sh` can identify sections.
7. Keep remote publication and messages within the user's authorization.
8. Verify artifacts and evidence. A worker saying “done” is not proof a test ran.

Native configs in `.codex/agents/` are generated from `.codex/roles/` with
`python3 tools/studio.py sync-agents`. All roles inherit the session model.
See `model-tiers.md` before deliberately choosing overrides.

Use native subagents when supported. If a named role is unavailable, brief a
generic worker with its guide. If delegation is unavailable, perform the domain
passes in the parent and disclose it. Do not invent a shared team service or
provider-specific task APIs.
