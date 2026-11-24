# HANDOFF — read this first (updated 2026-11-24, session 2)

## Where we are
- **Cycle 1**, phase RUN_FULL: plan_v1 full run (376 jobs) launched 2026-11-24 03:52 UTC in tmux session `nids`. Est. ~7 CPU-h wall on 4 cores. Tuning jobs take ~6 min each.
- **NEXT ACTION:**
  1. `cd project && python3 scripts/status.py`. If this is a **fresh container**, data/ is gone: run `bash scripts/get_data.sh` (≈5 min; row counts must be UNSW 2,365,424 / BOT 16,933,808 / TON 27,520,260 / CIC 20,115,529), then `bash scripts/launch_full.sh` (resumes: finished jobs are in results/ + state/queue.json, which autosave pushes to git), then `setsid nohup bash scripts/autosave.sh >/dev/null 2>&1 &`.
  2. When the queue is done, run_all.py calls `scripts/final_report.py` automatically (or run it by hand). Then: update gates, novelty score (expect ≤ 10, see below), variants_tried.csv (add V2 = plan_v1 full run, all arms), journal RESULT entries.
  3. Cycle 2 = Section 6.4 ladder (diagnose with the saved scores in results/scores/*.npz). The key question: is there anything **not** already in Gazi et al.'s code? Candidates logged in D15/journal 06: counterfactual "transplant" attribution of single feature groups (vs their drop-and-retrain), data-driven environment-feature selection (ESF), random-vs-chrono pools. If novelty stays ≤ 14 after cycle 2 → pivot is allowed (6.5 needs ≥2 cycles).

## One-liners
- Journal: JKSU-CIS (Springer Nature), JIF 6.4 (2025), verified median Received→Accepted 83.5 d (n=596) — **fails 72-day rule**; Q1 only partially verified. Frontiers checked this session (user allowed it): none ≤ 72 d (Frontiers in AI 83.5 d, n=300) → D17 keep JKSU-CIS.
- Topic: cross-network (leave-one-dataset-out) generalization of flow-based NIDS on the four UQ NetFlow-V3 datasets.
- Hypothesis H1: LODO collapse is driven by benign "environment-signature" features; ESF / PEN help. **Prior art now confirmed from code:** Gazi et al. (Zenodo 10.5281/zenodo.24172401) have BRN (== our PEN), feature-group drop ablation, failure decomposition and benign-divergence audit (journal 06, D15). Cycle 1 is therefore an independent replication (D16).

## Running now
- tmux session `nids`: `python3 run_all.py --mode full --resume` (lock in state/, heartbeat state/heartbeat).
- `scripts/autosave.sh` (setsid background): every 20 min commits results/ state/ journal/ and pushes to branch `claude/awesome-fermi-gqc7vh`. Stop: `touch state/STOP_AUTOSAVE`.

## Compute
Cycle 1 ≈ 0.4 CPU-h used so far of 15 h; global ≈ 0.6 of 120 h (state/budget.json, live). Machine: 4 CPU cores, 15 GB RAM, no GPU.

## Gates
| Gate | Status |
|---|---|
| G1 journal | FAIL on 72-day rule (stated): no legitimate in-scope journal verified ≤72 d among 30 Springer + 5 Frontiers |
| G2 prior art | FAIL: 54 papers opened (≥30 OK), but close prior work (Gazi code) covers our claims; P02 full text blocked (403) |
| G3 novelty | FAIL (self-estimate ≤ 10/25 for H1 as planned) |
| G4–G9 | unknown (full run in progress) |
| G10, G11 | not started (audit_numbers.py exists) |

## Last decisions (state/decisions.md)
D9 test locked; D10 source-only selection; D11 random pools for LODO, primary = mean macro-F1 UNSW/TON/CIC; D12 NaN→0; D13 Frontiers allowed (user); D14 no pivot yet; D15 Gazi code covers BRN/feature groups; D16 run plan_v1 anyway as replication; D17 keep JKSU-CIS; D18 re-sent master prompt = continue.

## Failures / problems so far
1. Elsevier/ScienceDirect 403. 2. ESF τ=0.8 dropped 0 features → τ∈{0.3,0.4,0.5}. 3. NaN/inf in UNSW/BOT zero-duration flows. 4. Chrono splits contain unseen attack families; BOT ~no benign. 5. First quick mode too long. 6. Sub-agent could not write .md. 7. Session-2 first get_data attempt failed because logs/ did not exist (fixed: mkdir). 8. preprints.org (P02 full text) blocks curl and headless Chromium (403). 9. Frontiers n=80 sample misleading (71.5 d) vs n=300 (83.5 d).

## Commands
- Status: `python3 scripts/status.py` • Logs: `tail -f logs/run_all_full.log`
- Start/resume: `bash scripts/launch_full.sh` • Stop: `tmux kill-session -t nids; pkill -f run_all.py; pkill -f run_job.py`
- Report: `python3 scripts/final_report.py` (writes results/metrics.json, statistics.json, RESULTS_SUMMARY.md, tables/, figures/) • Audit: `python3 scripts/audit_numbers.py`
- Supervisor (persistent machine only): `bash scripts/supervisor.sh` (stop: `touch state/STOP`); autostart `bash scripts/install_autostart.sh`; remove: `crontab -l | grep -v p_c1_6_nids | crontab -`
- **Honest note:** this cloud container has no cron/systemd and is reclaimed when idle; autostart/supervisor do not work here. Continuity = git branch + BOOTSTRAP_PROMPT.txt + autosave.sh.

## Files
journal_selection/ (times_<ISSN>.json, comparison incl. Frontiers section, selected) • literature/ (matrix, reported_results.md, prior_art.md) • state/novelty_ledger.json (54 papers) • topic/selected_topic.md • experiments/plan_v1.yaml • src/ • run_all.py • scripts/ (final_report.py, audit_numbers.py, frontiers_times.py, autosave.sh new) • journal/ENTRIES/ (00–07) • results/quick/ (smoke only).
