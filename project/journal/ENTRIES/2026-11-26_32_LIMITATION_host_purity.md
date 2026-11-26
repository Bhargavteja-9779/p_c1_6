# 32 LIMITATION — how much of host context is a testbed artefact? (seed 42, computed before the TEST results were read)
NF-UNSW-NB15-v2: 100 % of test attack flows come from source IPs that also appear in benign training; an attacker's test flows are
83.8 % attacks on average. Host context there is a genuine mixture of behaviours, not an identity lookup.
NF-CSE-CIC-IDS2018-v2: only 11.5 % of test attack flows come from source IPs seen in benign training; attacker hosts' test flows are
93.1 % attacks. Dedicated attacker machines in the CIC testbed make "this host only does odd things" easy, so the CIC gain overstates
what host context would give on a production network where compromised hosts also carry benign traffic. The graph baselines
(Anomal-E, GraphIDS, GDAE) aggregate exactly the same host neighbourhood, so the comparison with them stays fair, but the paper must
state this, report UNSW (mixed hosts) as the more realistic case, and add a mixed-host analysis (gain restricted to attack flows whose
source IP also emits benign flows).
