# If you have time: three optional stretches

Finish the [core workflow](README.md#build-these-three-things) first. Choose any of these within the same four-hour budget, or leave them as next steps. Skipping a stretch does not reduce your core assessment. In your handoff, say which you attempted and what you verified.

## 1. Keep competing requests safe

Try two callers reviewing overlapping orders before either imports. Then approve both, first sequentially and then concurrently. Can you preserve one record per identity and give each caller an accurate result?

For a stale selection with changed values, return 409 without new writes. Concurrent approvals may wait or return a temporary refusal with a retry path. Also try interleaved previews and selections containing row IDs from the other preview.

Show the requests and final database state in a test. High throughput is not the goal.

## 2. Recover from an interrupted import

Try a locked SQLite database or an insert failure partway through a batch. After removing the fault, retry and reconcile the result. Follow your declared atomic/partial policy.

For a write failure, return 500/503 with `saved_state` (`none`, `partial`, or `unknown`) alongside `error`, plus a useful next step in the message. Include a `result` in the normal success shape when retained outcomes are known.

For an extra challenge, lose the response after a successful commit, then restart and retry or upload again. Committed orders and IDs should survive. Previews may expire: a 404 followed by a fresh upload is fine. You don’t need permanent preview storage or a fault-injection API.

## 3. Handle input boundaries gracefully

Try BOM/CRLF files, reordered or extra columns, embedded newlines, Unicode identifiers, duplicate headers, ragged rows, and invalid encoding. Support each variation accurately or explain its refusal, then demonstrate a normal upload still works.

Add limits: 1,048,576 bytes and 1,000 records per CSV; 65,536 bytes per import request. Use HTTP 413 for oversized bodies and a file error for too many records. Choose compact identifiers so a full selection fits. Test immediately below, at, and above each limit, including multibyte text.

Check that SQL-like text stays literal, malformed requests reveal no internal files, and invalid values don’t crash the service. These are bounded checks, not a load-testing project.
