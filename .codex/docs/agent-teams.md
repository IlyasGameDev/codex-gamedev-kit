# Teams in Codex

The `team-*` skills are workflows coordinated by a parent Codex session. They use
native subagents when available. They require no experimental environment
variable, separate independent chats, or external shared task-list service.

Follow `coordination-rules.md` and native roles under `.codex/agents/`. Default
maximum concurrency is four; a host may allow fewer. Gather results before
starting dependent phases.

Give workers separate files, or explicitly create a Git worktree when useful.
Worktrees are optional and never created by a metadata flag. Do not copy secrets.
Preserve uncommitted work; identify files a new checkout cannot see.

Without delegation, run the needed role passes sequentially and state that
limitation. Keep the same expertise and acceptance checks.
