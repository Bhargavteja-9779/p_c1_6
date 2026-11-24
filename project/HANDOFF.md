# HANDOFF — read this first (updated 2026-11-24, session 2)

## Where we are
- **Cycle 1**, phase RUN_FULL. plan_v1 (376 jobs) was launched at 21:01 in this container. plan_v2 (E7 transplant, 48 jobs) is written; run_all now expands *all* plan versions, so v2 jobs are queued the next time run_all starts.
- Branch for this session: `claude/admiring-archimedes-xzq77t` (pushed after each step). Session 1 used `claude/cool-ptolemy-6dtl6w`; this branch contains all of it.
- **NEXT ACTION (in this order):**
  1. If this is a NEW container: data/ is not in git → `cd project && bash scripts/get_data.sh` (row counts must be UNSW 2,365,424 / BOT 16,933,808 / TON 27,520,260 / CIC 20,115,529), then `bash scripts/launch_full.sh` (resumes; done jobs are skipped only if their results/<job>.json exist — results/ IS in git).
  2. `python3 scripts/status.py`; when queue has no pending/running: run_all calls `scripts/final_report.py` automatically (or run it by hand), then restart `bash scripts/launch_full.sh` once more so plan_v2 E7 jobs get queued and run.
  3. Phase 2 redo for the new journal: literature matrix of 12–20 Frontiers in AI papers (a sub-agent was collecting it in session 2; if literature/frontiers_ai_matrix.csv does not exist, redo it).
  4. After E1/E2/E7: evaluate H2a–H2d (plan_v2 header), update gates, novelty score, variants_tried.csv, journal entries; write plan_v3 (E6 confirmation on seeds 100–104 of whatever claim survives; target TEST unlocked only there).

## One-liners
- Journal: **Frontiers in Artificial Intelligence** (2624-8212), JIF 6.7 (publisher page), median Received→Accepted **81 d** (n=150, our computation) → **fails 72-day rule**; Q1 only via aggregator. Fallback JKSU-CIS (83.5 d, JIF 6.4). D16/D18.
- Topic: cross-network (leave-one-dataset-out) generalization of flow-based NIDS on the four UQ NetFlow-V3 datasets.
- Contribution (narrowed, D15): **interventional attribution** of LODO loss to feature groups (transplant one group's benign/attack values from source networks vs within-target shuffle control), across lgbm/xgb/rf/mlp. ESF/PEN/CORAL/DANN results = replication of Gazi et al. 2026 (P01), who already pre-registered BRN vs DomNorm vs CORAL/DANN.

## Running now
tmux session `nids` (or setsid nohup) → `python3 run_all.py --mode full --resume`. Container is ephemeral: if it is gone, follow NEXT ACTION 1.

## Compute
Ledger state/budget.json (cycle "1" + quick 0.25 h). Ceilings 15 h/cycle, 120 h global. Machine: 4 CPU cores, no GPU. Observation: MLP-family tuning jobs take ~15 min each (plan estimate of 7 h is probably low).

## Gates
| Gate | Status |
|---|---|
| G1 journal | FAIL on 72-day rule (stated; 34 journals computed, none with a JIF meets it) |
| G2 prior art | partial: 53 abstracts + full deposits of P01, P04, full texts Layeghy&Portmann, Sarhan (literature/prior_art_fulltext.md); P02 full text blocked (403) |
| G3 novelty | unknown; differentiation now rests on the interventional attribution |
| G4–G9 | unknown (full run in progress) |
| G10, G11 | not started (audit script exists: scripts/audit_numbers.py) |

## Last decisions (state/decisions.md)
D9 test locked until confirmation • D11 primary metric = mean target macro-F1 over UNSW/TON/CIC • D13 Frontiers allowed • D14 no pivot yet • D15 narrow to interventional attribution • D16 Frontiers in AI candidate • D17 transplant "rest" split into 4 subgroups (after one smoke job; logged as forking path) • D18 n=150 → 81 d, still selected.

## Failures / problems so far
1. Elsevier/ScienceDirect blocked (403). 2. ESF τ=0.8 dropped 0 features → τ∈{0.3,0.4,0.5}. 3. NaN/inf only in UNSW/BOT (zero-duration flows). 4. Chrono splits contain unseen attack families; BOT ~no benign. 5. First quick mode too long → restricted. 6. Sub-agent could not write .md files. 7. preprints.org blocks P02 full text (403). 8. P01's results not released (only code). 9. Frontiers in AI n=60 median 71.5 d was sampling noise (n=150: 81 d).

## Commands (from project/)
- Status: `python3 scripts/status.py` • Logs: `tail -f logs/run_all_full.log`
- Start/resume: `bash scripts/launch_full.sh` • Stop: `tmux kill-session -t nids; pkill -f run_all.py; pkill -f run_job.py`
- Report: `python3 scripts/final_report.py` • Audit: `python3 scripts/audit_numbers.py`
- Journal times: `python3 scripts/journal_times.py <ISSN>` (Crossref-deposit publishers) / `python3 scripts/frontiers_times.py <ISSN> --n 150`
- Supervisor/autostart (persistent Linux box only): `bash scripts/supervisor.sh`, `bash scripts/install_autostart.sh`; remove: `crontab -l | grep -v p_c1_6_nids | crontab -`. **They do not work in this cloud container** (no cron/systemd; reclaimed when idle). Continuity = git branch + BOOTSTRAP_PROMPT.txt.

## Files
journal_selection/ (times_<ISSN>.json, comparison, selected) • literature/ (matrix CSV, reported_results.md, prior_art.md, prior_art_fulltext.md) • state/ • topic/selected_topic.md • experiments/plan_v1.yaml, plan_v2.yaml • src/ (prepare_data, nids, mlp, run_job, transplant) • run_all.py • scripts/ (final_report, audit_numbers, frontiers_times, …) • journal/ENTRIES/ • results/quick/ (smoke only, not for claims).
