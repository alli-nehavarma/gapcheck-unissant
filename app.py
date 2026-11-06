# app.py  --  the FRONT END (the website). Streamlit turns each st.something line into something on the page.
# Run it with:  py -m streamlit run app.py     (or double-click run_windows.bat)
# 4 tabs:  1) Review a case   2) Batch test bed   3) Scorecard   4) Impact & trust

import os, io, csv, json, zipfile, html, time
import streamlit as st
import pandas as pd
import checker
from samples import SAMPLES, KEY

st.set_page_config(page_title="Charge Narrative Gap Review", page_icon="🛡️", layout="wide")

# Optional: read CHALLENGEX_API_KEY from a local .env file (it is git-ignored, so it never reaches GitHub).
if os.path.exists(".env") and not os.environ.get("CHALLENGEX_API_KEY"):
    for line in open(".env", encoding="utf-8", errors="ignore"):
        if line.strip().startswith("CHALLENGEX_API_KEY") and "=" in line:
            os.environ["CHALLENGEX_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")

#*****************************************************************************************************
#   LOOK AND FEEL
#*****************************************************************************************************
st.markdown("""
<style>
.banner {background: linear-gradient(100deg,#0b2a5b,#1d5fd1 60%,#7c3aed); padding: 26px 30px; border-radius: 16px; color: white; margin-bottom: 16px;}
.banner h1 {color: white; margin: 0; font-size: 34px;}
.banner p {margin: 6px 0 0 0; color: #e3ecff; font-size: 16px;}
.pill {display:inline-block; background: rgba(255,255,255,0.18); padding: 3px 12px; border-radius: 14px; margin: 10px 6px 0 0; font-size: 13px;}
.badge {padding: 2px 9px; border-radius: 10px; font-size: 12px; font-weight: 700; color: white; margin-right: 6px;}
.high {background:#d64545;} .medium {background:#e0a100;} .low {background:#3b82f6;} .aib {background:#7c3aed;}
.chip {display:inline-block; padding:3px 10px; margin:2px 4px 2px 0; border-radius:12px; background:#fff0f0; color:#8a1f1f; border:1px solid #f0b4b4; font-size:13px;}
.sent {color:#111; padding:2px 4px; border-radius:4px; line-height:2.1;}
.gauge {width:124px; height:124px; border-radius:50%; display:flex; align-items:center; justify-content:center;}
.gauge-in {width:92px; height:92px; border-radius:50%; background:white; color:#111; display:flex; flex-direction:column; align-items:center; justify-content:center;}
.gauge-in b {font-size:30px; line-height:1;} .gauge-in span {font-size:11px; color:#555;}
</style>
<div class="banner"><h1>🛡️ Charge Narrative Gap Review</h1>
<p>Catch missing facts, contradictions and wrong citations <b>before</b> the record is final. The officer stays in charge: this tool never writes the narrative and never picks or suggests a charge.</p>
<span class="pill">Every flag points to a sentence</span><span class="pill">Hard cases go to a human</span><span class="pill">AI can't override the guardrails</span><span class="pill">Works even if the AI is down</span></div>
""", unsafe_allow_html=True)

#*****************************************************************************************************
#   SIDEBAR
#*****************************************************************************************************
st.sidebar.header("Settings")
use_ai = st.sidebar.checkbox("Use AI double-check", value=True)
animate = st.sidebar.checkbox("Animated scan", value=True)
typed_key = st.sidebar.text_input("AI key (kept in memory only, never saved)", type="password")
if typed_key.strip() != "":
    os.environ["CHALLENGEX_API_KEY"] = typed_key.strip()
if os.environ.get("CHALLENGEX_API_KEY"):
    st.sidebar.success("AI key found")
    if st.sidebar.button("Test AI connection"):
        import ai
        with st.sidebar:
            with st.spinner("Calling the model (can take several seconds)..."):
                ok, msg = ai.ping()
        (st.sidebar.success if ok else st.sidebar.error)(msg)
else:
    st.sidebar.warning("No AI key set. Only rule checks will run.")
st.sidebar.header("How it works")
st.sidebar.markdown("""
1. **Rules** check for missing facts, contradictions, and whether the cited law fits the facts.
2. **AI** double-checks and removes false alarms.
3. **Guardrails** delete anything unsafe from the AI.
4. **Unclear or multi-charge** cases go to a human.
""")

#*****************************************************************************************************
#   HELPER FUNCTIONS FOR THE PAGE
#*****************************************************************************************************
def badge(text, css):
    return '<span class="badge ' + css + '">' + html.escape(text) + '</span>'

def where_text(f):
    if f["sentence"]:
        return "Sentence " + str(f["sentence"])
    if f["field"]:
        return "Field: " + f["field"]
    return "Whole narrative"

def narrative_html(result, upto=None):
    # Builds the narrative with each flagged sentence colored. "upto" lets the animation reveal it sentence by sentence.
    n = len(result["sentences"]) if upto is None else upto
    out = ""
    for i in range(n):
        number = i + 1
        reasons, color = [], ""
        for f in result["flags"]:
            if f["sentence"] == number:
                reasons.append(f["reason"])
                if f["type"] in ["inconsistent", "citation_mismatch"]:
                    color = "#ffc9c9"                      # red = contradiction or citation problem
                elif color == "":
                    color = "#fff3bf"                      # yellow = unclear
        text = html.escape(result["sentences"][i])
        tip = html.escape(" | ".join(reasons), quote=True)
        label = "<sup>[" + str(number) + "]</sup> "
        if color != "":
            out += '<span class="sent" style="background:' + color + ';" title="' + tip + '">' + label + text + '.</span> '
        else:
            out += '<span class="sent">' + label + text + '.</span> '
    return out

def gauge_html(score):
    color = "#16a34a" if score >= 80 else ("#e0a100" if score >= 50 else "#d64545")
    return ('<div class="gauge" style="background: conic-gradient(' + color + ' 0 ' + str(score) + '%, #e5e7eb ' + str(score) + '% 100%);">'
            '<div class="gauge-in"><b>' + str(score) + '</b><span>READINESS</span></div></div>')

def flags_to_csv(flags):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["severity", "type", "element", "where", "reason", "question for officer", "source"])
    for f in flags:
        w.writerow([f["severity"], f["type"], f["element"], where_text(f), f["reason"], f["ask"], f["source"]])
    return buf.getvalue()

def show_result(result, case_name, key_prefix, do_animation=False):
    flags = result["flags"]
    run_id = str(st.session_state.get("run_id", 0))

    # ---- top row: gauge + numbers ----
    g, c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1, 1])
    g.markdown(gauge_html(result["readiness"]), unsafe_allow_html=True)
    c1.metric("Completeness", str(result["completeness"]) + "%")
    prev_key = "prev_" + key_prefix
    delta = None
    if prev_key in st.session_state:
        delta = len(flags) - st.session_state[prev_key]
    c2.metric("Flags found", len(flags), delta=delta, delta_color="inverse")
    c3.metric("Human review", "YES" if result["human_review"] else "No")
    c4.metric("Review time", str(result["seconds"]) + " s", "AI used" if result["ai_used"] else "rules only", delta_color="off")
    st.session_state[prev_key] = len(flags)

    if result["human_review"]:
        st.error("HUMAN REVIEW REQUIRED. " + " | ".join(result["reasons"]) + "  (The tool does not pick or suggest a charge.)")
    if result["ai_error"] != "":
        st.warning("AI was unavailable, so only the rule checks ran: " + result["ai_error"])

    # ---- narrative on the left, flags on the right ----
    left, right = st.columns([3, 2])
    with left:
        st.subheader("Narrative with flags")
        box = st.empty()
        if do_animation:
            total = len(result["sentences"])
            for i in range(1, total + 1):
                box.markdown(narrative_html(result, i) + "<p>🔍 Scanning sentence " + str(i) + " of " + str(total) + "...</p>", unsafe_allow_html=True)
                time.sleep(min(0.6, 3.0 / total))
        box.markdown(narrative_html(result), unsafe_allow_html=True)
        st.caption("Red = contradiction or citation problem. Yellow = unclear. Hover a colored sentence to see why.")
        missing = [f for f in flags if f["type"] == "missing" and f["element"] in checker.REQUIRED]
        if len(missing) > 0:
            st.markdown("**Missing facts:** " + "".join('<span class="chip">' + html.escape(f["element"].replace("_", " ")) + '</span>' for f in missing),
                        unsafe_allow_html=True)
        st.subheader("Citation check")
        if len(result["citations"]) == 0:
            st.write("No citation found.")
        else:
            st.table(result["citations"])

    states = []                                            # (flag, status) so we can build the finalize gate below
    with right:
        st.subheader("Flags (" + str(len(flags)) + ")")
        if any(f.get("advisory") for f in flags):
            st.caption("LOW 'advisory' notes come from Unissant's disposition / procedural-record element. They do not lower readiness or block finalizing.")
        if len(flags) == 0:
            st.success("No gaps found.")
        order = {"high": 0, "medium": 1, "low": 2}
        sorted_flags = sorted(flags, key=lambda x: order.get(x.get("severity", "medium"), 1))
        for i in range(len(sorted_flags)):
            f = sorted_flags[i]
            with st.container(border=True):
                sev = f.get("severity", "medium")
                line = badge(sev.upper(), sev) + badge(f["type"], "low")
                if f["source"] == "ai":
                    line += badge("AI", "aib")
                st.markdown(line + " **" + f["element"].replace("_", " ") + "** (" + where_text(f) + ")", unsafe_allow_html=True)
                st.write(f["reason"])
                if f.get("ask"):
                    st.info("Ask the officer: " + f["ask"])
                status = st.radio("Officer decision", ["Open", "Fixed", "Dismissed"], horizontal=True,
                                  key="st_" + run_id + "_" + key_prefix + "_" + str(i))
                states.append((f, status))

    # ---- the FINALIZE GATE: shows the officer stays in control ----
    st.divider()
    st.subheader("Finalize gate")
    open_high = len([1 for f, s in states if s == "Open" and f["severity"] == "high"])
    open_other = len([1 for f, s in states if s == "Open" and f["severity"] != "high"])
    resolved = len([1 for f, s in states if s != "Open"])
    if len(states) > 0:
        st.progress(resolved / len(states))
        st.caption(str(resolved) + " of " + str(len(states)) + " flags resolved by the officer")
    signed = True
    if result["human_review"]:
        signed = st.checkbox("A human reviewer has looked at this case and signs off", key="sign_" + run_id + "_" + key_prefix)
    if open_high == 0 and signed:
        st.success("✅ READY TO FINALIZE. All high-priority flags are resolved" + (" and a human signed off." if result["human_review"] else "."))
        if open_other > 0:
            st.caption(str(open_other) + " lower-priority flag(s) still open.")
    else:
        why = []
        if open_high > 0:
            why.append(str(open_high) + " high-priority flag(s) still open")
        if not signed:
            why.append("human sign-off needed")
        st.error("⛔ NOT READY: " + ", ".join(why) + ". The tool only flags; the officer decides.")

    # ---- trust panel ----
    t1, t2, t3 = st.columns(3)
    t1.metric("Charges suggested by the tool", 0)
    t2.metric("AI suggestions blocked by guardrails", result["ai_blocked"])
    t3.metric("Flags tied to a sentence or field", str(len([f for f in flags if f["sentence"] or f["field"] or f["type"] == "missing"])) + " of " + str(len(flags)))

    d1, d2, d3 = st.columns(3)
    d1.download_button("Report (.html, print to PDF)", checker.make_html_report(result, case_name), case_name + "_report.html", key="html_" + key_prefix)
    d2.download_button("Report (.txt)", checker.make_report(result, case_name), case_name + "_report.txt", key="rep_" + key_prefix)
    d3.download_button("Flags (.csv)", flags_to_csv(flags), case_name + "_flags.csv", key="csv_" + key_prefix)

def load_cases(files):
    cases = []
    for up in files:
        name = up.name
        raw = up.read().decode("utf-8", errors="ignore")
        if name.endswith(".json"):
            data = json.loads(raw)
            if isinstance(data, dict):
                data = [data]
            for d in data:
                cases.append({"id": d.get("id", name), "narrative": d["narrative"], "facts": d.get("facts") or d.get("case_facts") or {}})
        elif name.endswith(".csv"):
            for row in csv.DictReader(io.StringIO(raw)):
                cases.append({"id": row.get("id", "row" + str(len(cases) + 1)), "narrative": row["narrative"], "facts": {}})
        else:
            cases.append({"id": name.rsplit(".", 1)[0], "narrative": raw, "facts": {}})
    return cases

def pass_fail(ok):
    return "✅ meets target" if ok else "❌ below target"

#*****************************************************************************************************
#   THE FOUR TABS
#*****************************************************************************************************
tab1, tab2, tab3, tab4 = st.tabs(["1. Review a case", "2. Batch test bed", "3. Scorecard", "4. Impact & trust"])

# ---------------------------------------- TAB 1 ----------------------------------------
with tab1:
    names = ["(none)"] + [s["id"] for s in SAMPLES]
    choice = st.selectbox("Load a sample case (or paste your own below)", names)
    start_text = ""
    for s in SAMPLES:
        if s["id"] == choice:
            start_text = s["narrative"]
    narrative = st.text_area("Officer narrative. Edit it and review again to watch the flags disappear.", value=start_text, height=200, key="narrative_" + choice)

    facts = {}
    with st.expander("Case facts (optional). A filled box counts as present."):
        for name in checker.REQUIRED:
            facts[name] = st.text_input(name.replace("_", " ").capitalize(), key="fact_" + name)
        facts["selected_charge"] = st.text_input("Officer-selected charge", key="selected_charge")

    if st.button("Review case", type="primary") and narrative.strip() != "":
        with st.spinner("Reviewing..."):
            st.session_state["run_id"] = st.session_state.get("run_id", 0) + 1
            st.session_state["one_result"] = checker.review(narrative, facts, use_ai)
            st.session_state["one_name"] = choice if choice != "(none)" else "case"
            st.session_state["one_animate"] = animate
    if "one_result" in st.session_state:
        do_anim = st.session_state.pop("one_animate", False)
        show_result(st.session_state["one_result"], st.session_state["one_name"], "one", do_anim)

# ---------------------------------------- TAB 2 ----------------------------------------
with tab2:
    st.write("Run many narratives at once, like the Unissant test bed of 25 to 50 cases. The built-in set has 20 synthetic cases.")
    source = st.radio("Where are the narratives?", ["Built-in sample cases", "Upload files (.json, .csv, or .txt)"], horizontal=True)
    cases = []
    if source == "Built-in sample cases":
        cases = SAMPLES
    else:
        uploads = st.file_uploader("Upload one JSON/CSV file, or several .txt files", accept_multiple_files=True, type=["json", "csv", "txt"])
        if uploads:
            cases = load_cases(uploads)
            st.write(str(len(cases)) + " cases loaded.")

    st.download_button("Download the 20 sample cases as an upload file (.json)", json.dumps([{"id": s["id"], "narrative": s["narrative"]} for s in SAMPLES], indent=1),
                       "sample_cases.json", key="dl_samples")
    if st.button("Run batch", type="primary") and len(cases) > 0:
        results = {}
        bar = st.progress(0.0)
        for i in range(len(cases)):
            c = cases[i]
            results[c["id"]] = checker.review(c["narrative"], c.get("facts") or {}, use_ai)
            bar.progress((i + 1) / len(cases))
        st.session_state["batch_results"] = results
        st.session_state["run_id"] = st.session_state.get("run_id", 0) + 1

    if "batch_results" in st.session_state:
        results = st.session_state["batch_results"]
        total_flags = sum(len(r["flags"]) for r in results.values())
        human = [cid for cid in results if results[cid]["human_review"]]
        avg_time = sum(r["seconds"] for r in results.values()) / len(results)
        avg_ready = round(sum(r["readiness"] for r in results.values()) / len(results))
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Cases reviewed", len(results))
        m2.metric("Total flags", total_flags)
        m3.metric("Sent to human review", len(human))
        m4.metric("Average time", str(round(avg_time, 2)) + " s")
        m5.metric("Average readiness", avg_ready)

        # chart: which facts do officers miss most?
        counts = {}
        for r in results.values():
            for f in r["flags"]:
                counts[f["element"]] = counts.get(f["element"], 0) + 1
        if len(counts) > 0:
            st.subheader("Where do narratives fail most?")
            st.bar_chart(pd.DataFrame({"flags": list(counts.values())}, index=list(counts.keys())))

        rows = []
        for cid in results:
            r = results[cid]
            rows.append({"case": cid, "readiness": r["readiness"], "flags": len(r["flags"]),
                         "human review": "YES" if r["human_review"] else "", "seconds": r["seconds"],
                         "top issues": ", ".join(sorted(set(f["element"] for f in r["flags"])))})
        st.dataframe(rows, width="stretch")

        st.subheader("Human review queue")
        if len(human) == 0:
            st.write("Nothing needs human review.")
        for cid in human:
            st.warning(cid + ": " + " | ".join(results[cid]["reasons"]))

        zbuf = io.BytesIO()
        with zipfile.ZipFile(zbuf, "w") as z:
            for cid in results:
                z.writestr(cid + "_report.html", checker.make_html_report(results[cid], cid))
        st.download_button("Download all reports (.zip of HTML pages)", zbuf.getvalue(), "gap_reports.zip", key="zip_all")
        sbuf = io.StringIO()
        w = csv.DictWriter(sbuf, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
        st.download_button("Download summary (.csv)", sbuf.getvalue(), "batch_summary.csv", key="sum_all")

        st.subheader("Look at one case")
        pick = st.selectbox("Case", list(results.keys()), key="batch_pick")
        show_result(results[pick], pick, "batch")

# ---------------------------------------- TAB 3 ----------------------------------------
with tab3:
    st.write("Grades the batch results against an answer key, using the challenge targets.")
    key_source = st.radio("Answer key", ["Built-in sample key", "Upload key (.json)"], horizontal=True)
    key = None
    if key_source == "Built-in sample key":
        key = {k: {"planted": [list(p) for p in v["planted"]], "human": v["human"]} for k, v in KEY.items()}
    else:
        st.caption('Format: {"case_id": {"planted": [["missing", "country_of_citizenship"]], "human": false}}')
        up = st.file_uploader("Answer key JSON", type=["json"], key="keyfile")
        if up:
            key = json.loads(up.read().decode("utf-8"))

    if st.button("Run built-in samples now (fills the batch)"):
        st.session_state["batch_results"] = {s["id"]: checker.review(s["narrative"], s["facts"], use_ai) for s in SAMPLES}

    if key is not None and "batch_results" in st.session_state:
        sc = checker.score(st.session_state["batch_results"], key)
        a, b, c, d = st.columns(4)
        a.metric("Planted errors caught", str(round(sc["recall"] * 100)) + "%")
        a.caption("Target: 90% or more. " + pass_fail(sc["recall"] >= 0.9))
        b.metric("Wrong flags", str(round(sc["false_rate"] * 100)) + "%")
        b.caption("Target: 10% or less. " + pass_fail(sc["false_rate"] <= 0.1))
        c.metric("Hard cases sent to a human", str(round(sc["human_recall"] * 100)) + "%")
        c.caption("Target: 100%. " + pass_fail(sc["human_recall"] >= 1.0))
        slowest = max(r["seconds"] for r in st.session_state["batch_results"].values())
        d.metric("Slowest review", str(slowest) + " s")
        d.caption("Target: under 60 s. " + pass_fail(slowest < 60))
        st.dataframe(sc["rows"], width="stretch")
        st.caption("Advisory notes (disposition / procedural record) are not counted as wrong flags. Caught " + str(sc["caught"]) + ", missed " + str(sc["missed"]) + ", extra flags " + str(sc["extra"]) + ".")
    else:
        st.info("Run a batch in tab 2 (or click the button above), then your score appears here.")

# ---------------------------------------- TAB 4 ----------------------------------------
with tab4:
    st.subheader("How the pieces fit")
    dot = '''digraph G { rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#e8f0ff", fontname="Arial"];
      N [label="Officer narrative\\n+ case facts"]; R [label="Rule checks\\nmissing / conflicts / citation"];
      A [label="AI double-check\\n(Unissant gpt-oss-20b)"]; G [label="Guardrails\\nblock unsafe AI output", fillcolor="#ffe3e3"];
      F [label="Flags tied to\\nsentences + report"]; H [label="Human review\\nfor hard cases", fillcolor="#e3ffe8"]; O [label="Officer decides\\nand finalizes", fillcolor="#e3ffe8"];
      N -> R -> A -> G -> F -> H -> O; }'''
    try:
        st.graphviz_chart(dot)
    except Exception:
        st.write("Narrative + facts -> Rule checks -> AI double-check -> Guardrails -> Flags + report -> Human review -> Officer decides")

    st.subheader("Our guardrails")
    st.table([
        {"Rule from the challenge": "Never write the narrative", "How we enforce it": "The tool only flags and asks questions. It has no code that writes narrative text."},
        {"Rule from the challenge": "Never pick or suggest a charge", "How we enforce it": "The AI is told not to, and code deletes any AI text that recommends a charge or names a law the officer did not cite."},
        {"Rule from the challenge": "Send ambiguous or multi-charge cases to a human", "How we enforce it": "Two or more different charges, an incomplete citation, or conflicting facts always turn on human review."},
        {"Rule from the challenge": "Point every flag to a sentence or field", "How we enforce it": "AI flags that do not point to a real sentence with a real quote are deleted."},
        {"Rule from the challenge": "Under 60 seconds", "How we enforce it": "The AI call times out at 45 seconds. The rule checks still return."},
    ])

    st.subheader("Impact estimator (illustrative: change the assumptions)")
    st.caption("These numbers are examples to show the idea, not measured results.")
    e1, e2 = st.columns(2)
    per_day = e1.slider("Narratives written per day (one station)", 20, 1000, 200, 10)
    pct_bad = e1.slider("% that later need rework because of a gap", 1, 50, 15)
    late = e2.slider("Minutes to fix a gap found AFTER the record is final", 5, 60, 20)
    early = e2.slider("Minutes to fix a gap found BEFORE it is final", 1, 20, 5)
    recall_pct = e2.slider("% of gaps our tool catches", 50, 100, 90)
    saved_min_day = per_day * (pct_bad / 100) * (recall_pct / 100) * (late - early)
    k1, k2, k3 = st.columns(3)
    k1.metric("Gaps caught per day", round(per_day * pct_bad / 100 * recall_pct / 100))
    k2.metric("Rework time saved per day", str(round(saved_min_day / 60, 1)) + " hours")
    k3.metric("Per month (22 working days)", str(round(saved_min_day * 22 / 60)) + " hours")
