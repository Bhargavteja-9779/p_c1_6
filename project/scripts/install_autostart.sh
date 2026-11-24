#!/usr/bin/env bash
# For a persistent Linux machine with cron. Remove with: crontab -l | grep -v p_c1_6_nids | crontab -
P=$(cd "$(dirname "$0")/.." && pwd)
( crontab -l 2>/dev/null | grep -v p_c1_6_nids
  echo "@reboot bash $P/scripts/launch_full.sh # p_c1_6_nids"
  echo "@reboot bash $P/scripts/supervisor.sh # p_c1_6_nids"
  echo "*/5 * * * * bash $P/scripts/watchdog.sh # p_c1_6_nids" ) | crontab -
echo installed
