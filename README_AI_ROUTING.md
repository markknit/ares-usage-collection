# AI Model Routing and ARES Measurement Overview

This repository now uses a two-layer model-routing system. A general routing policy can apply across all ChatGPT conversations, while the ARES Usage Collection project adds project-specific tracking, Git discipline, measurement, and stronger review requirements.

## Purpose

The routing objective is to use the lowest-cost model reasonably capable of completing a task correctly, while escalating when reasoning difficulty, uncertainty, risk, or repeated failure makes a stronger model more economical.

Detailed effectiveness measurement remains specific to ARES and other projects where it is useful; ordinary conversations do not need task IDs or cost logs.

## General model roles

- **Terra** - routine questions, straightforward analysis, simple writing/editing, repository inspection, mechanical implementation, configuration, tests, documentation, and execution of a clear plan.
- **Sol** - complex reasoning, non-obvious debugging, cross-component analysis, substantial research, design work, or escalation after Terra struggles.
- **Astra** - exceptionally difficult or persistent problems, high-consequence decisions, difficult-to-reverse architecture, or independent review where maximum capability is justified.

Task size alone is not a reason to escalate. A long mechanical task can remain Terra; a short but subtle high-risk task can require Sol or Astra.

## Two policy layers

### 1. Account-wide routing

`GENERAL_MODEL_ROUTING.md` defines the reusable policy for substantial work in any subject. `docs/GLOBAL_CUSTOM_INSTRUCTIONS.md` contains the concise version intended for ChatGPT Custom Instructions.

Once that block is installed in ChatGPT Custom Instructions, new ordinary chats should apply model routing automatically. The user should not need to attach `context.md` merely to obtain model recommendations.

The general policy is intentionally lightweight: route silently when the current model is suitable, recommend a switch only when it is materially worthwhile, and do not create detailed task-effectiveness records unless measurement has been requested.

### 2. ARES-specific controls

The ARES Usage Collection project extends the general policy with:

- project-wide logical task identity;
- recommended-vs-actual model tracking;
- retry and escalation tracking;
- Git metadata and commit discipline;
- outcome and human-verification fields;
- credits-per-successful-task measurement; and
- mandatory stronger review for sensitive ARES data behavior.

Changes involving collection integrity, school identity, deduplication, potential data loss, or reporting semantics require review by at least Sol even if Terra performs the implementation.

## How the files fit together

- `GENERAL_MODEL_ROUTING.md` - general routing policy for substantial ChatGPT work in any subject.
- `docs/GLOBAL_CUSTOM_INSTRUCTIONS.md` - concise account-wide policy to paste into ChatGPT Custom Instructions.
- `docs/CHATGPT_PROJECT_INSTRUCTIONS.md` - ARES Project-specific instructions that extend the general policy.
- `context.md` - portable ARES-specific context/fallback for conversations where the ARES Project instructions are not available.
- `config/ai_model_routing.json` - authoritative machine-readable detailed routing policy for ARES repository work.
- `tools/ai_model_router.py` - deterministically applies the repository routing policy.
- `tools/ai_task_tracker.py` - records recommended model, actual model, retries, escalation, outcome, and task identity in Git commit metadata.
- `config/ai_project_task_schema.json` - shared schema for logical ARES tasks that may move between Chat, Work, Codex, and Git.

## Recommended day-to-day workflow

| Situation | What the user normally does |
| --- | --- |
| New ordinary ChatGPT chat | Ask the question normally. Account-wide Custom Instructions provide general routing. |
| ARES chat inside the ARES Project | Ask the task normally. Project Instructions add ARES controls automatically. |
| ARES chat outside the Project | General routing still applies. Attach/paste `context.md` if the ARES-specific controls are needed. |
| ARES repository/Codex work | Describe the task normally; the agent should use the repository router and tracker as part of implementation. |

Routing should normally be invisible. If the current model is appropriate, there is no reason to interrupt the user. ChatGPT should recommend a different model only when the expected improvement in cost, reliability, quality, or required review is material.

## Installing the account-wide policy

Copy the instruction block from `docs/GLOBAL_CUSTOM_INSTRUCTIONS.md` into ChatGPT Custom Instructions and enable customization.

- Android/iOS: **Settings -> Customize ChatGPT -> Custom Instructions**.
- Web/Desktop: **Settings -> Personalization -> Custom Instructions**.

After this one-time setup, the general routing policy is intended to be available to new chats without attaching a control file each time. Project-specific instructions still extend the general policy when working inside a Project.

## ARES measurement

The main ARES effectiveness metric is **credits per successful logical task**. Supporting metrics include first-pass success, retry rate, escalation rate, recommended vs. actual model, task type, outcome, and human verification.

OpenAI usage data remains authoritative for credits/tokens. Never invent task-level credit attribution when a reliable join is unavailable.

Do not equate generated code with success. Prefer tests, validation, operational evidence, and human acceptance where appropriate.

## Escalation and continuity

Escalate Terra to Sol when reasoning difficulty, uncertainty, cross-component interaction, or unsuccessful attempts make Terra less economical. Escalate Sol to Astra for persistent failure, especially consequential decisions, difficult-to-reverse architecture, or maximum-capability independent review.

For ARES, preserve the same logical task identity across Chat, Work, Codex, Git commits, and model escalations when they are pursuing the same outcome.

## Important limitations

The routing policy can recommend the appropriate model, but an ordinary ChatGPT conversation may not be able to switch the active model automatically. When automatic switching is unavailable, ChatGPT should recommend the change rather than imply that it occurred.

The ARES measurement system is operational measurement, not a controlled experiment. Harder tasks will naturally be routed to stronger models, so model comparisons must account for task difficulty and small sample sizes.

The repository policy is authoritative for detailed ARES repository routing. If a portable context file conflicts with `config/ai_model_routing.json`, use the repository configuration and correct the stale context file.
