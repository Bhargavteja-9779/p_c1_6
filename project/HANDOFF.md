# HANDOFF — read this first (updated 2026-11-24, session 2)

## Where we are
- **PIVOT #1 declared** (2026-11-24, D26). Topic 1 (cross-network NetFlow NIDS) failed over cycles 1–3: H1 (ESF/PEN) no gain, H2 partial (CIC only), H3 ensemble −0.056. Post-mortem: archive/topic1_nids_crossnet/POSTMORTEM.md. Novelty 9/25.
- Next cycle = **cycle 4**, phase PIVOT_TOPIC_SELECTION. Pivots used 1/3, cycles used 3/12.
- **NEXT ACTION:** Phase 3 again (MASTER_PROMPT Section 5 TOPIC): ≥10 candidates in JKSU-CIS scope, CPU-only (4 cores, no GPU), public data. For the top 3, run the prior-art check (≥8 query phrasings each, and read the closest work's code/paper if any) BEFORE writing code — lesson from topic 1. Then topic/selected_topic.md (new version; keep the old one as topic/selected_topic_v1_nids.md), plan_v4, quick run, full run. Reuse run_all.py / queue / budget / final_report.py / audit_numbers.py / autosave.sh.
- Keep the session awake during long runs (25-min check-ins); restart autosave: `rm -f state/STOP_AUTOSAVE; setsid nohup bash scripts/autosave.sh >/dev/null 2>&1 &`.

## One-liners
- Journal: JKSU-CIS (Springer Nature), JIF 6.4 (2025), verified median Received→Accepted 83.5 d (n=596) — **fails 72-day rule**; Q1 only partially verified. Frontiers checked this session (user allowed it): none ≤ 72 d (Frontiers in AI 83.5 d, n=300) → D17 keep JKSU-CIS.
- Topic: NONE yet (topic 1, cross-network NetFlow NIDS, archived after cycles 1–3).
- Hypothesis H1 (FAILED, journal 10): LODO collapse is driven by benign "environment-signature" features; ESF / PEN help. **Prior art now confirmed from code:** Gazi et al. (Zenodo 10.5281/zenodo.24172401) have BRN (== our PEN), feature-group drop ablation, failure decomposition and benign-divergence audit (journal 06, D15). Cycle 1 is therefore an independent replication (D16).

## Running now
Nothing (cycle 1 queue finished; autosave stopped via state/STOP_AUTOSAVE — delete it and restart autosave.sh before the next long run).

_Previous:_
- tmux session `nids`: `python3 run_all.py --mode full --resume` (lock in state/, heartbeat state/heartbeat).
- `scripts/autosave.sh` (setsid background): every 20 min commits results/ state/ journal/ and pushes to branch `claude/awesome-fermi-gqc7vh`. Stop: `touch state/STOP_AUTOSAVE`.

## Compute (see state/budget.json; cycles 1–3 ≈ 7.0 CPU-h of 120 global)
Cycle 1 ≈ 0.4 CPU-h used so far of 15 h; global ≈ 0.6 of 120 h (state/budget.json, live). Machine: 4 CPU cores, 15 GB RAM, no GPU.

## Gates
| Gate | Status |
|---|---|
| G1 journal | FAIL on 72-day rule (stated): no legitimate in-scope journal verified ≤72 d among 30 Springer + 5 Frontiers |
| G2 prior art | FAIL: 54 papers opened (≥30 OK), but close prior work (Gazi code) covers our claims; P02 full text blocked (403) |
| G3 novelty | FAIL: topic 1 scored 9/25 in cycles 1 and 2 (state/novelty_ledger.json) |
| G4 baselines | partial: 7 baselines, equal 8-config tuning; published NF-v3 LODO numbers not directly comparable (different pools/protocol) |
| G5 main result | FAIL (no arm beats XGB on val; confirmation not run) |
| G6 ablation | done for H1 groups (E2) — components do not help |
| G7 generalization | 4 targets × 3 seeds run |
| G8 leakage | partial (source-only selection, test locked); duplicate check not yet run |
| G9 reproducibility | unknown |
| G10, G11 | not started (audit_numbers.py exists) |

## Last decisions (state/decisions.md)
D9 test locked; D10 source-only selection; D11 random pools for LODO, primary = mean macro-F1 UNSW/TON/CIC; D12 NaN→0; D13 Frontiers allowed (user); D14 no pivot yet; D15 Gazi code covers BRN/feature groups; D16 run plan_v1 anyway as replication; D17 keep JKSU-CIS; D18 re-sent master prompt = continue.

## Failures / problems so far
1. Elsevier/ScienceDirect 403. 2. ESF τ=0.8 dropped 0 features → τ∈{0.3,0.4,0.5}. 3. NaN/inf in UNSW/BOT zero-duration flows. 4. Chrono splits contain unseen attack families; BOT ~no benign. 5. First quick mode too long. 6. Sub-agent could not write .md. 7. Session-2 first get_data attempt failed because logs/ did not exist (fixed: mkdir). 8. preprints.org (P02 full text) blocks curl and headless Chromium (403). 9. Frontiers n=80 sample misleading (71.5 d) vs n=300 (83.5 d). 10. 04:20–08:41 UTC: worker restart (user usage limit) killed the tmux run; resumed 08:41, interrupted job retried as attempt 2 (journal 08). Compute runs die when the session idles — keep check-ins going.

## Commands
- Status: `python3 scripts/status.py` • Logs: `tail -f logs/run_all_full.log`
- Start/resume: `bash scripts/launch_full.sh` • Stop: `tmux kill-session -t nids; pkill -f run_all.py; pkill -f run_job.py`
- Report: `python3 scripts/final_report.py` (writes results/metrics.json, statistics.json, RESULTS_SUMMARY.md, tables/, figures/) • Audit: `python3 scripts/audit_numbers.py`
- Supervisor (persistent machine only): `bash scripts/supervisor.sh` (stop: `touch state/STOP`); autostart `bash scripts/install_autostart.sh`; remove: `crontab -l | grep -v p_c1_6_nids | crontab -`
- **Honest note:** this cloud container has no cron/systemd and is reclaimed when idle; autostart/supervisor do not work here. Continuity = git branch + BOOTSTRAP_PROMPT.txt + autosave.sh.

## Files
journal_selection/ (times_<ISSN>.json, comparison incl. Frontiers section, selected) • literature/ (matrix, reported_results.md, prior_art.md) • state/novelty_ledger.json (54 papers) • topic/selected_topic.md • experiments/plan_v1.yaml • src/ • run_all.py • scripts/ (final_report.py, audit_numbers.py, frontiers_times.py, autosave.sh new) • journal/ENTRIES/ (00–07) • results/quick/ (smoke only).
