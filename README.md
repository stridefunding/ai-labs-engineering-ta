# Dependable order imports — V2.0.0

The accompanying [HTTP contract](API_CONTRACT.md) defines the service interface. This repository is the candidate-facing template. Its exercise version is recorded in [VERSION](VERSION); implement your solution on the `submission` branch.

Help an internal teammate import orders from a third-party partner with confidence. Build a small HTTP service that lets a caller inspect a CSV, decide which orders to import, and understand exactly what happened.

Give this **about four hours**. Prioritize a useful working slice and tell us clearly what remains incomplete. We care about correctness, recovery, meaningful tests, clear code, and a usable handoff. A frontend is not required or scored. No authentication, deployment, AI feature, Docker, ORM, or particular framework is required.

Use your preferred language and libraries. AI tools are welcome. You should be able to explain your decisions and show what you checked; tool choice, model name, and claims about development process are not scores.

## Supplied data

- `data/existing-orders.db`: 12 fictional orders in one SQLite table.
- `data/partner-export-01.csv` and `data/partner-export-02.csv`: 30 rows each, including data-quality problems.
- `API_CONTRACT.md`: the public HTTP interface and examples.
- `smoke.py`: a public contract check: `python3 smoke.py --url http://127.0.0.1:8000 --db /path/to/working.db`. Use a disposable working database. It does not substitute for your own tests.

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
- Existing orders are insert-only for this exercise. An identical resend can be skipped; changed required values are conflicts. An email-case change counts as a changed value in V2; this removes V1's undocumented equivalence variation.

Support the ordinary UTF-8 comma-separated exports, including quoted commas/escaped quotes, and the supplied exports and ordinary values described here. You need not support every CSV dialect. Clearly refuse malformed/unsupported input without losing a normal recovery path. The API contract discloses input limits and identifies optional format variations.

## What we will assess

Five attributes: correctness/data safety; failure handling/recovery; test quality; code clarity/changeability; developer experience/handoff. We exercise real HTTP requests and inspect the working SQLite database, including selected identities and original records, not just response counts.

Checks include valid files, missing/invalid values, repeated/conflicting identities, subset selection, stale previews, invalid direct requests, concurrent requests, controlled SQLite write failures/locks, a committed operation whose response is lost, restart, and bounded input limits. We also run and inspect your own tests. A browser or browser automation tool is not needed.

The public smoke check helps you verify the interface and a small useful workflow. It is not the complete evaluation, and passing it alone does not establish reliability. No score is awarded for extra features or documentation volume.

## Handoff and submission

Give us a short README with prerequisites and exact setup/start/test/reset commands; `PORT` and `ORDERS_DB` configuration; accepted formats and assumptions; atomic/partial failure policy; how a caller safely retries; tests actually run; and known limits/next work. If you used AI, briefly describe how and what you independently checked.

Use the provided template to create a **private** repository under your personal account. Keep `main` at the original template; implement on `submission`. Add `StrideTechHiring` as a collaborator and open an unmerged PR from `submission` to `main`. Reply to the assessment email with `READY FOR REVIEW`, your GitHub username, repository URL and PR URL.

We assess the exact committed PR-head snapshot. Ensure implementation files are committed; untracked work is not included. Once submitted, keep that snapshot unchanged until we confirm receipt. A few candid notes about incomplete work are more useful than unsupported claims of completeness.
