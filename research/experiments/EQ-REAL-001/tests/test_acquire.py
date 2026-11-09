import hashlib
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from acquire import acquire

class Response:
    status = 200
    headers = {"Content-Type": "application/zip", "ETag": '"test"'}
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, size): 
        part, self.data = self.data[:size], self.data[size:]
        return part
    def __init__(self, data): self.data = data

class AcquireTests(unittest.TestCase):
    def test_exact_download_receipt(self):
        raw = b"test official bytes"
        with tempfile.TemporaryDirectory() as directory:
            with patch("urllib.request.urlopen", return_value=Response(raw)):
                r = acquire({"source_id":"X", "url":"https://example.org/dataset.zip"}, pathlib.Path(directory))
            self.assertEqual(r["bytes"], len(raw))
            self.assertEqual(r["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual((pathlib.Path(directory)/"dataset.zip").read_bytes(),raw)

if __name__ == "__main__":
    unittest.main()
