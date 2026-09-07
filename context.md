# ARES Usage Collection — ChatGPT Context

Use these instructions whenever this file is supplied in a ChatGPT conversation concerning the ARES Usage Collection project.

## Purpose

Apply the ARES Terra/Sol/Astra routing and measurement policy automatically. The user should normally be able to describe the task without separately asking for model routing or tracking.

## When to apply routing

For every **substantial** ARES task involving implementation, debugging, configuration, testing, research, architecture, documentation, or review, assess the appropriate model before significant work begins.

Do not interrupt trivial questions, tiny edits, or low-cost exchanges with routing overhead.

## Model policy

Recommend the lowest-cost model reasonably capable of completing the task correctly:

- **Terra:** routine inspection, straightforward implementation, configuration edits, tests, documentation, and execution of an established plan.
- **Sol:** non-obvious debugging, cross-component reasoning, research, substantial design work, or escalation after Terra struggles.
- **Astra:** persistent problems after Sol, high-risk or difficult-to-reverse architecture, or especially consequential independent review.

Task size alone does not justify escalation. A large mechanical task can remain Terra; a small but subtle high-risk task can require Sol or Astra.

## Mandatory review

Work affecting any of the following requires review by at least Sol even if Terra performs the implementation:

- collection integrity
- school identity
- deduplication
- potential data loss
- reporting semantics

## Interaction with the user

Apply routing silently when the current model is suitable. Do not require the user to type a routing command.

If a different model would materially improve expected cost, reliability, or safety, tell the user which model is recommended and briefly why. Do not create unnecessary switching friction for small tasks.

If the current ChatGPT surface cannot switch models automatically, make the recommendation and allow the user to switch it.

## Escalation

Escalate Terra to Sol when reasoning difficulty, cross-component interaction, or unsuccessful attempts make Terra uneconomical. Escalate Sol to Astra for persistent failure, high-risk architecture, or consequential independent review.

Preserve one logical task identity across escalation where practical. Do not count escalation as a new successful task merely because a stronger model completed it.

## Cross-surface continuity

ARES work may move between ordinary ChatGPT, a ChatGPT Project, Work, Codex, and Git. Treat this as one logical task when it is pursuing the same outcome.

When repository access is available, consult the repository's authoritative detailed policy in `config/ai_model_routing.json` and use `tools/ai_model_router.py` and `tools/ai_task_tracker.py` for implementation work. Preserve the same `AI-Task-ID` across related implementation commits and escalations.

## Outcome and measurement

Use conservative outcomes: success, partial, failed, or abandoned. Do not equate code generation with success. Prefer tests, validation, operational evidence, and human acceptance where appropriate.

The primary operational metric is credits per successful logical task. Also consider first-pass success, retries, escalation, task type, recommended vs. actual model, and human verification.

Never invent token or credit usage. OpenAI usage data is authoritative for cost, and task-level attribution should be treated as provisional unless it can be reliably matched.

## Source of truth and drift

For repository work, `config/ai_model_routing.json` is the authoritative detailed routing policy. This context file intentionally contains a concise portable version. If repository access shows that this file conflicts with the current routing configuration, follow the repository configuration and flag the mismatch for correction.

## Starting a new ordinary ChatGPT conversation

If this file has been attached or its contents have been pasted into the conversation, these instructions are active for that conversation. The user does **not** need to invoke them again on each prompt.

A suitable first message is simply:

`Use the attached ARES context for this conversation. I need to <describe task>.`

After that, proceed normally for the rest of the chat.

This file does not itself change the active ChatGPT model or execute repository scripts. It provides the policy ChatGPT should follow and tells ChatGPT when a model change should be recommended.
