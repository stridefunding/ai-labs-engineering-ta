# API contract: the core workflow

Use these shapes so we can run your service consistently. The [README](README.md) contains the business rules; advanced scenarios are in the [optional appendix](STRETCHES.md).

## Start the service

Listen on `PORT` (default `8000`) and use the SQLite file at `ORDERS_DB`. Return JSON responses. `GET /api/health` returns HTTP 200:

```json
{"status":"ok","write_policy":"atomic"}
```

Declare `atomic` (roll back a failed batch) or `partial` (retain completed rows), and explain your choice in the handoff.

## 1. Preview

`POST /api/previews` takes the raw CSV body with `Content-Type: text/csv`. Return HTTP 201 with this shape:

```json
{
  "preview_id": "p1",
  "content_sha256": "<SHA-256 of the uploaded bytes>",
  "file_errors": [],
  "rows": [{
    "row_id": "p1:r1",
    "line": 2,
    "status": "eligible",
    "raw": {
      "external_order_id": "NEW-1", "customer_email": "buyer@example.com",
      "order_amount": "12.50", "currency": "USD", "order_date": "2026-08-24",
      "status": "paid", "source": "partner"
    },
    "order": {
      "external_order_id": "NEW-1", "customer_email": "buyer@example.com",
      "amount_minor": 1250, "currency": "USD", "order_date": "2026-08-24",
      "status": "paid", "source": "partner"
    },
    "issues": [],
    "duplicate_of": null
  }]
}
```

Use unique preview IDs and preview-scoped row IDs. Keep the reviewed content fixed. `line` identifies the record’s starting line, counting the header as line 1.

Row status is `eligible`, `blocked`, `duplicate`, or `already_present`. `raw` holds original fields; `order` holds validated values, or null for invalid rows. Identical duplicates point to their representative through `duplicate_of`; conflicting versions of one identity are blocked.

An issue looks like `{"severity":"error","code":"invalid_amount","message":"Use a nonnegative decimal with at most two decimal places.","field":"order_amount"}`. File errors use `code`, `message`, and `line` (or null). A file-level refusal prevents import; explain how to correct it. Preview never changes orders.

## 2. Import a selection

`POST /api/imports` takes `Content-Type: application/json`:

```json
{"preview_id":"p1","selected_row_ids":["p1:r1"]}
```

Accept a nonempty selection of eligible rows from that preview, without repeated IDs. Reject invalid selections and replacement content. Save only those orders. Recheck existing values: skip identical stored orders and refuse conflicting values without overwriting anything.

Return HTTP 200:

```json
{
  "preview_id": "p1",
  "replayed": false,
  "summary": {"inserted":1,"already_present":0,"duplicate":0,"not_imported":0},
  "rows": [{
    "row_id":"p1:r1", "outcome":"inserted", "persisted":true,
    "order_id":13, "code":"inserted", "message":"Order saved."
  }]
}
```

Return an outcome for **every preview row**, including unselected rows. Use the four outcomes shown in `summary`, with matching counts. `persisted` means those exact values exist in SQLite; `order_id` is their internal ID, otherwise null. A duplicate of an unselected, unsaved order is also unsaved.

## 3. Retry or correct

Repeating the same approval must not add more orders. Either recompute accurate outcomes with `replayed:false`, or return the original successful result with `replayed:true`. A corrected upload must work after a rejected file.

Use this shape for request errors:

```json
{"error":{"code":"invalid_selection","message":"Choose eligible rows from this preview."}}
```

Use HTTP 400 for invalid requests/selections, 404 for missing previews, 409 for conflicts, 415 for unsupported content types, and 422 for a refused file. These refusals make no order writes. Explain what the caller can do next. Detailed fault recovery and exact input limits are optional stretches.
