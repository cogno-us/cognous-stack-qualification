#!/usr/bin/env bash
# OCS-MVP-QGATE-05 / Worker C: host provisioning and host-evidence capture for the single authorized mvp-acceptance run.
# PROPOSED, non-authorizing. Runs on a GitHub-hosted ubuntu-24.04 runner as the runner user (passwordless sudo); every host change is on the ephemeral VM.
#
# Usage:
#   qgate05_host_setup.sh provision WORKSPACE EVDIR     create the throwaway identities, the base path and the read access, then snapshot "pre"
#   qgate05_host_setup.sh snapshot  WORKSPACE EVDIR LABEL   record host state only (no change); LABEL is a file-name part (pre, post)
#
# What provision does (all of it recorded under EVDIR, one <name>.out/.err/.rc per command, nothing aborts early):
#   * refuses to run if uid 65533 (the outsider probe uid) is already allocated;
#   * groups mvp-ingress, mvp-client, mvp-ipc; users mvp-ingress and mvp-client (own primary groups, no home, nologin); mvp-ipc has exactly those two members;
#   * BASE=/var/lib/qgate05-ocs (root:root 0755, must not pre-exist) and BASE/tmp, BASE/durable (root:root 0755). The suite's TMPDIR points at BASE/tmp so the NC4
#     state tree is created by tempfile.mkdtemp under /var/lib, NOT under /tmp (sticky, other-writable) and NOT under /opt (the ACL FAIL seen in QGATE-02/03);
#     BASE/durable is the durable writable store for the real-kill recovery test (A1);
#   * read access for the ingress uid: chmod -R go+rX,go-w on the workspace and go+x on its ancestors (the ingress runs as another uid and must read the
#     component checkouts; no write access is granted);
#   * NO sysctl, NO Yama change, NO ACL change: kernel.yama.ptrace_scope is recorded as found. If it is below 1 the suite reports the boundary test BLOCKED.
#   * the setgid IPC directory (2751, bounded synthetic test only, NOT production) is created by suites/mvp-chain/_ingress.py, not here; this script records it
#     in the run (the environment record and the suite's observations carry its stat).
# Exports (appended to $GITHUB_ENV when set): MVP_INGRESS_PROFILE, MVP_INGRESS_USER, MVP_CLIENT_USER, MVP_IPC_GROUP, MVP_QUALIFICATION_SHA, QG5_BASE, QG5_TMP, QG5_DURABLE_DIR.
# Deliberately no `set -e`: the exit status is 0 unless the script is itself misused (2); failures are visible as nonzero *.rc files and as a BLOCKED/INCOMPLETE gate.

umask 022
mode=$1; WS=$2; EVDIR=$3
case "$mode" in
  provision) [ "$#" -eq 3 ] || { echo "usage: $0 provision WORKSPACE EVDIR" >&2; exit 2; } ;;
  snapshot)  [ "$#" -eq 4 ] || { echo "usage: $0 snapshot WORKSPACE EVDIR LABEL" >&2; exit 2; } ;;
  *) echo "usage: $0 provision|snapshot ..." >&2; exit 2 ;;
esac
WS=$(cd "$WS" 2>/dev/null && pwd -P) || { echo "bad WORKSPACE $2" >&2; exit 2; }
mkdir -p "$EVDIR" || { echo "cannot create EVDIR $EVDIR" >&2; exit 2; }
EV=$(cd "$EVDIR" && pwd -P)
BASE=/var/lib/qgate05-ocs

# rec NAME CMD...: save stdout, stderr and exit status of CMD under EV; never aborts.
rec() { local n=$1; shift; "$@" >"$EV/$n.out" 2>"$EV/$n.err"; local rc=$?; echo "$rc" >"$EV/$n.rc"; return $rc; }
logl() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >>"$EV/host-setup.log"; }

snapshot() {   # snapshot LABEL
  local l=$1
  rec "kernel-$l"      bash -c 'uname -a; cat /proc/version; echo "yama.ptrace_scope=$(cat /proc/sys/kernel/yama/ptrace_scope 2>&1)"; echo "kernel.randomize_va_space=$(cat /proc/sys/kernel/randomize_va_space 2>&1)"; echo "fs.protected_symlinks=$(cat /proc/sys/fs/protected_symlinks 2>&1)"'
  rec "os-release-$l"  cat /etc/os-release
  rec "runner-image-$l" bash -c 'env | grep -E "^(ImageOS|ImageVersion|RUNNER_NAME|RUNNER_OS|RUNNER_ARCH|RUNNER_ENVIRONMENT|GITHUB_(RUN_ID|RUN_NUMBER|RUN_ATTEMPT|SHA|REF|REF_NAME|WORKFLOW|WORKFLOW_REF|WORKFLOW_SHA|EVENT_NAME|REPOSITORY|JOB|ACTOR))=" | sort; ls -l /etc/image-version* /imagegeneration 2>&1; cat /imagegeneration/imagedata.json 2>&1 | head -c 4000'
  rec "id-$l"          bash -c 'id; echo; grep -E "^(Cap(Inh|Prm|Eff|Bnd|Amb)|NoNewPrivs|Seccomp):" /proc/self/status; echo; command -v capsh && capsh --print'
  rec "identities-$l"  bash -c 'getent passwd mvp-ingress mvp-client 65533; getent group mvp-ingress mvp-client mvp-ipc; id mvp-ingress; id mvp-client'
  rec "base-stat-$l"   bash -c 'for p in "$0" "$0/tmp" "$0/durable" /var/lib /var /; do stat -c "%n %U:%G %a %F" "$p" 2>&1; done' "$BASE"
  rec "base-acl-$l"    bash -c 'command -v getfacl >/dev/null || { echo "getfacl not installed"; exit 0; }; for p in "$0" "$0/tmp" "$0/durable" /var/lib /var /; do getfacl -p "$p" 2>&1; done' "$BASE"
  rec "ws-ancestors-$l" bash -c 'd=$0; while :; do stat -c "%n %U:%G %a" "$d"; [ "$d" = / ] && break; d=$(dirname "$d"); done' "$WS"
  rec "mounts-$l"      bash -c 'findmnt -T /var/lib -o TARGET,SOURCE,FSTYPE,OPTIONS 2>&1; echo; findmnt -T "$0" -o TARGET,SOURCE,FSTYPE,OPTIONS 2>&1; echo; df -hT / /var/lib "$0" 2>&1' "$WS"
  rec "resources-$l"   bash -c 'nproc; free -m; uptime'
  rec "listeners-$l"   bash -c 'ss -xlpn 2>&1 | head -50'
}

if [ "$mode" = snapshot ]; then
  snapshot "$4"
  logl "snapshot $4 done"
  exit 0
fi

logl "provision start WS=$WS EV=$EV BASE=$BASE"
PROV_OK=1
[ -z "$(getent passwd 65533)" ] || { echo "uid 65533 (the outsider probe uid) is in use" >"$EV/provision-fatal.out"; PROV_OK=0; }
[ ! -e "$BASE" ] || { echo "$BASE already exists; refusing to reuse it" >>"$EV/provision-fatal.out"; PROV_OK=0; }
snapshot before-provision
if [ "$PROV_OK" = 1 ]; then
  rec p-groupadd-ingress sudo groupadd --system mvp-ingress || PROV_OK=0
  rec p-groupadd-client  sudo groupadd --system mvp-client   || PROV_OK=0
  rec p-groupadd-ipc     sudo groupadd --system mvp-ipc      || PROV_OK=0
  rec p-useradd-ingress  sudo useradd --system --no-create-home --shell /usr/sbin/nologin -g mvp-ingress -G mvp-ipc mvp-ingress || PROV_OK=0
  rec p-useradd-client   sudo useradd --system --no-create-home --shell /usr/sbin/nologin -g mvp-client -G mvp-ipc mvp-client || PROV_OK=0
  rec p-mkdir-base       sudo install -d -o root -g root -m 0755 "$BASE" "$BASE/tmp" "$BASE/durable" || PROV_OK=0
  rec p-chmod-workspace  sudo chmod -R go+rX,go-w "$WS" || PROV_OK=0
  rec p-chmod-ancestors  bash -c 'd=$0; while [ "$d" != "/" ]; do sudo chmod go+x "$d" || exit 1; d=$(dirname "$d"); done' "$WS" || PROV_OK=0
fi
{ echo "PROVISION_OK=$PROV_OK"; echo "BASE=$BASE"; echo "TMPDIR_FOR_SUITE=$BASE/tmp"; echo "DURABLE_DIR=$BASE/durable";
  echo "yama.ptrace_scope(as found, not changed)=$(cat /proc/sys/kernel/yama/ptrace_scope 2>&1)"; } >"$EV/provision-summary.out"
cat "$EV/provision-summary.out"
snapshot pre
if [ -n "${GITHUB_ENV:-}" ]; then
  {
    echo "MVP_INGRESS_PROFILE=approved"
    echo "MVP_INGRESS_USER=mvp-ingress"
    echo "MVP_CLIENT_USER=mvp-client"
    echo "MVP_IPC_GROUP=mvp-ipc"
    echo "MVP_QUALIFICATION_SHA=$(git -C "$WS" rev-parse HEAD)"
    echo "QG5_BASE=$BASE"
    echo "QG5_TMP=$BASE/tmp"
    echo "QG5_DURABLE_DIR=$BASE/durable"
  } >>"$GITHUB_ENV"
fi
logl "provision done PROV_OK=$PROV_OK"
exit 0
