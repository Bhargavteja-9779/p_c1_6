# Selected journal (Phase 1, cycle 1, 2026-11-24)

**Journal of King Saud University – Computer and Information Sciences (JKSU-CIS)**
Publisher: Springer Nature (on behalf of King Saud University; moved from Elsevier to Springer in 2025).
e-ISSN 2213-1248, print ISSN 1319-1578. Journal page: https://link.springer.com/journal/44443

| Field | Value | Evidence / status |
|---|---|---|
| JIF | 6.4 (2025); 5-yr JIF 6.0 (2025) | Official Springer journal page, fetched 2026-11-24 (headless browser) |
| JCR quartile | Q1 — **only partially verified** | Clarivate JCR is paywalled and was not opened. Secondary: King Saud University news (11 Nov 2021, https://news.ksu.edu.sa/en/node/137271) states Q1; LetPub/aggregators state Q1. With JIF 6.4 in "Computer Science, Information Systems" Q1 is very likely but the 2025 quartile itself is UNVERIFIED from Clarivate. |
| Submission → acceptance | **median 83.5 days**, IQR 63–112, range 0–266, 37.2 % of articles ≤ 72 d | Computed by us from publisher-deposited Received/Accepted dates of **596** articles (Crossref, published 2024-11 … 2026-11), file times_2213-1248.json (all DOIs listed). |
| Integrity flags | none found in this session (not exhaustively checked; Retraction Watch database not queried) | UNVERIFIED-complete |
| Scope | Broad computer & information sciences: AI/ML, security, networks, data science, NLP, vision | journal page |
| APC | UNVERIFIED (open access; APC not captured) | — |
| Data/code policy | Springer Nature standard research-data policy (data availability statement required) | UNVERIFIED in detail |

## Rule compliance (G1)
- Reputable publisher: PASS (Springer Nature).
- JCR indexed: PASS (JIF displayed by publisher implies JCR listing).
- Q1: LIKELY, not verified against Clarivate directly.
- **≤ 72 days submission→final acceptance: FAIL** — verified median is 83.5 days (12 days over). No legitimate JCR-listed candidate we could verify met the rule; the only journal with median ≤72 (Energy Informatics, 68 d) shows no JIF on its page and so is not demonstrably JCR-indexed.

## Why this one
Of 30 journals whose acceptance times we computed from article-level dates (journal_comparison.md), JKSU-CIS is the fastest with a JIF, has a strong JIF (6.4), and its broad CS scope accepts CPU-feasible ML research (this machine has no GPU).

## Candidates we could not verify
Elsevier journals (Expert Systems with Applications, Knowledge-Based Systems, Results in Engineering, Egyptian Informatics Journal, Alexandria Eng. J., etc.): ScienceDirect returned HTTP 403 / bot block, and Elsevier does not deposit article history in Crossref → acceptance times UNVERIFIED → excluded. IEEE journals: not attempted in cycle 1 (Crossref has no history dates).

## Re-check with Frontiers (session 2, 2026-11-24)
Frontiers in Artificial Intelligence: IF 6.7 (homepage), median 81.5 d (n=80 sampled). It is 2 days faster than JKSU-CIS and has a slightly higher IF, and both publish NIDS work (Crossref title search 2024-11→: e.g. 10.3389/frai.2026.1895608; JKSU-CIS e.g. 10.1007/s44443-026-00688-5). Both FAIL the 72-day rule by about 10 days. **Decision D18: keep JKSU-CIS.** The speed and IF differences are within sampling noise (n=80 vs n=596). JKSU-CIS has already published a cross-domain IDS paper (QuCAD-IDS). The literature matrix is built from JKSU-CIS. Frontiers in AI stays the documented runner-up. A human should check both JCR quartiles before submission.
