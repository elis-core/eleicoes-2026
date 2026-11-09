#!/usr/bin/env python3
"""Fetch exact official archive bytes and record SHA-256 without inventing source metadata."""
import argparse
import csv
import hashlib
import json
import pathlib
import urllib.request
from datetime import datetime, timezone

def acquire(row, directory, timeout=120):
    url = row["url"]
    name = url.rsplit("/", 1)[-1]
    path = directory / name
    h = hashlib.sha256()
    n = 0
    req = urllib.request.Request(url, headers={"User-Agent": "ELIS-EQ-REAL-001/1.0 (public research)"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        headers = dict(response.headers.items())
        status = response.status
        with path.open("wb") as output:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                output.write(block)
                h.update(block)
                n += len(block)
    return {"source_id": row["source_id"], "url": url, "path": str(path),
            "accessed_utc": datetime.now(timezone.utc).isoformat(), "http_status": status,
            "bytes": n, "sha256": h.hexdigest(),
            "last_modified_header": headers.get("Last-Modified", ""),
            "content_type_header": headers.get("Content-Type", ""),
            "etag_header": headers.get("ETag", "")}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--metadata-output", required=True)
    p.add_argument("--source-id", action="append", help="Limit downloads to these identifiers")
    a = p.parse_args()
    directory = pathlib.Path(a.output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    with open(a.manifest, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    receipts = []
    errors = []
    for row in rows:
        if a.source_id and row["source_id"] not in a.source_id:
            continue
        try:
            item = acquire(row, directory)
            receipts.append(item)
            print(json.dumps(item, sort_keys=True))
        except Exception as exc:
            errors.append({"source_id": row["source_id"], "error": repr(exc)})
            print(json.dumps(errors[-1], sort_keys=True))
    target = pathlib.Path(a.metadata_output)
    target.parent.mkdir(parents=True, exist_ok=True)
    keys = ["source_id", "url", "path", "accessed_utc", "http_status", "bytes",
            "sha256", "last_modified_header", "content_type_header", "etag_header"]
    with target.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(receipts)
    if errors:
        raise SystemExit(f"{len(errors)} download(s) failed; see stdout; no successful file receipts fabricated")

if __name__ == "__main__":
    main()
