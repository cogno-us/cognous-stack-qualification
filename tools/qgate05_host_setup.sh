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
#   * BASE=/var/lib/qgate05-ocs (root:root 0755, must not pre-exist) and BASE/tmp (root:root 0755). The suite's TMPDIR points at BASE/tmp so the NC4
#     state tree is created by tempfile.mkdtemp under /var/lib, NOT under /tmp (sticky, other-writable) and NOT under /opt (the ACL FAIL seen in QGATE-02/03);
#     (the real-kill harness also creates its own durable work dir with tempfile under TMPDIR, i.e. under BASE/tmp; there is no separate durable directory and no durable-directory environment variable);
#   * read access for the ingress uid: chmod -R go+rX,go-w on the workspace and go+x on its ancestors (the ingress runs as another uid and must read the
#     component checkouts; no write access is granted);
#   * Yama (restores the ORIGINAL host profile v1, which the workflow established with `sudo sysctl -w kernel.yama.ptrace_scope=1`): kernel.yama.ptrace_scope is read
#     BEFORE (as found) and, only if the file exists and the as-found value is numerically below 1, raised to 1 with `sudo sysctl -w kernel.yama.ptrace_scope=1`. It is NEVER
#     lowered (1, 2 and 3 are left untouched) and never faked: if Yama is absent or the sysctl fails, nothing is substituted and the suite reports the boundary tests BLOCKED
#     (verdict INCOMPLETE). Both the as-found and the effective value are written to EVDIR/yama-record.json and provision-summary.out. NO ACL change.
#   * the setgid IPC directory (2751, bounded synthetic test only, NOT production) is created by suites/mvp-chain/_ingress.py, not here; this script records it
#     in the run (the environment record and the suite's observations carry its stat).
# Exports (appended to $GITHUB_ENV when set): MVP_INGRESS_PROFILE, MVP_INGRESS_USER, MVP_CLIENT_USER, MVP_IPC_GROUP, MVP_QUALIFICATION_SHA, QG5_BASE, QG5_TMP.
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
  rec "base-stat-$l"   bash -c 'for p in "$0" "$0/tmp" /var/lib /var /; do stat -c "%n %U:%G %a %F" "$p" 2>&1; done' "$BASE"
  rec "base-acl-$l"    bash -c 'command -v getfacl >/dev/null || { echo "getfacl not installed"; exit 0; }; for p in "$0" "$0/tmp" /var/lib /var /; do getfacl -p "$p" 2>&1; done' "$BASE"
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
YAMA=/proc/sys/kernel/yama/ptrace_scope
YAMA_FOUND=absent; [ -r "$YAMA" ] && YAMA_FOUND=$(cat "$YAMA" 2>/dev/null)
[ -z "$(getent passwd 65533)" ] || { echo "uid 65533 (the outsider probe uid) is in use" >"$EV/provision-fatal.out"; PROV_OK=0; }
[ ! -e "$BASE" ] || { echo "$BASE already exists; refusing to reuse it" >>"$EV/provision-fatal.out"; PROV_OK=0; }
snapshot before-provision
if [ "$PROV_OK" = 1 ]; then
  rec p-groupadd-ingress sudo groupadd --system mvp-ingress || PROV_OK=0
  rec p-groupadd-client  sudo groupadd --system mvp-client   || PROV_OK=0
  rec p-groupadd-ipc     sudo groupadd --system mvp-ipc      || PROV_OK=0
  rec p-useradd-ingress  sudo useradd --system --no-create-home --shell /usr/sbin/nologin -g mvp-ingress -G mvp-ipc mvp-ingress || PROV_OK=0
  rec p-useradd-client   sudo useradd --system --no-create-home --shell /usr/sbin/nologin -g mvp-client -G mvp-ipc mvp-client || PROV_OK=0
  rec p-mkdir-base       sudo install -d -o root -g root -m 0755 "$BASE" "$BASE/tmp" || PROV_OK=0
  rec p-chmod-workspace  sudo chmod -R go+rX,go-w "$WS" || PROV_OK=0
  rec p-chmod-ancestors  bash -c 'd=$0; while [ "$d" != "/" ]; do sudo chmod go+x "$d" || exit 1; d=$(dirname "$d"); done' "$WS" || PROV_OK=0
fi
# Yama: raise to 1 only when the as-found value is a number below 1; never lower, never fake. A failed or impossible raise is recorded (rc file) and left to BLOCK the boundary rows.
YAMA_ACTION=none
if [ "$YAMA_FOUND" != absent ] && [ "$YAMA_FOUND" -lt 1 ] 2>/dev/null; then
  YAMA_ACTION=raised-to-1
  rec p-sysctl-yama sudo sysctl -w kernel.yama.ptrace_scope=1 || YAMA_ACTION=raise-to-1-FAILED
elif [ "$YAMA_FOUND" = absent ]; then
  YAMA_ACTION=absent-left-as-is
fi
YAMA_EFFECTIVE=absent; [ -r "$YAMA" ] && YAMA_EFFECTIVE=$(cat "$YAMA" 2>/dev/null)
printf '{"yama_ptrace_scope_as_found": "%s", "yama_ptrace_scope_effective": "%s", "action": "%s", "rule": "raised to 1 only if as found < 1; never lowered; absent stays absent and the boundary rows BLOCK"}\n' \
  "$YAMA_FOUND" "$YAMA_EFFECTIVE" "$YAMA_ACTION" >"$EV/yama-record.json"
{ echo "PROVISION_OK=$PROV_OK"; echo "BASE=$BASE"; echo "TMPDIR_FOR_SUITE=$BASE/tmp";
  echo "yama.ptrace_scope.as_found=$YAMA_FOUND"; echo "yama.ptrace_scope.effective=$YAMA_EFFECTIVE"; echo "yama.action=$YAMA_ACTION"; } >"$EV/provision-summary.out"
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
  } >>"$GITHUB_ENV"
fi
logl "provision done PROV_OK=$PROV_OK"
exit 0
