# OBSERVATION — 2026-11-24 — shift diagnostic (results/diagnostics/shift_by_group.json), before any full-run E2 result
Domain separability (Gini of a 2-fold LightGBM, target network vs pooled sources, random_train pools, 20k per side) is near-total on ALL features for both benign and attack flows (0.999–1.0). Per group, the picture differs by class:
- TTL: benign Gini 0.95–1.00 for UNSW/TON/CIC (0.80 BOT, only 933 benign flows) — but attack Gini is low for TON (0.27) and BOT (0.46) and high for UNSW (1.00) and CIC (0.96).
- App fields (DNS/FTP/ICMP): benign 0.58–0.86, attack 0.05–0.81.
- TCP window: ~0.87–0.98 in both classes everywhere.
So TTL looks like a benign-side environment signature for TON and BOT targets (their attacks resemble the other networks' attacks in TTL, but their benign traffic does not), and a both-sides signature for UNSW and CIC. This is a measurement only; whether it explains detection loss is H2, tested when E2 finishes.
