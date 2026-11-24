# HANDOFF — read this first (updated 2026-11-24, end of session 1)

## Where we are
- **Cycle 1**, phase: BUILD done → full run NOT yet started. Quick run passed (32/32 jobs, results/quick/).
- **NEXT ACTION (do in this order):**
  1. `cd project && bash scripts/get_data.sh` (data/ is NOT in git: re-downloads ~1.4 GB and rebuilds the 24 pools; row counts must match: UNSW 2,365,424 / BOT 16,933,808 / TON 27,520,260 / CIC 20,115,529).
  2. `python3 scripts/status.py`, then `bash scripts/launch_full.sh` (runs plan_v1, 376 jobs, est. ~7 CPU-h, resumable).
  3. While it runs: the user said **Frontiers journals are now allowed** (message 2026-11-24, overrides the Section 4 exclusion). Run `python3 scripts/journal_times.py <Frontiers ISSNs>` (e.g. Frontiers in Computer Science 2624-9898, Frontiers in AI 2624-8212, Frontiers in Big Data 2624-909X, and any Frontiers journal with a JIF that fits) — first check Frontiers deposits Received/Accepted in Crossref `assertion`; if not, scrape article pages with Playwright. Update journal_selection/*.md and decisions.md.
  4. Prior art: get FULL TEXTS of Gazi et al. 2026 (zenodo 10.5281/zenodo.24172400), Rayamajhi 2026 (10.20944/preprints202610.1041.v1), Valencia Vélez 2026 (Zenodo), Layeghy & Portmann 2023 (10.1016/j.compeleceng.2023.108692). Decide whether contribution narrows to (a) attribution of LODO loss to benign-shift feature groups or (b) pre-registered remedy test (see literature/prior_art.md "Blunt verdict").
  5. When the run ends: write scripts/final_report.py (not yet written! run_all.py calls it at queue end — it will just fail harmlessly) + scripts/audit_numbers.py; update gates, novelty score, journal entries, variants_tried.csv; then plan_v2.

## One-liners
- Journal: JKSU-CIS (Springer), JIF 6.4 (2025), verified median Received→Accepted 83.5 d (n=596) — **fails 72-day rule**; Q1 only partially verified.
- Topic: cross-network (leave-one-dataset-out) generalization of flow-based NIDS on the four UQ NetFlow-V3 datasets.
- Hypothesis H1: LODO collapse is largely caused by "environment-signature" features (benign-traffic differences between networks); ESF (drop env-discriminative features) and PEN (per-network quantile normalization) may help. **Prior-art warning:** LODO on all four NF-v3 sets already done (Gazi 2026, Rayamajhi 2026).

## Running now
Nothing (container is ephemeral; session ending).

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
