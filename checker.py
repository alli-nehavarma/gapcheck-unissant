# checker.py  --  the BACKEND. All the checking logic lives in this one file.
# It only uses things you already know: lists, dictionaries, loops, `in`, and functions.

import time

#*****************************************************************************************************
#   PART 1: THE CHECKLIST  (a dictionary: fact name -> list of "clue words")
#*****************************************************************************************************
# If NONE of the clue words appear in the narrative (and the form box is empty),
# we say that fact is missing.
months = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]

REQUIRED = {
    "subject_name":           ["'", "’", "‘", '"', "mr.", "ms.", "mrs."],
    "country_of_citizenship": ["citizen of", "national of", "native of", "citizen and national"],
    "date_of_encounter":      months + ["/2024", "/2025", "/2026", "-2025-", "2025-", "2026-"],
    "place_of_encounter":     ["near", "station", "port of entry", "checkpoint", "airport", "bridge", "sector", "highway"],
    "manner_of_encounter":    ["encounter", "apprehend", "arrest", "observed", "detain", "found", "located", "interdict"],
    "manner_of_entry":        ["entered", "crossed", "arrived", "presented", "admitted", "without inspection", "not designated"],
    "subject_statements":     ["stated", "claimed", "said", "advised", "interview", "declined", "told", "admits"],
    "immigration_history":    ["prior", "previous", "never", "removed", "deported", "visa", "history"],
    "documents":              ["document", "passport", "visa", "card", "permit", "papers"],
}

#*****************************************************************************************************
#   PART 2: THE LAW CHEAT SHEET  (a dictionary: law -> info about it)
#*****************************************************************************************************
# Laws are written in lowercase with no spaces so we can match messy typing like "212(A) (9) (A) (I)".
# "supports"    = words that FIT this law.   "contradicts" = words that go AGAINST this law.
# "needs"       = facts from the checklist that must be present for this law to make sense.
# Unissant will give you the real reference sheet: add/replace entries here.
CHARGES = {
    "212(a)(6)(a)(i)": {
        "meaning": "Entered the U.S. without being admitted or paroled (entry without inspection).",
        "supports": ["without inspection", "not designated", "ewi", "illegally entered", "not then admitted"],
        "contradicts": ["was admitted", "inspected and admitted", "lawfully admitted", "overstay"],
        "needs": ["manner_of_entry"]},
    "212(a)(6)(c)(i)": {
        "meaning": "Fraud or willful misrepresentation of a material fact.",
        "supports": ["misrepresent", "fraud", "false", "counterfeit", "altered", "impersonat"],
        "contradicts": [],
        "needs": ["documents"]},
    "212(a)(7)(a)(i)(i)": {
        "meaning": "Immigrant without a valid, unexpired entry document or visa.",
        "supports": ["no passport", "no visa", "no valid", "no document", "never had any documents", "lacked", "not in possession"],
        "contradicts": [],
        "needs": ["documents"]},
    "212(a)(9)(a)": {
        "meaning": "Previously removed or deported, then entered or tried to enter again.",
        "supports": ["ordered removed", "previously removed", "removed from", "deported", "removal order"],
        "contradicts": ["no prior removal", "never been removed", "never removed"],
        "needs": ["immigration_history"]},
    "212(a)(9)(b)(i)": {
        "meaning": "Left the U.S. after a period of unlawful presence (3- or 10-year bar).",
        "supports": ["unlawful presence", "unlawfully present", "overstay", "departed"],
        "contradicts": [],
        "needs": ["manner_of_entry"]},
    "212(a)(2)(a)(i)(i)": {
        "meaning": "Convicted of, or admits, a crime involving moral turpitude.",
        "supports": ["convict", "crime", "offense", "charged with", "sentenced"],
        "contradicts": ["no criminal record", "no criminal history"],
        "needs": []},
    "237(a)(1)(b)": {
        "meaning": "Was admitted to the U.S. but is now here in violation of the law.",
        "supports": ["admitted", "overstay", "visa", "status"],
        "contradicts": ["without inspection", "not designated", "ewi"],
        "needs": ["manner_of_entry"]},
    "235(b)(1)": {
        "meaning": "Expedited removal of an arriving alien found inadmissible.",
        "supports": ["arriving", "port of entry", "expedited", "airport"],
        "contradicts": [],
        "needs": ["place_of_encounter"]},
}

#*****************************************************************************************************
#   PART 3: PAIRS OF CLUES THAT CONTRADICT EACH OTHER
#*****************************************************************************************************
# If one sentence has a clue from list A and a different sentence has a clue from list B, we flag it.
CONFLICTS = [
    {"element": "manner_of_entry",
     "a": ["without inspection", "not designated", "ewi"],
     "b": ["was admitted", "inspected and admitted", "lawfully admitted", "presented herself at", "presented himself at"],
     "reason": "One sentence says the subject entered without inspection, but another says the subject was inspected or admitted."},
    {"element": "documents",
     "a": ["never had any documents", "no documents", "no valid documents"],
     "b": ["presented a passport", "presented her passport", "presented his passport", "presented a visa", "presented her visa", "presented his visa"],
     "reason": "One sentence says the subject had no documents, but another says a document was presented."},
    {"element": "immigration_history",
     "a": ["no prior immigration", "no prior history", "no prior removal", "never been removed", "never been deported"],
     "b": ["previously ordered removed", "previously removed", "was deported", "ordered removed"],
     "reason": "One sentence says there is no prior history/removal, but another describes a prior removal."},
]

#*****************************************************************************************************
#   PART 4: SMALL HELPER FUNCTIONS
#*****************************************************************************************************
def split_into_sentences(text):
    # Turn line breaks into ". " then cut at every ". " so we get a list of sentences.
    text = text.replace("\n", ". ")
    pieces = text.split(". ")
    sentences = []
    for p in pieces:
        p = p.strip()
        if p != "":
            sentences.append(p)
    return sentences

def has_any(text, words):
    # True if ANY word from the list appears in the text.
    text = text.lower()
    for w in words:
        if w in text:
            return True
    return False

def find_sentence(sentences, words):
    # Returns the number (1, 2, 3...) of the first sentence containing any of the words, or None.
    for i in range(len(sentences)):
        if has_any(sentences[i], words):
            return i + 1
    return None

def make_flag(kind, element, reason, sentences, number=None, field=None, source="rules"):
    # One problem = one dictionary. "number" says which sentence it came from.
    quote = ""
    if number is not None:
        quote = sentences[number - 1]
    return {"type": kind, "element": element, "reason": reason,
            "sentence": number, "field": field, "quote": quote, "source": source}

def find_laws(text):
    # Looks for laws from the cheat sheet inside the text.
    # Returns: laws found (list) and incomplete citations such as "Section 212" with nothing after it (list).
    squashed = text.lower().replace(" ", "")          # remove spaces so messy typing still matches
    squashed = squashed.replace("1182(", "212(").replace("1227(", "237(").replace("1225(", "235(")  # 8 U.S.C. numbers -> INA numbers
    laws = []
    for law in CHARGES:
        if law in squashed:
            laws.append(law)
    incomplete = []
    for num in ["212", "237", "235"]:
        word = "section" + num
        start = 0
        while True:
            i = squashed.find(word, start)
            if i == -1:
                break
            after = squashed[i + len(word): i + len(word) + 1]   # the character right after "section212"
            if after != "(":
                incomplete.append("Section " + num)
            start = i + 1
    return laws, incomplete

#*****************************************************************************************************
#   PART 5: THE THREE CHECKS
#*****************************************************************************************************
def check_missing(narrative, facts, sentences):
    # CHECK 1: is each required fact in the narrative or in the form box?
    flags = []
    for name in REQUIRED:
        filled_in_form = facts.get(name, "").strip() != ""
        found_in_text = has_any(narrative, REQUIRED[name])
        if not filled_in_form and not found_in_text:
            reason = name.replace("_", " ").capitalize() + " is not stated in the narrative."
            flags.append(make_flag("missing", name, reason, sentences))
    return flags

def check_conflicts(sentences):
    # CHECK 2: do two sentences contradict each other?
    flags = []
    for c in CONFLICTS:
        a = find_sentence(sentences, c["a"])
        b = find_sentence(sentences, c["b"])
        if a is not None and b is not None and a != b:
            reason = c["reason"] + " (Compare sentence " + str(a) + " and sentence " + str(b) + ".)"
            flags.append(make_flag("inconsistent", c["element"], reason, sentences, number=b))
    return flags

def check_charges(laws, incomplete, sentences, all_text, facts):
    # CHECK 3: does each cited law fit the facts?  (NEVER suggests a different law.)
    flags, citations, reasons = [], [], []

    for sec in incomplete:
        msg = "'" + sec + "' is incomplete. INA charges need the full subsection."
        num = find_sentence(sentences, [sec.lower()])
        flags.append(make_flag("unclear", "charge_citation", msg, sentences, number=num))
        citations.append({"law": sec, "status": "incomplete", "meaning": "Subsection missing."})
        reasons.append("A charge citation is incomplete ('" + sec + "').")

    if len(laws) == 0 and len(incomplete) == 0:
        flags.append(make_flag("citation_mismatch", "charge_citation",
                     "No charge citation from the reference sheet was found.", sentences, field="selected_charge"))
        reasons.append("No readable charge citation, so the charge cannot be checked.")

    if len(laws) > 1:
        reasons.append(str(len(laws)) + " different charges are cited (multi-charge case).")

    for law in laws:
        info = CHARGES[law]
        status = "ok"
        # a) any words that go AGAINST this law?
        num = find_sentence(sentences, info["contradicts"])
        if num is not None:
            msg = law + " means: " + info["meaning"] + " Other facts in the record point the other way."
            flags.append(make_flag("citation_mismatch", "charge_citation", msg, sentences, number=num))
            status = "likely mismatch"
        # b) any words that FIT this law?
        if not has_any(all_text, info["supports"]):
            msg = law + " means: " + info["meaning"] + " The narrative does not state facts that match this."
            flags.append(make_flag("citation_mismatch", "charge_citation", msg, sentences))
            status = "likely mismatch"
        # c) is every fact this law needs present?
        for need in info["needs"]:
            if not has_any(all_text, REQUIRED[need]) and facts.get(need, "").strip() == "":
                msg = law + " needs '" + need.replace("_", " ") + "' but it is not stated."
                flags.append(make_flag("citation_mismatch", "charge_citation", msg, sentences))
                status = "likely mismatch"
        citations.append({"law": law, "status": status, "meaning": info["meaning"]})
    return flags, citations, reasons

#*****************************************************************************************************
#   PART 6: THE MAIN FUNCTION  (runs everything and returns one result dictionary)
#*****************************************************************************************************
def review(narrative, facts=None, use_ai=False):
    start_time = time.time()
    if facts is None:
        facts = {}
    sentences = split_into_sentences(narrative)

    # the officer's "selected charge" box counts as part of the text we search for laws
    all_text = narrative + " " + " ".join(str(v) for v in facts.values())
    laws, incomplete = find_laws(all_text)

    flags = check_missing(narrative, facts, sentences)
    flags += check_conflicts(sentences)
    charge_flags, citations, reasons = check_charges(laws, incomplete, sentences, all_text, facts)
    flags += charge_flags

    # contradicting entry facts mean the case is ambiguous, so a human must look
    for f in flags:
        if f["type"] == "inconsistent" and f["element"] == "manner_of_entry":
            reasons.append("Facts about how the subject entered conflict, so the case is ambiguous.")

    # OPTIONAL: ask the AI to double-check (if it fails, we just keep the rules-only result)
    ai_used, ai_error = False, ""
    if use_ai:
        try:
            import ai                                   # our AI file
            missing_names = [f["element"] for f in flags if f["type"] == "missing"]
            answer = ai.ask_ai(sentences, facts, laws, list(CHARGES.keys()), missing_names)
            # the AI found facts we thought were missing -> remove those false alarms
            flags = [f for f in flags if not (f["type"] == "missing" and f["element"] in answer["present"])]
            flags += answer["flags"]                    # extra problems the AI found (already checked)
            if answer["ambiguous"] != "":
                reasons.append(answer["ambiguous"])
            ai_used = True
        except Exception as e:
            ai_error = str(e)[:200]

    reasons = list(dict.fromkeys(reasons))              # remove duplicate reasons
    return {"flags": flags, "citations": citations, "sentences": sentences,
            "human_review": len(reasons) > 0, "reasons": reasons,
            "ai_used": ai_used, "ai_error": ai_error,
            "seconds": round(time.time() - start_time, 2)}

def make_report(result, case_name="case"):
    # Turns the result dictionary into a readable one-page text report.
    lines = ["GAP REPORT: " + case_name, ""]
    if result["human_review"]:
        lines.append("*** HUMAN REVIEW REQUIRED (this tool never picks or suggests a charge) ***")
        for r in result["reasons"]:
            lines.append("  - " + r)
        lines.append("")
    lines.append("1. GAPS")
    gaps = [f for f in result["flags"] if f["element"] != "charge_citation"]
    if len(gaps) == 0:
        lines.append("  None found.")
    for f in gaps:
        where = "Sentence " + str(f["sentence"]) if f["sentence"] else (f["field"] or "whole narrative")
        lines.append("  - [" + f["type"] + "] " + f["element"] + " (" + where + "): " + f["reason"])
    lines.append("")
    lines.append("2. CITATION CHECK")
    for c in result["citations"]:
        lines.append("  - " + c["law"] + ": " + c["status"] + ". " + c["meaning"])
    for f in result["flags"]:
        if f["element"] == "charge_citation":
            where = "Sentence " + str(f["sentence"]) if f["sentence"] else (f["field"] or "whole narrative")
            lines.append("  - FLAG (" + where + "): " + f["reason"])
    lines.append("")
    lines.append("Review time: " + str(result["seconds"]) + "s. AI check used: " + str(result["ai_used"]))
    return "\n".join(lines)
