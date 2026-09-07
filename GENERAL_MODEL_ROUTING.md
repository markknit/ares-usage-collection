# General ChatGPT Model Routing Policy

Use this policy for substantial ChatGPT work, regardless of subject. It is intentionally general and does not include ARES-specific Git, task-ID, or M&E controls.

## Objective

Use the lowest-cost OpenAI model that can reasonably complete the task correctly. Escalate only when reasoning difficulty, uncertainty, risk, or failed attempts justify it.

## Default roles

- **Terra** — routine questions, straightforward analysis, simple writing/editing, repository inspection, mechanical implementation, configuration, tests, and execution of a clear plan.
- **Sol** — complex reasoning, non-obvious debugging, cross-component analysis, substantial research, design work, or escalation after Terra struggles.
- **Astra** — exceptionally difficult or persistent problems, high-consequence decisions, difficult-to-reverse architecture, or independent review where maximum capability is justified.

Task size alone is not a reason to escalate. A long but mechanical task can remain Terra; a short but subtle high-risk task may warrant Sol or Astra.

## Interaction rule

Apply routing silently when the current model is suitable. Do not interrupt trivial or low-cost exchanges with model-selection commentary.

If a different model is materially more appropriate, tell the user which model to use and briefly why. If the current ChatGPT surface cannot switch models automatically, make the recommendation rather than pretending a switch occurred.

## Escalation

Escalate Terra to Sol when reasoning difficulty, uncertainty, cross-component interaction, or unsuccessful attempts make Terra less economical. Escalate Sol to Astra when the problem remains unresolved, the decision is especially consequential, or an independent maximum-capability review is warranted.

Do not treat escalation as failure by itself; judge whether the overall task was completed efficiently and correctly.

## Measurement

Do not create task IDs or detailed cost logs for ordinary conversations unless the user explicitly wants measurement. Routing is global; measurement is optional and project-specific.

Never invent token or credit usage. Use OpenAI-provided usage data when precise cost attribution matters.

## Scope

Project-specific instructions may extend this policy with stronger review requirements, tracking, Git controls, task schemas, or evaluation rules. When a project-specific policy conflicts with this general policy, follow the more specific project policy.
