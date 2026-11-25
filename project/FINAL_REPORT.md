# FINAL REPORT — status at 2026-11-25 (honest exit summary, MASTER_PROMPT §11.7)

## 1. Bottom line
**There is no submission-ready paper yet, and submitting one now would very likely be rejected.**
We have not produced a method that beats the JKSU-CIS paper we compete with (HF-DIF), or even one that significantly beats a plain
Isolation Forest on its datasets. Writing a manuscript that claims otherwise would require invented numbers, which this project forbids.
What we do have is a verified benchmark, a reproducibility audit of HF-DIF, and a well-documented set of negative results.

## 2. Target journal and the paper to beat
- Journal: J. King Saud Univ. – Computer and Information Sciences (Springer Nature), JIF 6.4; measured median received→accepted
  83.5 days (n = 596) — passes the user's relaxed ≈80-day rule only approximately (journal_selection/).
- Comparable JKSU-CIS papers read (journal_selection/jksu_profile.md, literature/journal_benchmark.md):
| Paper | Task | Claimed result | Rigour observed |
|---|---|---|---|
| HF-DIF (10.1007/s44443-026-00706-6) | unsupervised tabular AD, 20 ADBench sets | AUC-ROC 82.6, AUC-PR 34.9 | 10 seeds, t-test+Holm, GPU, **no code**, contradictory split description |
| GAMP (10.1007/s44443-025-00021-6) | tabular AD (CWRU+ODDS) | "+10.7 % AUC" | no seeds, no statistics, baseline count inconsistent |
| SIGMA-AD (10.1007/s44443-026-01284-3) | multivariate time-series AD | PA-F1 92.2 (raw F1 31.6) | 5 seeds, Holm, code on acceptance |
| GDAE (10.1007/s44443-026-01241-0) | NetFlow graph AD | PR-AUC 0.859 / 0.949 | 5 seeds, no statistics |
Accepted JKSU-CIS method papers share one pattern: a named method, many baselines, a clear average win, ablation, runtime.
The win is the non-negotiable part — and it is exactly what we do not have.

## 3. What was done and what improved (topic 2, this line of work)
| Item | Before | Now | Evidence |
|---|---|---|---|
| HF-DIF protocol | ambiguous (paper states two incompatible splits) | resolved: transductive contaminated; our ECOD/iForest reproduce their columns (+1.7 / +0.4) | journal 19, D34, results/t2_eval_stats.json |
| HF-DIF data quality | taken at face value | their Backdoor baselines look broken (ECOD 50.0 vs our 84.6; COPOD 51.0 vs 78.9) | journal 19 |
| DIF baseline | their 69.1 (15 sets) | our CPU PyOD-DIF 60.6, −8.5, p = 0.008 → their DIF column does not reproduce | journal 27 |
| Tuning hygiene | method designed on the evaluation sets (HF-DIF) | design on 27 disjoint DEV sets, one frozen EVAL run, predictions written first | D35, plan_v4.yaml |
| Mechanism | — | contaminated kNN improves monotonically with k (68.9 → 82.8, k 1 → 100 on DEV): masking by clustered anomalies | journal 21–22 |
| Best method on EVAL | iForest 66.5 / kNN 64.9 (18 sets) | kNN k=10 % n 69.1 (+2.7, **not significant**, p = 0.26) | journal 27 |
| vs HF-DIF (reported) | 82.6 | still −12.1 points, 0/18 wins | journal 27 |
Dead ends (all logged, all on DEV): trimmed references, projection pursuit, pseudo-label self-training, noise-contrastive
classifiers, multi-representation kNN, label-free scale selection, locally whitened kNN, AntiHub (journals 20–26). Oracle check:
even choosing the best detector per dataset with hindsight gives only +1.4 on DEV (journal 24).
The parallel session line (branch claude/admiring-archimedes-xzq77t, cycle 5) reached the same conclusion with a different protocol
(H4–H7 failed; "reference-set family exhausted").

## 4. Quality gates
| Gate | Status |
|---|---|
| G0 journal fit | PASS (named-method tabular AD is a frequent JKSU-CIS paper type) |
| G1 journal time | PASS only under user relaxation (83.5 d vs ≈80 d) |
| G2 prior art | partial (HF-DIF full text, survey of 2024–26 tabular AD; Zimek 2013 subsampling, AntiHub covered) |
| G3 novelty > 25/30 | **FAIL** (honest estimate 12/30: masking-scale observation is known in spirit; no new method survives) |
| G4 baselines reproduced | PASS for iForest/ECOD; DIF does not match the paper (documented) |
| G5 main result | **FAIL** (journal 27) |
| G6–G11 | not reached (no method worth ablating / writing up) |

## 5. Why a paper written today would not be accepted
1. JKSU-CIS reviewers compare against the journal's own prior work; −12 AUC-ROC points to HF-DIF is disqualifying.
2. Our only positive effect (+2.7 over iForest) is not statistically significant on 18–20 datasets.
3. A "reproducibility audit of HF-DIF" cannot be conclusive without their code (not released); it would read as a comment, a paper
   type JKSU-CIS rarely publishes (jksu_profile.md).

## 6. What would make it acceptable (recommended next steps)
A. **Representation + scale method (most promising, matches the parallel line's cycle 5):** HF-DIF's gains sit on Wilt, Optdigits,
   Vowels, Landsat, Satellite — sets where *learned or projected representations* matter. Combine our masking-safe scale with a
   cheap learned representation (e.g. random-network ensembles as in DIF, but scored by large-k kNN), designed on DEV, frozen, one EVAL run.
B. **Ask the HF-DIF authors for code** (to be done by a human author). If their numbers do not reproduce, a benchmark/reproducibility
   paper becomes viable — better suited to a journal that publishes such work (e.g. a data/benchmark venue) than to JKSU-CIS.
C. **Pivot** (pivot 2 of 3 is allowed): directions in jksu_profile.md §"Candidate directions" with weaker JKSU comparators —
   e.g. GAMP (no statistics) or GDAE (no statistics), where a rigorous CPU method has a realistic chance to win.

## 7. What a human must fill in for any eventual submission
Authors, affiliations, funding, ethics/AI-use declarations, cover letter signature; contact HF-DIF authors for code (§6B).

## Reproduce
`bash scripts/get_data_adbench.sh` → `pip install pyod==3.6.9 torch` → `bash scripts/run_t2_baselines.sh` →
`python3 src/ad/bench.py --protocol transd --methods scknn_F0.1,fuse_F0.1_w0.5 --seeds 0-9 --datasets hfdif20 --max_n 1000000` →
`python3 scripts/t2_eval_report.py`. Use OMP_NUM_THREADS=1 when running several jobs in parallel.
