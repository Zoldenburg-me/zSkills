#!/usr/bin/env python3
"""Start the agent-tracker MCP server against a hosted board, never the local SQLite fallback."""
import os
import runpy
import sys

if not os.environ.get("AGENT_DASH_URL", "").strip():
    sys.exit("agent-tracker: no board URL set. Set the plugin's Board URL (ai-harness-board) or AGENT_DASH_URL.")
os.environ["AGENT_DASH_URL"] = os.environ["AGENT_DASH_URL"].strip().rstrip("/")
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
runpy.run_path(os.path.join(here, "mcp_server.py"), run_name="__main__")
