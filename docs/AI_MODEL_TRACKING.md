# AI model routing and effectiveness tracking

## What you need to do

For ordinary ARES work, your interaction should be minimal.

1. **At the start of a substantial AI-assisted task**, describe the task normally. If you are working interactively in Codex and model selection is not automated by the client, run the router (or ask the AI agent to run it) before implementation.
2. **Use the recommended model** unless there is a clear reason not to. If the actual model differs, record the reason at commit time.
3. **Do not manually escalate just because a task is large.** Escalate when the work hits the configured reasoning/risk/failure thresholds.
4. **At each completed major implementation step**, validate the work and create the tracked commit. Reuse the same task ID if the same logical task continues or escalates.
5. You do **not** need to maintain a separate spreadsheet or task log. Git commit metadata is the repository source of truth.

The router recommends a model; it cannot force the ChatGPT/Codex client to switch models if that client does not expose programmatic model switching. In that situation, you or the agent must select the recommended model in the client.

## Quick start

For a straightforward implementation:

```bash
python3 tools/ai_model_router.py --type implementation --files 3
```

Example output:

```text
MODEL=terra
REASON=implementation defaults to terra
POLICY_VERSION=1
```

For cross-component debugging after one failed attempt:

```bash
python3 tools/ai_model_router.py \
  --type debugging \
  --files 6 \
  --components 3 \
  --previous-failures 1 \
  --cross-boundary
```

For a high-risk architectural change:

```bash
python3 tools/ai_model_router.py \
  --type architecture \
  --architecture-impact high \
  --risk high \
  --irreversible-design
```

Use `--json` when another script/agent needs machine-readable output.

## Routing policy

Rules live in `config/ai_model_routing.json`. They are deterministic and versioned so later analysis can tell which policy produced a recommendation.

Default intent:

- **Terra:** routine inspection, straightforward implementation, configuration, tests, documentation, and execution of a clear plan.
- **Sol:** research, non-obvious debugging, architecture/review, cross-component reasoning, medium architecture impact, or escalation after a failed attempt.
- **Astra:** high architecture impact, high-risk changes, difficult-to-reverse design, or repeated Sol failure.

Task size alone is not an escalation criterion. A large mechanical change may remain on Terra.

## M&E-critical review rule

Changes involving any of these areas require at least **Sol review**, even if Terra performs the implementation:

- collection integrity
- school identity
- deduplication
- data loss
- reporting semantics

Pass the matching `--area` value to the router, for example:

```bash
python3 tools/ai_model_router.py \
  --type implementation \
  --area collection-integrity
```

The output may recommend Terra for implementation while also returning `REVIEW_MODEL=sol`. This is intentional: implementation cost and independent review rigor are separate decisions.

## Escalation

Keep the same `AI-Task-ID` across escalation.

Typical path:

```text
Terra -> Sol -> Astra
```

- Move Terra to Sol when the configured Sol trigger is reached, especially a failed attempt or newly discovered cross-component reasoning.
- Move Sol to Astra when the task becomes high risk/high architecture impact, is difficult to reverse, or reaches the configured repeated-Sol-failure threshold.
- Do not reset retry history when escalating.

## Creating the tracked commit

After staging and validating the intended files:

```bash
python3 tools/ai_task_tracker.py commit \
  --model terra \
  --recommended-model terra \
  --routing-policy-version 1 \
  --type implementation \
  --retries 0 \
  --message "Implement school sync validation"
```

If you deliberately override the router:

```bash
python3 tools/ai_task_tracker.py commit \
  --model sol \
  --recommended-model terra \
  --routing-policy-version 1 \
  --override-reason "Unexpected concurrency interaction discovered during implementation" \
  --type debugging \
  --retries 1 \
  --message "Resolve collection concurrency issue"
```

For an escalated task, preserve the task ID and record the prior model:

```bash
python3 tools/ai_task_tracker.py commit \
  --task-id ares-20260907-120000-abcdef \
  --model sol \
  --recommended-model sol \
  --routing-policy-version 1 \
  --type debugging \
  --retries 2 \
  --escalated-from terra \
  --reason "Cross-component failure remained unresolved" \
  --message "Resolve sync validation failure"
```

The tracker commits staged files only by default. `--all` exists but should be used deliberately.

## What is recorded

Every tracked commit can record:

- `AI-Task-ID`
- `AI-Model` (actual model)
- `AI-Recommended-Model`
- `AI-Routing-Policy-Version`
- `AI-Model-Override-Reason` when applicable
- `AI-Task-Type`
- `AI-Retries`
- `AI-Escalated`
- `AI-Outcome`
- `AI-Escalated-From` when applicable
- `AI-Escalation-Reason` when applicable

## Exporting task data

```bash
python3 tools/ai_task_tracker.py export --output ai-task-log.csv
```

The generated CSV is an analysis artifact. Git trailers remain the durable source of truth.

## OpenAI credit integration

Repository metadata and OpenAI usage data remain deliberately separate until the actual Business/Codex export schema is verified. OpenAI usage data should be the authoritative source for tokens/credits. Do not estimate a per-task credit join merely from timestamps if a reliable identifier is unavailable.

When an actual usage export is available, add a reconciliation step that preserves unmatched/ambiguous records instead of silently assigning them.

## Metrics

Primary metric: **credits per successful logical task**.

Also review:

- first-pass success rate
- retry and escalation rates
- credits by task type
- credits by initial and final model
- recommended-model vs actual-model agreement
- override rate and override reasons
- total credits across an escalation chain
- later rework of commits originally marked successful
- sensitive-area review compliance

## How to improve the router

Do not tune rules after only a few observations. After at least 20 tasks, and preferably enough observations within each task category, review patterns such as repeated Terra-to-Sol escalation. Change `config/ai_model_routing.json` only when the data supports a change, and increment its `version` whenever routing behavior changes.

## Evaluation limitations

This is observational operational data, not a randomized model comparison. Harder tasks are intentionally routed to stronger models, so raw average cost by model is confounded by task difficulty. Model versions, reasoning settings, developer familiarity, and incomplete credit-to-task matching can also distort results.

Human review remains necessary to determine whether a technical `success` was substantively correct, whether an M&E-sensitive change preserves data meaning, and whether later rework invalidates an earlier success classification.
