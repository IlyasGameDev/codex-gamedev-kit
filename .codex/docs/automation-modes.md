# Automation modes

`modes.automation` changes discussion style, not sandbox, hooks, approvals,
network access, or user authorization. Read `codex-runtime.md`; it takes
precedence over inherited “May I write?” examples.

```bash
bash .codex/hooks/yaml-helper.sh resolve_config --keys automation,automation_always_ask
```

The shipped project selects `guided`. Older configurations with no value use
the helper's conservative `collaborative` fallback. `$settings --local` can
change personal preferences without modifying shared configuration.

| Mode | Behavior |
| --- | --- |
| `collaborative` | Discuss significant unresolved choices and show concrete drafts at requested milestones. Existing authorization covers routine edits. |
| `guided` | State important assumptions and implement requested work. Ask only about material scope or outcome choices. |
| `autonomous` | Make routine decisions, record significant ones, and complete the authorized workflow. |

## Universal rules

- An implementation/fix/workflow request authorizes ordinary reversible work.
- Check authorization for scope expansion, destruction, publication, messages,
  purchases, and other external actions. Never re-ask an already settled decision.
- `automation_always_ask` reminds you to check authorization; it does not override
  a user's explicit instruction or create redundant confirmation steps.
- Skipped optional input calls for a reasonable assumption when possible.
- Use a question tool only if available. Otherwise ask in prose. Subagents send
  questions to the parent instead of blocking their clear independent work.
- Prepare reviewable work before requesting a necessary final decision.

Record significant autonomous choices with `log_decision` in
`.codex/hooks/yaml-helper.sh` or a concise checkpoint. Keep decisions, reasons,
and evidence; never record secrets or treat an assumption as fact.
