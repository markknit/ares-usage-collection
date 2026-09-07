# AI model effectiveness tracking

## Purpose

Measure which OpenAI model completes ARES development work most efficiently in practice. The primary metric is **credits per successful task**, not raw token price or subjective impressions.

The system deliberately separates two data sources:

1. **Repository outcome metadata** records what work was attempted, the model used, retries, escalation, outcome, and resulting commit.
2. **OpenAI usage exports** remain the authoritative source for tokens/credits and are joined later when the available export fields support a reliable match.

Do not invent or estimate a join key. Until OpenAI's export schema has been verified, cost attribution to an individual task should be labelled provisional unless it can be matched reliably.

## Default model-routing policy

- **Terra:** routine repository inspection, straightforward implementation, configuration edits, tests, documentation, and clean execution of an established plan.
- **Sol:** non-obvious debugging, cross-component reasoning, design of substantial changes, or escalation after Terra makes repeated unsuccessful attempts.
- **Astra:** persistent problems after Sol, consequential/difficult-to-reverse architecture decisions, or independent review of high-risk changes.

Do not escalate merely because a task is large. Escalate when reasoning difficulty or repeated rework is the bottleneck.

## What is recorded

Every AI-assisted major implementation commit should include these Git trailers:

- `AI-Task-ID`
- `AI-Model`
- `AI-Task-Type`
- `AI-Retries`
- `AI-Escalated`
- `AI-Outcome`
- `AI-Escalated-From` when applicable
- `AI-Escalation-Reason` when applicable

The task ID is intended to connect multiple commits belonging to one logical task. A task that escalates from Terra to Sol should retain the same task ID so the eventual analysis can count the full cost of the task rather than treating the escalation as a separate success.

## Recommended task types

Use a small stable vocabulary where possible:

- `implementation`
- `debugging`
- `config`
- `tests`
- `documentation`
- `architecture`
- `review`
- `research`

## Creating a tracked commit

Stage and validate the intended files first, then run:

```bash
python3 tools/ai_task_tracker.py commit \
  --model terra \
  --type implementation \
  --retries 0 \
  --message "Implement school sync validation"
```

For an escalated task, preserve its task ID:

```bash
python3 tools/ai_task_tracker.py commit \
  --task-id ares-20260907-120000-abcdef \
  --model sol \
  --type debugging \
  --retries 2 \
  --escalated-from terra \
  --reason "Cross-component failure remained unresolved" \
  --message "Resolve sync validation failure"
```

The tool commits staged files only by default. `--all` is available but should be used deliberately.

## Exporting repository task data

```bash
python3 tools/ai_task_tracker.py export --output ai-task-log.csv
```

The generated CSV contains:

`task_id, committed_at, commit_sha, task, task_type, model, retries, escalated, escalated_from, escalation_reason, outcome`

The CSV is a generated analysis artifact; Git commit trailers are the durable source of truth.

## Metrics to review

After enough observations (target at least 20 tasks, and preferably enough tasks in each major task category), calculate:

- credits per successful logical task
- first-pass success rate
- retry rate
- escalation rate
- credits by task type
- credits by initial model
- total credits for escalated tasks, including the earlier model attempts
- failure/partial-outcome rate

Avoid ranking models from tiny samples. Task difficulty is a major confounder because harder work will intentionally be routed to stronger models.

## Evaluation cautions

This is observational operational data, not a randomized experiment. Model comparisons can be biased by task difficulty, developer familiarity, changing model versions, reasoning settings, and incomplete cost-to-task matching. Record model/version and reasoning level from OpenAI usage data when available. Periodically assign comparable tasks to different models if a stronger causal comparison is needed.

Human review remains necessary to judge whether a change was actually correct and whether later rework reveals a false initial `success` outcome.
