#!/usr/bin/env python3
"""Self-check for bin/board's URL rule: python3 -I test_board.py (exits non-zero on failure)."""
import importlib.machinery, importlib.util, os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin", "board")
spec = importlib.util.spec_from_loader("board", importlib.machinery.SourceFileLoader("board", path))
board = importlib.util.module_from_spec(spec)
spec.loader.exec_module(board)

for ok in ("https://board.example.com", "http://localhost:8787", "http://127.0.0.1", "http://[::1]:9000",
           "HTTP://LOCALHOST"):
    assert board.url_ok(ok), ok
for bad in ("http://localhost.evil.com", "http://localhost@evil.com", "http://evil.com", "ftp://localhost",
            "http://localhost:80@evil.com", "localhost"):
    assert not board.url_ok(bad), bad
print("board self-check ok")
