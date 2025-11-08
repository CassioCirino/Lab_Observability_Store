#!/usr/bin/env bash
# Usage: ./toggle_fault.sh latency on|off
FAULT=${1:-}
STATE=${2:-}
if [[ -z "$FAULT" || -z "$STATE" ]]; then
  echo "Usage: $0 {latency|errors|depSlow|frontLongTask|sqli} {on|off}"
  exit 1
fi
if [[ "$STATE" == "on" ]]; then
  BODY="{\"$FAULT\":{\"enabled\":true}}"
else
  BODY="{\"$FAULT\":{\"enabled\":false}}"
fi
curl -s -X PUT -H 'Content-Type: application/json' -d "$BODY" http://127.0.0.1:8080/admin/faults/config && echo
