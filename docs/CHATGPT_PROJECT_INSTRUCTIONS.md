# ChatGPT Project instructions for ARES Usage Collection

Paste the block below into the ChatGPT Project Instructions for the `ares-usage-collection` project.

---

## ARES AI model routing and task tracking

For every substantial ARES Usage Collection task, apply the project's AI routing policy before doing significant work. The durable routing rules are in `config/ai_model_routing.json`; the shared cross-surface task schema is in `config/ai_project_task_schema.json`.

### 1. Decide whether routing is needed

Do not interrupt trivial questions or tiny edits with routing overhead. For substantial implementation, debugging, architecture, research, configuration, testing, documentation, or review work, classify the task before significant work begins.

### 2. Choose the recommended model

Use the repository routing policy as the source of truth. In summary:

- Terra: routine inspection, straightforward implementation, configuration edits, tests, documentation, and execution of an established plan.
- Sol: non-obvious debugging, cross-component reasoning, substantial design work, research, or escalation after Terra struggles.
- Astra: high-risk or difficult-to-reverse architecture, persistent problems after Sol, or especially consequential independent review.

Task size alone is not a reason to escalate. Favor the lowest-cost model that can reasonably complete the task correctly.

If the current ChatGPT surface cannot switch models automatically, tell the user only when a model change is materially worthwhile. For small tasks, do not create unnecessary model-switching friction.

### 3. Apply mandatory review rules

Changes involving collection integrity, school identity, deduplication, data loss, or reporting semantics require review by at least Sol even if Terra performs the implementation.

### 4. Maintain one logical task across surfaces

When work moves between Chat, Work, Codex, or repository implementation, keep one logical ARES task identity where practical. Do not treat escalation as a new successful task; preserve earlier attempts so total effort and cost can later be measured fairly.

When repository work is involved, follow `tools/ai_model_router.py` and `tools/ai_task_tracker.py`, and preserve the same `AI-Task-ID` across escalations or multiple implementation commits belonging to one logical task.

For non-repository work, use the fields defined in `config/ai_project_task_schema.json` conceptually. Do not invent OpenAI credit values or claim precise task-level cost unless usage data can be reliably attributed.

### 5. Escalate based on evidence

Escalate Terra to Sol when reasoning difficulty, cross-component interaction, or an unsuccessful attempt indicates that Terra is no longer economical. Escalate Sol to Astra for persistent failure, high-risk architecture, or especially consequential review. State the reason for a significant escalation.

### 6. Record outcomes conservatively

Distinguish success, partial completion, failure, and abandonment. Do not call work successful merely because code was produced. Use relevant tests, validation, operational evidence, or human review. If later rework shows that an earlier success assessment was wrong, note that in subsequent evaluation.

### 7. Measurement objective

The primary operational metric is credits per successful logical task, supplemented by first-pass success, retry rate, escalation rate, task type, recommended vs. actual model, and human verification. Model comparisons are observational unless comparable tasks were intentionally assigned across models; do not overinterpret small or confounded samples.

### 8. Git discipline

After every major completed implementation step, validate the work and create a descriptive Git commit before starting the next major step. For AI-assisted repository work, include the AI task metadata required by the repository tracking system.

---

## User interaction expectation

Once these instructions are installed, the user should normally just describe the ARES task. ChatGPT should apply routing silently when the current model is already suitable. It should ask the user to switch models only when the expected benefit is material or when mandatory review requires a stronger model.

For repository tasks, the agent should invoke the router/tracker workflow as part of implementation rather than asking the user to remember commands.
