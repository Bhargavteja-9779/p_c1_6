# HANDOFF — read this first (updated 2026-11-24, end of session 1)

## Where we are (session 2, 2026-11-24)
- **Cycle 1**, phase: FULL RUN of plan_v1 in progress (tmux session `nids`, 376 jobs, resumable). Data rebuilt; row counts verified identical.
- Done this session: scripts/final_report.py (tested on quick CSV); scripts/frontiers_times.py; literature/prior_art_fulltext.md (Gazi E7/E6/E4 already does group ablation + all-feature benign divergence + removal → our angle narrows); H2 pre-registered (journal 07); src/shift_diagnostics.py → results/diagnostics/shift_by_group.json (journal 08).
- **NEXT ACTION:**
  1. If container is fresh: `bash scripts/get_data.sh` then `bash scripts/launch_full.sh` (resumes; done jobs are kept only if results/ and state/queue.json were committed — commit them periodically!).
  2. Watch `python3 scripts/status.py`. When E1+E2 done: `python3 scripts/final_report.py`, then test H2 (Spearman of E2 Δ vs shift_by_group benign/attack Gini; write scripts/h2_test.py).
  3. Frontiers timing scrape (logs/frontiers_times.out): FCS 2624-9898 median 92 d (n=80) → fails 72 d. Remaining: Front. AI 2624-8212 (IF 6.7 per journal homepage), Big Data 2624-909X (IF 3.8), Comms & Networks (IF 2.7), IoT. Then update journal_selection/*.md + decisions.
  4. Write scripts/audit_numbers.py; update gates, novelty, variants_tried.csv; plan_v2 (E6 confirmation on seeds 100–104 + test) once method frozen.

## One-liners
- Journal: JKSU-CIS (Springer), JIF 6.4 (2025), verified median Received→Accepted 83.5 d (n=596) — **fails 72-day rule**; Q1 only partially verified.
- Topic: cross-network (leave-one-dataset-out) generalization of flow-based NIDS on the four UQ NetFlow-V3 datasets.
- Hypothesis H1: LODO collapse is largely caused by "environment-signature" features (benign-traffic differences between networks); ESF (drop env-discriminative features) and PEN (per-network quantile normalization) may help. **Prior-art warning:** LODO on all four NF-v3 sets already done (Gazi 2026, Rayamajhi 2026).

## Running now
tmux session `nids` running `run_all.py --mode full --resume` (plan_v1).

## Compute
Cycle 1: 0.25 CPU-h (quick runs) of 15 h; global 0.25 of 120 h. Ledger: state/budget.json. Machine: 4 CPU cores, no GPU.

## Gates
| Gate | Status |
|---|---|
| G1 journal | FAIL on 72-day rule (stated); re-check with Frontiers candidates |
| G2 prior art | partial: 53 abstracts opened, 129 queries; full texts of closest works missing; close prior work unaddressed |
| G3 novelty | unknown (likely ≤14 given prior art) |
| G4–G9 | unknown (no full run yet) |
| G10, G11 | not started |

## Last decisions (state/decisions.md D1–D12)
D4 JKSU-CIS; D5 topic; D6 HF mirror data; D7 feature drops; D8/D11 random+chrono pools, LODO on random pools, primary metric = mean target macro-F1 over UNSW/TON/CIC; D9 target TEST locked until confirmation (NIDS_ALLOW_TEST); D10 source-only selection; D12 NaN/inf→0.

## Failures / problems so far
1. Elsevier/ScienceDirect blocked (403) → Elsevier journals unverifiable. 2. ESF τ=0.8 dropped 0 features in smoke test → plan uses τ∈{0.3,0.4,0.5}. 3. NaN/inf only in UNSW/BOT (zero-duration flows). 4. Chronological splits contain unseen attack families; BOT val/test ~no benign. 5. First quick mode was the whole plan (too long) → restricted to UNSW/seed 0. 6. A sub-agent could not write .md files (harness rule) — main agent saved its content.

## Commands
- Status: `python3 scripts/status.py`   • Logs: `tail -f logs/run_all_full.log`
- Start/resume: `bash scripts/launch_full.sh`   • Stop: `tmux kill-session -t nids; pkill -f run_all.py; pkill -f run_job.py`
- Supervisor (agent auto-restart): `bash scripts/supervisor.sh` (stop: `touch state/STOP`)
- Autostart on a persistent Linux box: `bash scripts/install_autostart.sh`; remove: `crontab -l | grep -v p_c1_6_nids | crontab -`
- **Honest note:** this cloud container has no cron/systemd and is reclaimed when idle, so autostart and the supervisor do NOT work here; they are for a persistent machine. Continuity = git branch `claude/cool-ptolemy-6dtl6w` + BOOTSTRAP_PROMPT.txt.

## Files
journal_selection/ (times_<ISSN>.json raw dates + DOIs, comparison, selected) • literature/ (matrix CSV, reported_results.md, prior_art.md) • state/novelty_ledger.json • topic/selected_topic.md • experiments/plan_v1.yaml • src/ (prepare_data.py, nids.py, mlp.py, run_job.py) • run_all.py • journal/ENTRIES/ • results/quick/ (smoke only, not for claims).
