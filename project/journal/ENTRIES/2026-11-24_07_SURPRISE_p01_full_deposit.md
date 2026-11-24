# 2026-11-24 — SURPRISE — the closest prior work already pre-registered our remedy test

I had the code deposit of Gazi et al. 2026 (P01) read in full. It already contains a benign-referenced per-testbed
normalization (BRN) with a mixture control, CORAL/DANN/AdaBN/TENT, identifier/artifact feature removal and a
drop-one-group XGBoost ablation, all under leave-one-testbed-out on NF-v3 with source-only tuning and pre-declared
hypotheses. Their results are not released yet. Valencia Vélez 2026 (P04) shows feature removal does not rescue transfer.
So my H1 remedy (ESF/PEN) is not a novel test. What I could not find anywhere is an *interventional* attribution:
swapping one feature group's benign distribution between networks and measuring how much of the loss disappears.
That is the direction I take next (decision D15). The plan_v1 run continues unchanged; its ESF/PEN arms become a replication.
