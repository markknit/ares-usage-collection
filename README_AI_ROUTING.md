# ARES AI Routing and Measurement Overview

This repository includes a lightweight system for choosing among OpenAI Terra, Sol, and Astra for ARES Usage Collection work and for measuring whether those choices are effective over time.

## Purpose

The goal is to use the lowest-cost model that can complete a task correctly, while escalating when reasoning difficulty, risk, or repeated failure makes a stronger model more economical.

## Default model roles

- **Terra** — routine inspection, straightforward implementation, configuration edits, tests, documentation, and execution of a clear plan.
- **Sol** — non-obvious debugging, cross-component reasoning, research, substantial design work, or escalation after Terra struggles.
- **Astra** — persistent problems after Sol, high-risk or difficult-to-reverse architecture decisions, or especially consequential review.

Task size alone is not a reason to escalate.

## Mandatory stronger review

Changes involving collection integrity, school identity, deduplication, potential data loss, or reporting semantics require review by at least Sol even if Terra performs the implementation.

## How the pieces fit together

- `config/ai_model_routing.json` — authoritative machine-readable routing policy for repository work.
- `tools/ai_model_router.py` — applies the repository routing policy.
- `tools/ai_task_tracker.py` — records recommended model, actual model, retries, escalation, outcome, and task identity in Git commit metadata.
- `config/ai_project_task_schema.json` — shared schema for logical tasks that may move between Chat, Work, Codex, and Git.
- `docs/CHATGPT_PROJECT_INSTRUCTIONS.md` — instructions to paste into the ChatGPT ARES Project so the same policy applies to normal Project conversations.
- `context.md` — portable instructions for ARES work in ordinary ChatGPT conversations outside the Project.

## What the user normally does

Inside the ARES ChatGPT Project, just describe the task. The Project instructions should apply the routing policy without requiring special commands. ChatGPT should only ask you to switch models when the expected benefit is material or when stronger review is required.

Outside the ARES Project, attach or paste `context.md` at the beginning of an ARES-related chat. Once it is present in that conversation, you can continue normally; you do not need to invoke it again for every message.

For repository implementation, the agent should use the router and tracker as part of the workflow rather than asking the user to remember their commands.

## What is measured

The main effectiveness metric is **credits per successful logical task**. Supporting metrics include first-pass success, retry rate, escalation rate, recommended vs. actual model, task type, outcome, and human verification.

OpenAI usage exports remain the authoritative source for credits/tokens. Do not invent task-level credit attribution when a reliable join is not available.

## Important limitation

Routing policy can recommend a stronger or cheaper model, but ordinary ChatGPT conversations cannot necessarily switch the active model automatically. When automatic switching is unavailable, ChatGPT should tell the user when a change is materially worthwhile.

This system is operational measurement, not a controlled experiment. Harder tasks will naturally be routed to stronger models, so model comparisons must account for task difficulty and small sample sizes.
