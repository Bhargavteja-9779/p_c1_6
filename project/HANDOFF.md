# HANDOFF — read this first (updated 2026-11-24, session 2)

## Where we are
- **PIVOT #1** (D26): topic 1 (cross-network NetFlow NIDS) archived after cycles 1–3 (archive/topic1_nids_crossnet/POSTMORTEM.md). Next cycle = **cycle 4**, phase PIVOT_TOPIC_SELECTION. Pivots 1/3, cycles 3/12, compute ≈7.0/120 CPU-h.
- **User amendments (end of MASTER_PROMPT.md, D27–D32):** ≈80-day acceptance OK (JKSU-CIS 83.5 d → G1 pass by override); novelty must exceed **25/30** (6th dimension = prior-art clearance); new **G0 journal-fit gate** (topic must match what JKSU-CIS publishes, ≥4/5) and **beat-the-journal gate** (beat comparable JKSU-CIS papers, literature/journal_benchmark.md); follow JKSU-CIS writing style; never stop until top-notch.
- Finding so far (journal_selection/jksu_profile.md): JKSU-CIS mostly publishes NAMED-METHOD papers on public benchmarks; audit/negative-result topics fit poorly.
- **NEXT ACTION:**
  1. Finish journal_selection/jksu_profile.md from ≥40 JKSU-CIS papers (abstracts + ≥6 full texts: structure, datasets, baselines, exact numbers, weaknesses). (A sub-agent was running this in session 2; if its result is not in the file, redo it.)
  2. DONE (D33: tabular AD on ADBench). Remaining from this step: HF-DIF exact protocol + per-dataset tables → literature/journal_benchmark.md; SOTA survey → literature/prior_art_v2/tabular_ad.md; then method design, H4 written BEFORE tests, plan_v4. (Original text:) Choose a CPU-feasible named-method topic in a frequent JKSU area with directly comparable JKSU papers (e.g. tabular / time-series anomaly detection, graph learning). Prior-art check (≥8 phrasings, read closest code/paper) BEFORE code. Write topic/selected_topic.md (old one kept as selected_topic_v1_nids.md), literature/journal_benchmark.md, plan_v4.
  3. Build, quick run, full run (keep session awake; autosave), report, novelty /30, iterate.
- Prior-art checks of earlier candidates: literature/prior_art_v2/*.md (Elliptic = crowded; phishing-dataset audit, NIDS underspecification, Android drift results added when available).

## One-liners
- Journal: JKSU-CIS (Springer Nature), JIF 6.4 (2025), verified median Received→Accepted 83.5 d (n=596) — **fails 72-day rule**; Q1 only partially verified. Frontiers checked this session (user allowed it): none ≤ 72 d (Frontiers in AI 83.5 d, n=300) → D17 keep JKSU-CIS.
- Topic 2 (D33): unsupervised/semi-supervised tabular anomaly detection on ADBench — named-method paper; beat HF-DIF (JKSU-CIS 10.1007/s44443-026-00706-6: avg AUC-ROC 82.6, AUC-PR 34.90 on 20 ADBench sets). Data: `bash scripts/get_data_adbench.sh` (47 .npz). Baselines via PyOD 3.6.9.
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
| G1 journal | PASS under user-relaxed rule ≈80 d (D27): JKSU-CIS median 83.5 d (n=596); original 72-d rule failed (stated) |
| G2 prior art | FAIL: 54 papers opened (≥30 OK), but close prior work (Gazi code) covers our claims; P02 full text blocked (403) |
| G3 novelty | FAIL: target now > 25/30 (D28); topic 1 scored 9/25 |
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
