#!/usr/bin/env bash
set -euo pipefail
cd /root/projects/Morning-Newspaper-Assistant
pkill -f '/root/projects/Morning-Newspaper-Manager/runtime/static_dashboard_server.py' || true
pkill -f '/root/projects/Morning-Newspaper-Assistant/runtime/static_dashboard_server.py' || true
nohup /usr/bin/python3 /root/projects/Morning-Newspaper-Assistant/runtime/static_dashboard_server.py >/tmp/morning-newspaper-8510.log 2>&1 &
echo $! > /tmp/morning-newspaper-8510.pid
echo "started 8510 server pid=$(cat /tmp/morning-newspaper-8510.pid)"
