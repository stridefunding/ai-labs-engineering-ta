# Build a dependable order import service with Clasp

Thanks for taking the time to work through this exercise. We’re looking forward to seeing how you approach a practical engineering problem, the choices you make, and how you check your work.

Imagine a teammate has received an order export from a partner. Before adding it to the database, they need to understand what’s in the file, resolve any concerns, and choose what to import. Your task is to build a small HTTP service that helps them do that with confidence—and understand what happened if something goes wrong.

## Before you start

Plan to spend **about four hours**. Start with a useful working flow, then use the remaining time on the risks you think matter most. If you run out of time, tell us what’s incomplete and what you would do next. That context helps us understand your decisions.

Use your preferred language and libraries. **No frontend or deployment is required.** You also don’t need authentication, an AI feature, Docker, an ORM, or any particular framework. We care about correctness, recovery, meaningful tests, clear code, and a handoff another engineer can follow.

AI assistance is welcome within the [model and disclosure guidelines below](#using-ai-tools). Your choice of model or harness doesn’t earn extra credit; we’re interested in your decisions and what you verified.

The [API contract](API_CONTRACT.md) gives you the interface, examples, and input limits. Keep `main` at the starting template and build your solution on `submission`. If anything in the brief is unclear, please reply to your invitation email.

## What’s included

- `data/existing-orders.db`: 12 fictional orders in one SQLite table.
- `data/partner-export-01.csv` and `data/partner-export-02.csv`: 30 rows each, including data-quality problems.
- `API_CONTRACT.md`: the public HTTP interface and examples.
- `smoke.py`: a public contract check: `python3 smoke.py --url http://127.0.0.1:8000 --db /path/to/working.db`. Use a disposable working database. Use it to check the interface as you build, alongside your own tests.

Keep the supplied files unchanged. Run against a working database copy, configured with `ORDERS_DB`; document how to initialize and reset it. You may add tables/columns/indexes, but retain the supplied order columns, their meanings, existing values and generated internal IDs.

## Build the workflow

1. Accept a CSV and return a preview with stable preview-scoped row identifiers, recognized order values, and actionable concerns. Preview must not insert or modify orders.
2. Accept an explicit selection from that preview. Bind it to the content reviewed and recheck the current database before inserting. Support selecting a subset of an otherwise valid batch. Never silently update an existing order or pick a winner among conflicting values.
3. Return accurate outcomes for all rows, including those not selected, duplicated, blocked or already present. A duplicate of a deselected row must not imply that the order was saved.
4. Make retries safe. Handle changed database state, competing requests, temporary write failures and process restarts without duplicating or corrupting orders. A temporary refusal with a useful retry path is acceptable; high concurrency throughput is not required.

You may refuse an entire mixed file if its problems make a safe import decision unavailable. Explain what needs correction, and allow a corrected or subsequent valid upload to work. You may instead support valid rows while refusing others. Do not invent missing values or silently “fix” questionable amounts/dates.

Declare whether a write failure rolls back the selected batch or retains explicitly reported completed rows. Either policy is acceptable when durable state and responses agree, retries are safe, and the caller can reconcile what happened. You do not need a permanent history UI, an event store, or a production idempotency framework.

## Order rules

- `source` plus `external_order_id` identifies an order. Both are case-sensitive, and different sources may reuse the same external ID.
- Every supplied order field is required. Do not treat whitespace-only text as present. For this task trim surrounding whitespace before validation; preserve the remaining identifier/source/email text and letter case exactly. Do not fold distinct identities together.
- `order_amount` is in major units: `12.50` becomes integer `amount_minor = 1250`. Zero is valid. Accept ordinary unsigned decimal notation with up to two decimal places; reject negatives, rounding, exponents, currency symbols and ambiguous separators. The supported maximum is `2^53 - 1` minor units; reject larger values explicitly.
- Currencies are `USD`, `EUR`, `GBP`; statuses are `pending`, `paid`, `shipped`, `cancelled`. No conversions or transitions are required. You may refuse other casing; any supported normalization must be visible before approval.
- `order_date` is a real calendar date in `YYYY-MM-DD` form. No timezones or “must be in the past” rule. All required customer emails must be nonblank; do not invent extra business rules. If you add syntax checks, document them and keep ordinary addresses working.
- Existing orders are insert-only for this exercise. An identical resend can be skipped; changed required values are conflicts. An email-case change counts as a changed value.

Support the ordinary UTF-8 comma-separated exports, including quoted commas/escaped quotes, and the supplied exports and ordinary values described here. You need not support every CSV dialect. Clearly refuse malformed/unsupported input without losing a normal recovery path. The API contract discloses input limits and identifies optional format variations.

## How we’ll review your work

We’ll look at five areas:

- **Correctness and data safety:** does the service save the approved orders with the right values and explain the results accurately?
- **Recovery:** can a caller safely make progress after a failure, retry, or restart?
- **Tests:** do your checks give useful confidence in the behavior and risks that matter?
- **Code clarity:** can another engineer understand the responsibilities and make a focused change?
- **Developer experience and handoff:** can we follow your instructions to run, test, and reset the service, and understand its limitations?

We’ll run real HTTP requests, inspect the working SQLite database, and run and read your tests. Checks include valid files, missing or invalid values, repeated or conflicting identities, subset selection, stale previews, invalid direct requests, concurrent requests, controlled SQLite write failures and locks, a committed operation whose response is lost, restart, and bounded input limits. You won’t need a browser or browser automation tool.

The public smoke check covers the interface and a small working flow; our review also explores the cases above. Extra features and longer documentation don’t earn extra credit. Focus on a solution you can explain and evidence that it works.

## Using AI tools

You’re welcome to use AI for planning, implementation, testing, debugging, review, and documentation. You should be able to explain the decisions in your submission and tell us what you checked yourself.

For closed-source models, please use **only Terra, Luna, Sonnet, or Haiku**. **Any open-source model is permitted.** The same rule applies to delegated agents, automated reviewers, model routing, and fallbacks, so check those settings before you start. A harness can provide access to several models; choose a configuration that identifies an allowed model.

In your handoff, list **every harness/tool and model you used**, including review-only assistance. By “harness,” we mean the environment driving the model—for example, a CLI agent, IDE assistant, chat interface, API script, orchestration framework, or review bot. Please identify the harness and the model separately.

This table is enough to get started:

| Role / work performed | Harness/tool and version, if known | Provider and model name / exact ID or version | Relevant settings, if known |
| --- | --- | --- | --- |

Include model switches, routed or fallback models, delegated reviewers, and reasoning/effort settings when exposed. Mark details the tool doesn’t expose as `unknown` rather than guessing; a folder or harness name doesn’t establish model identity, and an unknown model isn’t automatically permitted. If you accidentally use a model outside the allowed list, please mention it openly.

Also summarize what you independently checked and which checks actually ran. If you didn’t use AI, just say so. We don’t need hidden chain-of-thought, full chat transcripts, or an exhaustive process diary.

## Wrapping up

Leave a short README that helps us pick up where you left off. Please include:

- Prerequisites and exact setup, start, test, and reset commands, including `PORT` and `ORDERS_DB` configuration.
- Accepted formats, assumptions, and whether a write failure rolls back the batch or retains completed rows.
- How a caller safely retries and reconciles the result.
- Tests you actually ran, what you independently checked, and the AI tool/model disclosure above.
- Known limitations and what you’d work on next.

A few candid notes about unfinished work are helpful. You don’t need to spend your remaining time polishing a long write-up.

When you’re ready to submit:

1. Use this template to create a **private** repository under your personal account.
2. Keep `main` at the original template and commit your implementation on `submission`.
3. Add **StrideTechHiring** as a collaborator and open an **unmerged PR** from `submission` to `main`.
4. Reply to your invitation email with **READY FOR REVIEW**, your GitHub username, repository URL, and PR URL.

We review the exact committed PR-head snapshot, so please make sure your implementation files are committed—untracked files won’t be included. Keep that snapshot unchanged until we confirm receipt.

Thanks again for making time for this. We’re looking forward to discussing your approach with you.
