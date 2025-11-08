#!/usr/bin/env bash
set -e
# call reset endpoint
curl -s -X POST http://127.0.0.1:8080/admin/reset || echo "reset endpoint failed"
echo "Reset requested."
