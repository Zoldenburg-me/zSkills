#!/usr/bin/env python3
"""Start the agent-tracker MCP server against a hosted board, never the local SQLite fallback.

The token comes from AGENT_DASH_TOKEN, or else from the file named by AGENT_DASH_TOKEN_FILE
(written by `board token <name>`, mode 600), so it never has to sit in an MCP config.
"""
import os
import runpy
import sys


def token_from_file(path):
    path = os.path.expanduser(path)
    try:
        with open(path) as f:
            if os.fstat(f.fileno()).st_mode & 0o077:
                sys.exit(f"agent-tracker: {path} is readable by group or others; run chmod 600 {path}.")
            token = f.read().strip()
    except OSError:
        token = ""
    if not token:
        sys.exit(f"agent-tracker: no token in {path}; run `board token <name>` to write it.")
    return token


if __name__ == "__main__":
    if not os.environ.get("AGENT_DASH_URL", "").strip():
        sys.exit("agent-tracker: no board URL set. Set the plugin's Board URL (ai-harness-board) or AGENT_DASH_URL.")
    os.environ["AGENT_DASH_URL"] = os.environ["AGENT_DASH_URL"].strip().rstrip("/")
    if not os.environ.get("AGENT_DASH_TOKEN", "").strip() and os.environ.get("AGENT_DASH_TOKEN_FILE", "").strip():
        os.environ["AGENT_DASH_TOKEN"] = token_from_file(os.environ["AGENT_DASH_TOKEN_FILE"].strip())
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    runpy.run_path(os.path.join(here, "mcp_server.py"), run_name="__main__")
