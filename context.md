# ARES Usage Collection — ChatGPT Context

Use these instructions whenever this file is supplied in a ChatGPT conversation concerning the ARES Usage Collection project.

## Relationship to general model routing

ARES uses the same general principle as `GENERAL_MODEL_ROUTING.md`: use the lowest-cost model reasonably capable of completing the task, apply routing silently when the current model is suitable, and escalate based on reasoning difficulty, uncertainty, risk, or failed attempts rather than task size.

This file adds **ARES-specific controls and measurement**. It does not redefine the general Terra/Sol/Astra policy unnecessarily.

## When to apply ARES controls

For substantial ARES work involving implementation, debugging, configuration, testing, research, architecture, documentation, or review, apply the ARES controls below. Do not interrupt trivial questions or tiny edits with tracking overhead.

## Mandatory ARES review

Work affecting any of the following requires review by at least Sol even if Terra performs the implementation:

- collection integrity
- school identity
- deduplication
- potential data loss
- reporting semantics

## Cross-surface task continuity

ARES work may move between ordinary ChatGPT, a ChatGPT Project, Work, Codex, and Git. Treat work pursuing the same outcome as one logical task where practical.

When repository access is available, consult `config/ai_model_routing.json`, use `tools/ai_model_router.py` and `tools/ai_task_tracker.py` for implementation work, and preserve the same `AI-Task-ID` across related implementation commits and escalations.

## Outcome and measurement

Use conservative outcomes: success, partial, failed, or abandoned. Do not equate code generation with success. Prefer tests, validation, operational evidence, and human acceptance where appropriate.

For measured ARES work, the primary operational metric is credits per successful logical task. Also consider first-pass success, retries, escalation, task type, recommended vs. actual model, and human verification.

Never invent token or credit usage. OpenAI usage data is authoritative for cost, and task-level attribution is provisional unless it can be reliably matched.

## Git discipline

After every major completed implementation step, validate the work and create a descriptive Git commit before proceeding to the next major step. For AI-assisted repository work, include the AI metadata required by the repository tracking system.

## Source of truth

For repository work, `config/ai_model_routing.json` is the authoritative detailed ARES routing policy. If this portable context conflicts with the repository configuration, follow the repository configuration and flag the mismatch.

## Starting a new ordinary ChatGPT conversation

If this file is attached or pasted into an ordinary conversation, the ARES-specific instructions are active for that conversation. The user does not need to invoke them on every prompt.

If a global/general model-routing instruction is already active, this file simply adds the ARES-specific controls above.

This file does not itself switch the active ChatGPT model or execute repository scripts. When automatic switching is unavailable, ChatGPT should recommend a model change only when it is materially worthwhile or required by the ARES review policy.
