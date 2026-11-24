# OBSERVATION — 2026-11-24 — the machine
The machine has no GPU (no nvidia-smi), 4 CPU cores, 15 GB RAM, Python 3.13, and runs in an ephemeral cloud container. Everything must be CPU-feasible, and anything not pushed to git is lost when the container is reclaimed. "GPU hours" in the config are therefore counted as CPU compute hours.
