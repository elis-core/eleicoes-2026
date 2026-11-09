#!/usr/bin/env python3
"""Inspect real ZIP headers and streaming CSV row counts; never infer fields from titles."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()

def inspect_zip(path):
    out = {"archive": str(path), "archive_sha256": sha256(path), "members": []}
    with ZipFile(path) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f"corrupt ZIP member: {bad}")
        for member in archive.infolist():
            detail = {"name": member.filename, "uncompressed_bytes": member.file_size,
                      "crc32": format(member.CRC, "08x")}
            if not member.is_dir() and member.filename.lower().endswith(".csv"):
                with archive.open(member) as raw:
                    with io.TextIOWrapper(raw, encoding="latin-1", newline="") as stream:
                        sample = stream.readline()
                        if not sample:
                            detail["rows"] = 0
                            detail["headers"] = []
                        else:
                            # TSE convention is semicolon; record the actual sample to verify.
                            delimiter = ";" if sample.count(";") >= sample.count(",") else ","
                            detail["delimiter"] = delimiter
                            detail["headers"] = next(csv.reader([sample], delimiter=delimiter))
                            detail["rows"] = sum(1 for _ in csv.reader(stream, delimiter=delimiter))
                            detail["header_encoding_assumed"] = "latin-1 (reversible byte decoding)"
            out["members"].append(detail)
    return out

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--directory", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    archives = sorted(Path(a.directory).glob("*.zip"))
    results = [inspect_zip(path) for path in archives]
    Path(a.output).write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Inspected {len(results)} ZIP archive(s); wrote {a.output}")

if __name__ == "__main__":
    main()
