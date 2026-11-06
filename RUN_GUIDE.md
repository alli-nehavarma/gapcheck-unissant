# How to operate the Charge Narrative Gap Review

## One-time setup (Windows)
1. Install Python 3.10+ from python.org (tick "Add Python to PATH").
2. Unzip the project folder.
3. Double-click `run_windows.bat` (first run installs the libraries, then opens the site at http://localhost:8501). Leave the black window open.
   Mac/Linux: `pip install -r requirements.txt` then `streamlit run app.py`.

## Turn on the AI (optional - the rule checks work without it)
Pick ONE:
- Paste the key into the sidebar box "AI key", then click "Test AI connection" (it can take several seconds; the hosted model is slow).
- Or copy `.env.example` to `.env`, put the key in it, restart the site.
- Or PowerShell before starting: `$env:CHALLENGEX_API_KEY="your_key"`
The key is in Unissant's email. Never put it in code or Git. Share it only inside your team.

## Using the site
- Tab 1 Review a case: pick a sample or paste a narrative, click "Review case". Mark each flag Open / Fixed / Dismissed. The Finalize gate turns green when all HIGH flags are resolved (and a human signs off on hard cases). Download the report (.html -> Ctrl+P -> PDF, .txt, or .csv).
- Tab 2 Batch test bed: run the 20 built-in cases, or upload .json / .csv / .txt narratives (button provides a ready sample_cases.json). Downloads a zip of reports and a summary CSV.
- Tab 3 Scorecard: click "Run built-in samples now" to grade against the answer key and the challenge targets (90% caught, <=10% wrong, 100% hard cases to a human, <60 s).
- Tab 4 Impact & trust: architecture, guardrails, adjustable impact estimator.
- No website needed: `python samples.py` (score) and `python test_guardrails.py` (AI guardrail test, works offline).

## 3-minute demo
1. Tab 1, load S1_clean: readiness 100, no flags.
2. Load S4_charge_mismatch: red sentence, HUMAN REVIEW banner, no charge suggested.
3. Load S2_missing_citizenship, add "a citizen of Mexico" to the narrative, Review again: the flag disappears.
4. Tab 3, "Run built-in samples now": scorecard.

## Troubleshooting
- "AI was unavailable": check the key, click Test AI connection, or just continue - rules-only results are still valid.
- Browser did not open: go to http://localhost:8501.
- "py is not recognized": reinstall Python with "Add Python to PATH", or use `python` instead of `py`.
