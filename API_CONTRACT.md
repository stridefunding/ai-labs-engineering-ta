# Order import HTTP contract — V2

This specifies the observable interface, not internal classes, libraries, preview storage, or a reference importer. The [candidate brief](README.md) supplies business rules. The included smoke client exercises the public examples; private fixtures and scoring artifacts are not candidate-facing.

## Runtime and transport

Listen locally on `PORT` (default 8000). Use `ORDERS_DB` for the working SQLite file. Document initialization/reset; never write to the supplied seed. The assessor may start another instance on a different port and disposable DB. No credentials, remote service or browser is required.

All responses are UTF-8 JSON. Support these endpoints:

| Request | Purpose | Normal response |
| --- | --- | --- |
| `GET /api/health` | Readiness and declared write policy | 200 |
| `POST /api/previews` with `Content-Type: text/csv` | Preview the exact raw UTF-8 CSV request body | 201, including actionable file/row refusal information |
| `POST /api/imports` with `Content-Type: application/json` | Approve identifiers from a specific preview | 200 with complete outcomes |

Raw CSV avoids multipart and filename/path handling. Limit CSV requests to **1,048,576 bytes**, including any BOM/newlines, and **1,000 data records**. Limit the import JSON body to **65,536 encoded bytes**, not decoded string length. The assessor's import requests obey that cap; choose compact row identifiers so a 1,000-row selection fits. Return 413 for byte-limit violations and an actionable file error for too many CSV records. A normal request after refusal must work. These are bounded tests, not load testing or a requirement to build a proxy-level resource-control system.

Parse ordinary UTF-8 CSV with the seven named headers, quoted fields, escaped double quotes and LF/CRLF. An optional UTF-8 BOM is accepted. Duplicate required headers and missing columns must be refused, not guessed. Reordered/extra columns and embedded newlines may be supported correctly or explicitly refused. Distinct text identifiers, including ordinary punctuation, leading zeros, and letter case, remain distinct; do not reinterpret them as numbers or markup. Ignore wholly empty lines consistently and explain how row locations are reported.

`GET /api/health` returns:

```json
{"status":"ok","write_policy":"atomic"}
```

`write_policy` is `atomic` or `partial`, matching the documented behavior after an unexpected write failure. This declares a policy; the evaluator still tests it.

## Preview response

The following is illustrative data, not a fixture to hardcode:

```json
{
  "preview_id": "p-example",
  "content_sha256": "<64 lowercase hexadecimal characters for the exact request bytes>",
  "file_errors": [],
  "rows": [
    {
      "row_id": "p-example:r1",
      "line": 2,
      "status": "eligible",
      "raw": {
        "external_order_id": "NEW-1",
        "customer_email": "buyer@example.com",
        "order_amount": "12.50",
        "currency": "USD",
        "order_date": "2026-08-24",
        "status": "paid",
        "source": "partner"
      },
      "order": {
        "external_order_id": "NEW-1",
        "customer_email": "buyer@example.com",
        "amount_minor": 1250,
        "currency": "USD",
        "order_date": "2026-08-24",
        "status": "paid",
        "source": "partner"
      },
      "issues": [],
      "duplicate_of": null
    }
  ]
}
```

- `preview_id` is a nonempty opaque string identifying an immutable reviewed input. Separate uploads never replace the content behind an earlier ID. The SHA is calculated from original body bytes; do not normalize newlines before hashing.
- `row_id` is a nonempty opaque string scoped to that preview, not a shared positional index. A row ID from another preview must be rejected. An index prefixed with preview ID is sufficient; there is no cryptography requirement for identifiers.
- `line` is the one-based physical starting line of the CSV record, including the header. If multiline records are supported, later locations must remain accurate. File-level parse failures can use `line: null` in their diagnostic.
- `status` is `eligible`, `blocked`, `duplicate`, or `already_present`. Eligible rows may carry warnings; approval is always explicit, so separate UI selection defaults are unnecessary.
- `raw` contains the seven CSV fields as received. `order` contains the normalized seven order fields shown above, or `null` when the record cannot form a valid order. Never invent values to fill missing fields. Show any supported normalization before approval.
- `issues` contains objects with `severity` (`error` or `warning`), stable machine-readable `code`, human-readable `message`, and `field` (column name or null). The exact explanatory sentence is not asserted by the evaluator. Diagnostics must distinguish the actual problem and offer enough context to correct it.
- `duplicate_of` is the representative row's ID for identical in-file duplicates, otherwise null. Different values for the same new identity are blocked as conflicts; do not choose a winner silently. Only an eligible representative can be approved as a new order.
- `file_errors` uses objects with `code`, `message`, and `line` (integer or null). Unsupported structure, invalid encoding, empty content, or deliberate whole-file refusal goes here. The caller must correct/re-upload; imports against this preview return 422 without writes. A header-only file may return an empty row list with a `no_orders` file error.

Previewing may store metadata; it must not mutate orders. Invalid currency or another bad value must produce a usable JSON diagnostic, including raw field context. A mixed file may return blocked rows alongside eligible rows, or be refused at file level with useful reasons. The valid positive-control inputs must not be refused indiscriminately.

Unfinished previews may expire on restart. Return an explicit missing-preview error and let the caller upload again. Permanent preview retention and a cleanup subsystem are not required for this local exercise.

## Approval request

```json
{
  "preview_id": "p-example",
  "selected_row_ids": ["p-example:r1"]
}
```

Accept only nonempty string identifiers, with a nonempty list and no duplicate IDs. An empty list returns 400 without writes; the caller can simply choose not to submit. Reject unknown IDs, IDs belonging to another preview, blocked selections, and in-file duplicate rows as invalid selections. Do not accept caller-supplied replacement order data or CSV content in this request. Unexpected request fields are rejected with 400 rather than silently used or ignored.

Recheck selected records against the current DB at import time. Exact identities already stored with the same values may be reported as already present. If a selected identity now conflicts, refuse the approval with 409 and no new orders from that request; the caller must review fresh state. This pre-write conflict check is distinct from the declared atomic/partial policy for an unexpected failure during otherwise valid writes.

Import only approved identities. Unselected eligible rows stay unsaved. Invalid/duplicate rows that were not selected do not authorize extra writes. Do not update/delete existing orders or change the meaning of an immutable preview.

## Successful result and repeat semantics

```json
{
  "preview_id": "p-example",
  "replayed": false,
  "summary": {
    "inserted": 1,
    "already_present": 0,
    "duplicate": 0,
    "not_imported": 0
  },
  "rows": [
    {
      "row_id": "p-example:r1",
      "outcome": "inserted",
      "persisted": true,
      "order_id": 13,
      "code": "inserted",
      "message": "Order saved."
    }
  ]
}
```

Return one result row for every nonblank record in the preview, including unselected and blocked records. `outcome` is `inserted`, `already_present`, `duplicate`, or `not_imported`. Counts must match those row outcomes; they describe records, not four independent counts of distinct orders. `code` gives the specific reason, such as `not_selected`, `invalid_row`, or `duplicate_of_unselected`. Wording is free, but facts must agree with the DB.

`persisted` states whether that row's exact order values exist at the operation's decision point. `order_id` is the actual generated/stored internal ID when persisted, otherwise null. Invalid or conflicting rows cannot be called persisted because another version shares their identity. A duplicate of an inserted representative may be persisted with the same order ID; a duplicate of an unselected absent representative must be false/null. Previously existing identical rows can be already present even though this request did not insert them. Do not promise every “skipped” row was saved.

Repeat the same approval safely. Two acceptable responses, both observable and testable:

- Recompute against current state and return `replayed: false`, with zero new inserts and accurate already-present/other outcomes.
- Replay the original successful result with `replayed: true`. Its inserted count describes the original operation, not new writes during the retry.

A successful preview may be single-decision or reusable. If a later different selection is unsupported, return 409 `preview_consumed` with instructions to upload again. Do not replay the earlier selection as if it represented the new request. Do not require a database-backed operation-history system solely to implement replay; recomputing is acceptable.

On restart, committed orders and their IDs/values survive. A missing in-memory preview can return 404; re-uploading then approving eligible rows must reconcile safely. Existing identical rows need not become selectable merely to demonstrate a no-op. A safe re-upload showing that everything already exists is useful feedback.

## Errors, write faults, and lost responses

Use this error envelope for request/protocol failures:

```json
{
  "error": {
    "code": "invalid_selection",
    "message": "The selection contains a row from another preview. Review the intended preview and try again."
  }
}
```

| HTTP status | Required meaning |
| --- | --- |
| 400 | Invalid JSON/shape/types/selection or unexpected import fields; no order writes |
| 404 | Unknown/expired preview; no order writes; upload again |
| 409 | Selected values conflict with current DB, or different selection on a consumed preview; no order writes |
| 413 | Encoded request body exceeds its endpoint limit; no order writes |
| 415 | Unsupported content type; no order writes |
| 422 | Preview/file cannot be imported because of its diagnosed problems; no order writes |
| 500 or 503 | Actual write/service failure or temporary DB unavailability; state and recovery information below |

For 500/503, add `saved_state`: `none`, `partial`, or `unknown`, and a useful next step. If completed/retained outcomes can be established, include `result` in the success-result shape with accurate rows/counts. Do not claim `none` unless rollback/no-write is established. `unknown` is appropriate when the process cannot establish what committed; retry/re-upload must safely reconcile it. Internal exception details, credentials and filesystem contents are not useful public errors.

With `atomic`, an induced statement failure after earlier inserts leaves none of that attempt's new orders. With `partial`, completed approved orders may remain, but no unapproved/invalid order may persist and feedback must reconcile retained state. Removing the fault and retrying the same decision must finish safely, without duplicate identities or overwrites. No candidate fault-injection endpoint is required; the assessor uses disposable SQLite copies.

Concurrent requests may wait or return a bounded temporary failure. They must not cause duplicate identities or invalidate future recovery. If a committed response never reaches the caller, a repeated decision or fresh preview must establish the durable outcome safely. The assessment does not require the server to detect what a client displayed or to implement a browser.

## Self-checking without private fixtures

The public `smoke.py` client uses a running URL and disposable working DB to verify preview/no-write, import a known valid subset, repeat it, and submit one invalid input. It prints HTTP and identity-level mismatches clearly. It is public executable documentation, not a reference implementation of parsing/import policy or the complete private evaluation.

Candidates remain responsible for their own risk-focused tests. The private suite varies inputs within the disclosed rules and exercises the public failure/recovery categories. It does not require undocumented locale conversions, hidden business defaults, visual polish, or an implementation-specific architecture.

Keep row identifiers at most 48 UTF-8 bytes and preview identifiers at most 128 bytes so a full supported selection fits the import request limit. JSON boolean values are not integer order IDs.
