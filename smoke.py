#!/usr/bin/env python3
"""Public V2 smoke test. Standard library only; use a disposable working DB."""
import argparse
from contextlib import closing
import base64
import json
import sqlite3
import urllib.error
import urllib.request
import uuid
from pathlib import Path


class Client:
    def __init__(self, url, timeout=45, record=None):
        self.url = url.rstrip('/')
        self.timeout = timeout
        self.record = record or (lambda exchange: None)

    def request(self, method, path, data=None, content_type=None):
        if isinstance(data, dict):
            data = json.dumps(data, separators=(',', ':')).encode()
            content_type = 'application/json'
        headers = {'Content-Type': content_type} if content_type else {}
        req = urllib.request.Request(self.url + path, data=data, headers=headers, method=method)
        exchange = {'method': method, 'path': path, 'content_type': content_type,
                    'request_base64': base64.b64encode(data or b'').decode()}
        try:
            try:
                response = urllib.request.urlopen(req, timeout=self.timeout)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                raw = response.read()
                exchange.update(status=response.status, response_content_type=response.headers.get('Content-Type', ''),
                                response_base64=base64.b64encode(raw).decode())
            try:
                exchange['body'] = json.loads(raw)
            except (ValueError, UnicodeError):
                exchange['body'] = None
            return exchange
        except (OSError, urllib.error.URLError) as error:
            exchange['transport_error'] = str(error)
            raise
        finally:
            self.record(exchange)

    def preview(self, data):
        return self.request('POST', '/api/previews', data, 'text/csv')

    def approve(self, preview, rows):
        return self.request('POST', '/api/imports', {'preview_id': preview['preview_id'], 'selected_row_ids': rows})


def snapshot(path):
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)) as conn:
        return conn.execute('SELECT id, source, external_order_id, customer_email, amount_minor, currency, order_date, status FROM orders ORDER BY id').fetchall()


def smoke(url, db):
    client = Client(url)
    health = client.request('GET', '/api/health')
    assert health['status'] == 200 and health['body']['status'] == 'ok', health
    assert health['body']['write_policy'] in ('atomic', 'partial'), health
    before = snapshot(db)
    marker = 'SMOKE-' + uuid.uuid4().hex[:12]
    header = b'external_order_id,customer_email,order_amount,currency,order_date,status,source\n'
    data = header + ''.join(f'{marker}-{i},buyer@example.com,0.29,USD,2026-08-24,paid,smoke\n' for i in [1, 2]).encode()
    response = client.preview(data)
    assert response['status'] == 201, response
    p = response['body']
    assert not p['file_errors'] and len(p['rows']) == 2, p
    assert snapshot(db) == before, 'Preview changed orders'
    selected = p['rows'][0]['row_id']
    result = client.approve(p, [selected])
    assert result['status'] == 200, result
    after = snapshot(db)
    assert after[:len(before)] == before, 'Existing records changed'
    assert len(after) == len(before) + 1 and after[-1][1:] == ('smoke', marker+'-1', 'buyer@example.com', 29, 'USD', '2026-08-24', 'paid'), after[-2:]
    assert client.approve(p, [selected])['status'] == 200
    assert snapshot(db) == after, 'Repeat changed orders'
    invalid = client.preview(header + b'BAD,,1.00,USD,2026-08-24,paid,smoke\n')
    assert invalid['status'] == 201
    bad = invalid['body']
    assert bad['file_errors'] or bad['rows'] and all(r['status'] == 'blocked' and r['issues'] for r in bad['rows']), bad
    assert snapshot(db) == after
    print('PASS: health, preview/no-write, exact subset persistence, repeat, invalid-input diagnosis')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--db', type=Path, required=True)
    args = parser.parse_args()
    smoke(args.url, args.db)
