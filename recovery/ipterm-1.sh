#!/bin/sh
# Run only inside ipterm-1's trusted console. Default is read-only.
set -eu
[ "$(hostname)" = "ipterm-1" ] || { echo "Wrong client; stopped" >&2; exit 1; }
[ "$(id -u)" = 0 ] || { echo "Root required" >&2; exit 1; }
ip link show dev eth0 >/dev/null
addresses=$(ip -4 -o addr show dev eth0 | awk '{print $4}')
routes=$(ip -4 route show default)
[ -z "$addresses" ] || [ "$addresses" = "172.16.0.10/24" ] || { echo "Conflicting address; stopped" >&2; exit 1; }
if [ -n "$routes" ]; then
 [ "$(printf '%s\n' "$routes" | wc -l)" -eq 1 ] || { echo "Multiple default routes; stopped" >&2; exit 1; }
 printf '%s\n' "$routes" | grep -Eq '^default via 172\.16\.0\.1 dev eth0( |$)' || { echo "Conflicting default route; stopped" >&2; exit 1; }
fi
if [ "${1:-}" != "--apply" ]; then
 echo "Preflight passed. Use --apply after confirming 172.16.0.10 is reserved for this client."
 ip -4 addr show dev eth0
 ip -4 route
 exit 0
fi
ip link set dev eth0 up
[ -n "$addresses" ] || ip addr add 172.16.0.10/24 dev eth0
[ -n "$routes" ] || ip route add default via 172.16.0.1 dev eth0
ip -4 addr show dev eth0
ip -4 route
