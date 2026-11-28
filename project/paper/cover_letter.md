# Cover letter (draft — author fields to be completed)

Dear Editor,

We submit the manuscript "HoCo-kNN: training-free host-context nearest neighbours for benign-only NetFlow intrusion detection" for
consideration in the Journal of King Saud University – Computer and Information Sciences.

The journal recently published GDAE (doi:10.1007/s44443-026-01241-0), a dual-autoencoder graph detector for benign-only NetFlow
intrusion detection. Our manuscript follows GDAE's protocol exactly (NF-UNSW-NB15-v2 and NF-CSE-CIC-IDS2018-v2, random 8:1:1 splits,
the same five seeds) and shows that a detector with no trained parameters — nearest neighbours on log-rescaled flow features plus the
closed-form mean behaviour of the source host — obtains higher PR-AUC than GDAE and the other graph models in its comparison on both
datasets, on a CPU and without any attack labels, including for model selection and thresholds. We report where our detector is
weaker (Macro-F1 on NF-UNSW-NB15-v2) and how much of the host-context gain on NF-CSE-CIC-IDS2018-v2 comes from the testbed design.

We believe the work will interest the journal's readers because it offers practitioners a cheap, transparent and reproducible detector,
and because it clarifies what the graph component of recent NIDS models actually contributes. All code and the frozen experiment plan
will be released.

The manuscript is not under consideration elsewhere. [Conflicts of interest, funding and author statements to be completed by the authors.]

Sincerely,
[Corresponding author, affiliation — to be completed]
