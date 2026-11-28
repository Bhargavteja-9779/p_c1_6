#!/usr/bin/env bash
# Topic 3 data: official UQ NetFlow-v2 datasets (Sarhan, Layeghy, Portmann 2022; UQ RDM, open access, academic use with citation).
# The RDM API returns a short-lived signed S3 URL; files are zips. Idempotent.
cd "$(dirname "$0")/.." && mkdir -p data/nfv2 && cd data/nfv2
declare -A ID=( [NF-UNSW-NB15-v2]=8c6e2a00-ef9c-11ed-827d-e762de186848 [NF-CSE-CIC-IDS2018-v2]=ce5161d0-ef9c-11ed-827d-e762de186848 [NF-ToN-IoT-v2]=a4ad7080-ef9c-11ed-a964-b70596e96ad5 )
for n in "${!ID[@]}"; do
  [ -f "$n.done" ] && continue
  url=$(curl -s "https://api.rdm.uq.edu.au/datasets/${ID[$n]}/download" | python3 -c "import json,sys; print(json.load(sys.stdin)['url'])")
  curl -sS -L --retry 5 -C - -o "$n.zip" "$url" && unzip -o -q "$n.zip" -d "$n" && sha256sum "$n.zip" > "$n.sha256" && rm "$n.zip" && touch "$n.done"
done
find . -name "*.csv" -exec ls -la {} \;
