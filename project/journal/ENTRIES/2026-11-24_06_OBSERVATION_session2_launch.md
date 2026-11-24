# 2026-11-24 — OBSERVATION — session 2: data rebuilt, full run launched

New container (session 2). I re-downloaded the four NetFlow-V3 parquet files and rebuilt the 24 pools with
scripts/get_data.sh. Row counts match session 1 exactly: UNSW 2,365,424; BOT 16,933,808; TON 27,520,260;
CIC 20,115,529 (logs/get_data.log). I then launched plan_v1 (376 jobs) with scripts/launch_full.sh at 21:01.
I also wrote scripts/final_report.py and scripts/audit_numbers.py, which session 1 had left unwritten.
