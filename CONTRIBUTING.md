# Contributing to ARES Usage Collection

## Commit policy

Each major implementation step must be committed after it is completed and validated, before work begins on the next major step.

A major implementation step includes:

- completing or materially changing a component
- adding or modifying a server script
- changing deployment configuration
- completing an integration
- changing the setup portal
- adding or modifying phone automation
- completing a test or documentation milestone

Before committing:

1. Review all changed files.
2. Run the relevant tests or validation.
3. Confirm that no credentials, tokens, live rclone configuration, or private data are included.
4. Update documentation where necessary.
5. Use a concise and descriptive commit message.

Avoid combining unrelated changes into one commit.

## AI-assisted development tracking

For major implementation steps completed with OpenAI/Codex assistance, record the model and outcome metadata in the Git commit. Prefer:

```bash
python3 tools/ai_task_tracker.py commit \
  --model terra \
  --type implementation \
  --retries 0 \
  --message "Describe completed step"
```

Use the same `AI-Task-ID` across commits when one logical task spans multiple commits or is escalated between models. Record an escalation rather than silently starting a new task so later analysis includes the cost of unsuccessful earlier attempts.

Default routing is Terra for routine implementation, Sol for harder reasoning/debugging, and Astra for persistent or high-consequence problems. Do not escalate solely because a task is large.

See `docs/AI_MODEL_TRACKING.md` for the tracking schema, routing policy, export command, evaluation metrics, and limitations.
