import os
import stat
import subprocess
import time

import pytest

from ia_driver import gitsafe
from ia_driver.events import EventLog
from ia_driver.gitsafe import GitError, run_git

_GIT = gitsafe.resolve_git()
CLEAN_ENV = {"PATH": "/usr/bin:/bin", "HOME": "/nonexistent-test-home", "GIT_CONFIG_NOSYSTEM": "1",
             "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e.x",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e.x",
             "GIT_AUTHOR_DATE": "2020-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2020-01-01T00:00:00Z"}


def g(repo, *args, check=True):
    """Test-side git (setup only; deliberately independent of gitsafe)."""
    r = subprocess.run([_GIT, "-C", str(repo), *args], env=CLEAN_ENV, capture_output=True)
    if check and r.returncode:
        raise AssertionError(r.stderr.decode())
    return r.stdout.decode().strip()


def make_repo(tmp_path, name="repo", files=None, ignore=None):
    root = (tmp_path / name).resolve()
    root.mkdir()
    subprocess.run([_GIT, "init", "-q", str(root)], env=CLEAN_ENV, check=True)
    files = files or {"src/a.py": "A = 1\n", "src/b.py": "B = 2\n", "README": "hello\n"}
    if ignore:
        files = {**files, ".gitignore": ignore}
    for rel, txt in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(txt)
    g(root, "add", "-A")
    g(root, "commit", "-q", "-m", "init")
    return root, g(root, "rev-parse", "HEAD"), g(root, "rev-parse", "HEAD^{tree}")


def fake_git(tmp_path, body, name="fakegit"):
    p = tmp_path / name
    p.write_text("#!/bin/sh\n" + body + "\n")
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return str(p)


def test_happy_path_and_event_logging(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    ev = EventLog()
    out = run_git(root, ["rev-parse", "--verify", "HEAD"], ev)
    assert out.decode().strip() == commit
    snap = ev.snapshot()
    assert [e["kind"] for e in snap] == ["git_read"]
    assert snap[0]["root"] == str(root) and snap[0]["argv"][0] == _GIT
    assert "safe.directory" not in " ".join(snap[0]["argv"])  # ownership checks never weakened
    assert "core.fsmonitor=false" in snap[0]["argv"] and "--no-optional-locks" in snap[0]["argv"]


@pytest.mark.parametrize("args", [
    ["log"], ["config", "--list"], ["fetch"], ["checkout", "HEAD"], ["diff"], ["show", "HEAD"],
    ["rev-list", "--count", "HEAD"], ["-c", "core.fsmonitor=x", "status"], ["--git-dir=/x", "status"],
    ["--exec-path=/x", "rev-parse"], [], [""], ["status;id"], ["rev-parse "],
])
def test_non_allowlisted_subcommand_refused_before_any_process(tmp_path, args):
    root, *_ = make_repo(tmp_path)
    ev = EventLog()
    with pytest.raises(GitError):
        run_git(root, args, ev)
    assert len(ev) == 0  # nothing was executed or logged as executed


@pytest.mark.parametrize("args", [
    ["rev-parse", "--git-dir"], ["rev-parse", "--exec-path=/tmp"], ["status", "--output=/tmp/x"],
    ["ls-files", "--work-tree=/tmp"], ["ls-files", "-c", "x"], ["ls-files", "-cfoo"],
    ["cat-file", "--textconv", "HEAD:README"], ["cat-file", "--filters", "HEAD:README"],
    ["status", "--porc"], ["status", "--ignored=matching"], ["rev-parse", "-HEAD"],
    ["rev-parse", "--config-env=a=b"], ["ls-tree", "--upload-pack=x", "HEAD"],
    ["status", "--GIT-DIR=/x"], ["rev-parse", "HEAD\0x"],
])
def test_dangerous_or_unlisted_options_refused(tmp_path, args):
    root, *_ = make_repo(tmp_path)
    ev = EventLog()
    with pytest.raises(GitError):
        run_git(root, args, ev)
    assert len(ev) == 0


def test_dash_dash_makes_dashed_paths_positional_but_dangerous_prefix_before_it_still_refused(tmp_path):
    root, *_ = make_repo(tmp_path)
    ev = EventLog()
    run_git(root, ["ls-files", "-z", "--", "-weird-name"], ev)  # a path after -- is data
    with pytest.raises(GitError):
        run_git(root, ["ls-files", "--git-dir=x", "--", "a"], ev)


def test_root_must_have_real_git_directory(tmp_path):
    root, *_ = make_repo(tmp_path)
    plain = tmp_path / "plain"
    plain.mkdir()
    ev = EventLog()
    with pytest.raises(GitError):  # must NOT discover a parent repo
        run_git(plain, ["rev-parse", "--verify", "HEAD"], ev)
    with pytest.raises(GitError):
        run_git("relative/path", ["status"], ev)
    assert len(ev) == 0


def test_hostile_config_refused_and_nothing_executed(tmp_path):
    root, *_ = make_repo(tmp_path)
    marker = tmp_path / "pwned"
    hook = tmp_path / "hook.sh"
    hook.write_text(f"#!/bin/sh\ntouch {marker}\n")
    hook.chmod(0o755)
    with open(root / ".git" / "config", "a") as fh:
        fh.write(f"[core]\n\tfsmonitor = {hook}\n")
    ev = EventLog()
    with pytest.raises(GitError, match="unsafe .git/config"):
        run_git(root, ["status", "--porcelain"], ev)
    assert not marker.exists() and len(ev) == 0


def test_dash_c_override_neutralises_fsmonitor_even_if_scan_were_bypassed(tmp_path, monkeypatch):
    root, *_ = make_repo(tmp_path)
    marker = tmp_path / "ran"
    hook = tmp_path / "hook.sh"
    hook.write_text(f"#!/bin/sh\ntouch {marker}\nprintf '\\0'\n")
    hook.chmod(0o755)
    g(root, "config", "core.fsmonitor", str(hook))
    # premise: a plain git status really would run the hook
    subprocess.run([_GIT, "-C", str(root), "status"], env=CLEAN_ENV, capture_output=True)
    assert marker.exists(), "premise failed: git did not run the fsmonitor hook"
    marker.unlink()
    monkeypatch.setattr(gitsafe, "scan_git_config", lambda r: [])
    run_git(root, ["status", "--porcelain"], EventLog())
    assert not marker.exists()


@pytest.mark.parametrize("snippet", [
    "[core]\n\tfsmonitor = true\n", "[core]\n\thooksPath = /tmp/h\n", "[core]\n\tworktree = /tmp\n",
    "[core]\n\tgitProxy = x\n", "[core]\n\tsshCommand = x\n", "[core]\n\tpager = x\n",
    "[alias]\n\tst = !id\n", "[filter \"f\"]\n\tclean = id\n", "[diff \"d\"]\n\ttextconv = id\n",
    "[merge \"m\"]\n\tdriver = id\n", "[extensions]\n\tworktreeConfig = true\n",
    "[include]\n\tpath = /tmp/x\n", "[includeIf \"gitdir:/\"]\n\tpath = /tmp/x\n",
    "[core] fsmonitor = x\n", "[CORE]\n\tFSMonitor = x\n", "[core]\n\tfilemode = false\n",
    "[core]\n\tsomethingnew = 1\n", "[url \"x\"]\n\tinsteadOf = y\n", "[credential]\n\thelper = x\n",
])
def test_scan_git_config_flags_hostile_keys(tmp_path, snippet):
    root, *_ = make_repo(tmp_path)
    assert gitsafe.scan_git_config(str(root)) == []  # baseline git init config is accepted
    with open(root / ".git" / "config", "a") as fh:
        fh.write(snippet)
    assert gitsafe.scan_git_config(str(root)), snippet


def test_scan_flags_worktree_config_and_commondir(tmp_path):
    root, *_ = make_repo(tmp_path)
    (root / ".git" / "commondir").write_text("../other\n")
    assert any("commondir" in p for p in gitsafe.scan_git_config(str(root)))


def test_parent_environment_is_not_used(tmp_path, monkeypatch):
    root, commit, _ = make_repo(tmp_path, "a")
    other, other_commit, _ = make_repo(tmp_path, "b", files={"x": "different\n"})
    assert commit != other_commit
    evil_cfg = tmp_path / "evil.cfg"
    evil_cfg.write_text("[core]\n\tfsmonitor = /bin/false\n[alias]\n\tstatus = !false\n")
    for k, v in {"GIT_DIR": str(other / ".git"), "GIT_WORK_TREE": str(other),
                 "GIT_INDEX_FILE": str(tmp_path / "nonexistent-index"),
                 "GIT_OBJECT_DIRECTORY": str(other / ".git" / "objects"),
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(other / ".git" / "objects"),
                 "GIT_CONFIG_GLOBAL": str(evil_cfg), "GIT_CONFIG_SYSTEM": str(evil_cfg),
                 "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.hooksPath",
                 "GIT_CONFIG_VALUE_0": "/tmp", "GIT_EXTERNAL_DIFF": "/bin/false",
                 "GIT_NAMESPACE": "zzz", "HOME": str(tmp_path)}.items():
        monkeypatch.setenv(k, v)
    ev = EventLog()
    assert run_git(root, ["rev-parse", "--verify", "HEAD"], ev).decode().strip() == commit
    assert run_git(root, ["status", "--porcelain"], ev) == b""
    # and the child's actual environment, observed through a fake git
    fake = fake_git(tmp_path, "env")
    dump = run_git(root, ["status"], ev, git_bin=fake).decode().splitlines()
    names = {l.split("=", 1)[0] for l in dump}
    for forbidden in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                      "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_COUNT",
                      "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0", "GIT_EXTERNAL_DIFF", "GIT_NAMESPACE"):
        assert forbidden not in names
    env = dict(l.split("=", 1) for l in dump if "=" in l)
    assert env["GIT_CONFIG_GLOBAL"] == "/dev/null" and env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert env["HOME"] == gitsafe.NONEXISTENT_HOME and not os.path.exists(env["HOME"])
    assert env["GIT_TERMINAL_PROMPT"] == "0" and env["GIT_OPTIONAL_LOCKS"] == "0"
    assert env["GIT_CEILING_DIRECTORIES"] == str(tmp_path)
    assert set(names) <= {"PATH", "HOME", "XDG_CONFIG_HOME", "LC_ALL", "LANG", "GIT_CONFIG_NOSYSTEM",
                          "GIT_CONFIG_GLOBAL", "GIT_ATTR_NOSYSTEM", "GIT_TERMINAL_PROMPT",
                          "GIT_OPTIONAL_LOCKS", "GIT_NO_REPLACE_OBJECTS", "GIT_ASKPASS", "GIT_PAGER",
                          "GIT_CEILING_DIRECTORIES", "PWD", "SHLVL", "_", "OLDPWD"}


def test_output_cap_enforced_real_git(tmp_path):
    root, *_ = make_repo(tmp_path, files={"big": "x" * 10000 + "\n"})
    assert len(run_git(root, ["cat-file", "-p", "HEAD:big"], EventLog(), max_bytes=20000)) > 10000
    with pytest.raises(GitError, match="exceeded"):
        run_git(root, ["cat-file", "-p", "HEAD:big"], EventLog(), max_bytes=100)


def test_output_cap_kills_endless_producer(tmp_path):
    root, *_ = make_repo(tmp_path)
    fake = fake_git(tmp_path, "exec yes aaaaaaaaaaaaaaaa")
    t = time.monotonic()
    with pytest.raises(GitError, match="exceeded"):
        run_git(root, ["status"], EventLog(), max_bytes=1000, git_bin=fake, timeout=20)
    assert time.monotonic() - t < 10


def test_timeout_kills_hung_process(tmp_path):
    root, *_ = make_repo(tmp_path)
    fake = fake_git(tmp_path, f"touch {tmp_path}/started\nsleep 60")
    t = time.monotonic()
    with pytest.raises(GitError, match="timed out"):
        run_git(root, ["status"], EventLog(), timeout=0.5, git_bin=fake)
    assert time.monotonic() - t < 10
    assert (tmp_path / "started").exists()  # it really started, and was killed


def test_nonzero_exit_raises_with_stderr(tmp_path):
    root, *_ = make_repo(tmp_path)
    with pytest.raises(GitError) as ei:
        run_git(root, ["rev-parse", "--verify", "no-such-ref"], EventLog())
    assert ei.value.returncode not in (0, None)
