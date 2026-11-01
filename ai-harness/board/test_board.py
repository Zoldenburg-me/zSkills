#!/usr/bin/env python3
"""Self-check for bin/board and server/launch.py: python3 -I test_board.py (exits non-zero on failure)."""
import importlib.machinery, importlib.util, json, os, subprocess, sys, tempfile

here = os.path.dirname(os.path.abspath(__file__))


def load(name, path):
    spec = importlib.util.spec_from_loader(name, importlib.machinery.SourceFileLoader(name, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


board = load("board", os.path.join(here, "bin", "board"))
launch = load("launch", os.path.join(here, "server", "launch.py"))

for ok in ("https://board.example.com", "http://localhost:8787", "http://127.0.0.1", "http://[::1]:9000",
           "HTTP://LOCALHOST"):
    assert board.url_ok(ok), ok
for bad in ("http://localhost.evil.com", "http://localhost@evil.com", "http://evil.com", "ftp://localhost",
            "http://localhost:80@evil.com", "localhost"):
    assert not board.url_ok(bad), bad

# TOML merge keeps other entries and replaces ours, subtables included.
toml = '''model = "o3"  # keep me

[mcp_servers.other]
command = "npx"

[mcp_servers.agent-tracker-main]
command = "old"

[mcp_servers.agent-tracker-main.env]
X = "1"

[mcp_servers.agent-tracker-mainx]
command = "keep"

[profiles.fast]
model = "o4-mini"
'''
new, found = board.toml_set(toml, "agent-tracker-main", '[mcp_servers.agent-tracker-main]\ncommand = "new"\n')
assert found
for keep in ('model = "o3"  # keep me', "[mcp_servers.other]", '[mcp_servers.agent-tracker-mainx]\ncommand = "keep"',
             '[profiles.fast]\nmodel = "o4-mini"'):
    assert keep in new, keep
assert '"old"' not in new and 'X = "1"' not in new and new.count("[mcp_servers.agent-tracker-main]") == 1
gone, found = board.toml_set(new, "agent-tracker-main", None)
assert found and "agent-tracker-main]" not in gone and "[mcp_servers.other]" in gone
assert board.toml_set(gone, "agent-tracker-main", None) == (gone, False)

# JSON merge keeps other keys and other mcp entries.
cfg = json.dumps({"$schema": "https://opencode.ai/config.json", "model": "x", "mcp": {"other": {"type": "remote"}}})
new, found = board.json_set(cfg, "agent-tracker-main", {"type": "local"})
d = json.loads(new)
assert not found and d["model"] == "x" and d["mcp"]["other"] == {"type": "remote"} and d["mcp"]["agent-tracker-main"]
d = json.loads(board.json_set(new, "agent-tracker-main", None)[0])
assert d["mcp"] == {"other": {"type": "remote"}}
try:
    board.json_set("// comment\n{}", "agent-tracker-main", {})
    raise AssertionError("JSONC should be refused, not overwritten")
except ValueError:
    pass

with tempfile.TemporaryDirectory() as tmp:
    # The token file is refused unless only the owner can read it, and missing or empty is an error.
    tf = os.path.join(tmp, "main.token")
    board.write_private(tf, "secret-test-token\n", keep_mode=False)
    assert os.stat(tf).st_mode & 0o777 == 0o600
    assert launch.token_from_file(tf) == "secret-test-token"
    for mode in (0o640, 0o604, 0o644):
        os.chmod(tf, mode)
        try:
            launch.token_from_file(tf)
            raise AssertionError(f"mode {oct(mode)} accepted")
        except SystemExit as e:
            assert tf in str(e) and "secret" not in str(e)
    os.chmod(tf, 0o600)
    for path in (os.path.join(tmp, "missing.token"), os.path.join(tmp, "empty.token")):
        if "empty" in path:
            board.write_private(path, "  \n")
        try:
            launch.token_from_file(path)
            raise AssertionError(path)
        except SystemExit as e:
            assert path in str(e)

    # `board add --tool codex|opencode` writes only the token file's path, keeps other entries, and list/remove work.
    env = {**os.environ, "AGENT_TRACKER_HOME": os.path.join(tmp, "at"), "CODEX_HOME": os.path.join(tmp, "codex"),
           "XDG_CONFIG_HOME": os.path.join(tmp, "xdg")}
    os.makedirs(env["CODEX_HOME"])
    with open(os.path.join(env["CODEX_HOME"], "config.toml"), "w") as f:
        f.write('[mcp_servers.other]\ncommand = "npx"\n')
    run = lambda *a: subprocess.run([sys.executable, "-I", os.path.join(here, "bin", "board"), *a], env=env,
                                    capture_output=True, text=True, stdin=subprocess.DEVNULL)
    for tool, path in (("codex", os.path.join(env["CODEX_HOME"], "config.toml")),
                       ("opencode", os.path.join(env["XDG_CONFIG_HOME"], "opencode", "opencode.json"))):
        out = run("add", "main", "https://board.example.com", "--tool", tool, "--token-file", tf)
        assert out.returncode == 0, out.stderr
        text = open(path).read()
        assert "secret-test-token" not in text and "secret-test-token" not in out.stdout + out.stderr
        assert tf in text and "AGENT_DASH_TOKEN_FILE" in text and "https://board.example.com" in text
        assert "names-main.json" in text and "launch.py" in text
        assert tool == "codex" or os.stat(path).st_mode & 0o077 == 0  # new files 600; codex keeps its 644
        assert "agent-tracker-main" in run("list", "--tool", tool).stdout
        assert run("remove", "main", "--tool", tool).returncode == 0
        assert run("remove", "main", "--tool", tool).returncode != 0
        assert "agent-tracker-main" not in open(path).read()
    assert "[mcp_servers.other]" in open(os.path.join(env["CODEX_HOME"], "config.toml")).read()
    assert run("add", "main", "http://evil.com", "--tool", "codex").returncode != 0
# Comments above the next table survive removing ours; a dotted or inline leftover entry is refused.
kept = '[mcp_servers.agent-tracker-main]\ncommand = "x"\n\n# about other\n[mcp_servers.other]\n'
assert "# about other\n[mcp_servers.other]" in board.toml_set(kept, "agent-tracker-main", None)[0]
for leftover in ('[mcp_servers]\nagent-tracker-main = { command = "x" }\n',
                 'mcp_servers.agent-tracker-main.command = "x"\n'):
    try:
        board.toml_set(leftover, "agent-tracker-main", '[mcp_servers.agent-tracker-main]\n')
        raise AssertionError(leftover)
    except ValueError:
        pass
# OpenCode files already using "mcp": {"servers": {...}} get the entry there.
d = json.loads(board.json_set('{"mcp": {"servers": {"o": {}}}}', "agent-tracker-main", {"type": "local"})[0])
assert d["mcp"]["servers"]["agent-tracker-main"] and "agent-tracker-main" not in d["mcp"]

with tempfile.TemporaryDirectory() as tmp:
    # Without tomllib the old config.toml is backed up and the skipped validation is said.
    board.CODEX, real_tomllib = os.path.join(tmp, "config.toml"), board.tomllib
    with open(board.CODEX, "w") as f:
        f.write('[mcp_servers.other]\ncommand = "npx"\n')
    board.tomllib = None
    board.edit("codex", "agent-tracker-main", {"AGENT_DASH_URL": "https://board.example.com"})
    board.tomllib = real_tomllib
    assert open(board.CODEX + ".board-bak").read() == '[mcp_servers.other]\ncommand = "npx"\n'
    assert "[mcp_servers.agent-tracker-main]" in open(board.CODEX).read()

    # `board token` checks the token before writing it: a rejected token leaves the old file alone.
    board.CONF, tf = tmp, os.path.join(tmp, "main.token")
    board.write_private(board.board_file("main"), json.dumps({"url": "https://board.example.com", "token_file": tf}))
    board.write_private(tf, "old-token\n", keep_mode=False)
    board.prompt_token = lambda url: "new-token"
    board.whoami = lambda url, token: 401
    try:
        board.token("main")
        raise AssertionError("rejected token accepted")
    except SystemExit as e:
        assert "unchanged" in str(e) and "new-token" not in str(e)
    assert open(tf).read() == "old-token\n"
    board.whoami = lambda url, token: 200
    board.token("main")
    assert open(tf).read() == "new-token\n" and os.stat(tf).st_mode & 0o777 == 0o600

    # Both prompts refuse to run without a terminal, since getpass would echo stdin.
    env = {**os.environ, "AGENT_TRACKER_HOME": tmp}
    for args in (["token", "main"], ["add", "x", "https://board.example.com"]):
        out = subprocess.run([sys.executable, "-I", os.path.join(here, "bin", "board"), *args], env=env,
                             input="piped-token\n", capture_output=True, text=True)
        assert out.returncode != 0 and "yourself in a terminal" in out.stderr, out
        assert "piped-token" not in out.stdout + out.stderr
print("board self-check ok")
