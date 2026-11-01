# app.py  --  the FRONT END (the website). Streamlit turns each st.something line into something on the page.
# Run it with:  streamlit run app.py

import streamlit as st
import checker
from samples import SAMPLES

st.title("Charge Narrative Gap Review")
st.caption("Flags problems only. It never writes the narrative and never picks or suggests a charge. Synthetic data only.")

# --- INPUTS ---
names = ["(none)"] + [s["id"] for s in SAMPLES]
choice = st.selectbox("Load a sample case", names)
start_text = ""
for s in SAMPLES:
    if s["id"] == choice:
        start_text = s["narrative"]

narrative = st.text_area("Officer narrative", value=start_text, height=250, key="narrative_" + choice)

facts = {}
with st.expander("Case facts (optional)"):
    for name in checker.REQUIRED:
        facts[name] = st.text_input(name.replace("_", " ").capitalize(), key=name)
    facts["selected_charge"] = st.text_input("Officer-selected charge", key="selected_charge")

use_ai = st.checkbox("Use AI double-check", value=True)

# --- RUN ---
if st.button("Review") and narrative.strip() != "":
    result = checker.review(narrative, facts, use_ai)

    if result["human_review"]:
        st.error("HUMAN REVIEW REQUIRED: " + " | ".join(result["reasons"]))
    if result["ai_error"] != "":
        st.warning("AI was unavailable, so only the rule checks ran: " + result["ai_error"])

    st.subheader("Gaps and flags")
    rows = []
    for f in result["flags"]:
        where = "Sentence " + str(f["sentence"]) if f["sentence"] else (f["field"] or "whole narrative")
        rows.append({"type": f["type"], "element": f["element"], "where": where, "reason": f["reason"]})
    if len(rows) == 0:
        st.write("No gaps found.")
    else:
        st.table(rows)

    st.subheader("Citation check")
    st.table(result["citations"])
    st.download_button("Download report", checker.make_report(result), "gap_report.txt")
    st.caption("Took " + str(result["seconds"]) + " seconds")
