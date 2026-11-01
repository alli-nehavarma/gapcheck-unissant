# ai.py  --  the AI part. It sends the narrative to Unissant's model and gets a JSON answer back.
# The AI is only a helper: its answer is CLEANED before we use it (see the checks below).

import os, json
from openai import OpenAI            # Unissant's server speaks the same language as OpenAI, so we use this library

URL = "https://challengex-ext2.unissantmissionworks.com/v1"
MODEL = "gpt-oss-20b"                # exactly this name

# The rules we give the AI. "Reasoning: low" makes this model answer faster.
RULES = """Reasoning: low
You review synthetic immigration charge narratives for documentation problems.
Rules: Never write or rewrite the narrative. Never suggest or name any charge or law other than ones the officer already cited.
Only flag problems the text clearly shows. If unsure, do not flag.
Every flag needs a sentence number and a short exact quote from that sentence.
Reply with ONE JSON object and nothing else:
{"flags":[{"type":"missing|inconsistent|unclear","element":"","sentence":0,"quote":"","reason":"one plain sentence"}],
 "present":[{"element":"","quote":""}],
 "ambiguous":""}
"present" = for each element in the 'maybe missing' list that the text actually states, give a quote.
"ambiguous" = a short reason if the facts are too unclear or contradictory for a computer to judge, else an empty string."""

def reason_is_safe(reason, cited_laws, known_laws):
    # Throws away AI text that recommends a charge, or names a law the officer did NOT cite.
    r = reason.lower().replace(" ", "")
    for bad in ["shouldbecharged", "recommendcharging", "appropriatecharge", "correctchargeis"]:
        if bad in r:
            return False
    for law in known_laws:
        if law in r and law not in cited_laws:
            return False
    return True

def ask_ai(sentences, facts, cited_laws, known_laws, missing_names):
    key = os.environ.get("CHALLENGEX_API_KEY")          # the secret key lives in your computer's settings, NOT in the code
    if not key:
        raise Exception("CHALLENGEX_API_KEY is not set")
    client = OpenAI(base_url=URL, api_key=key, timeout=45, max_retries=0)   # give up after 45 seconds

    numbered = ""
    for i in range(len(sentences)):
        numbered += "[" + str(i + 1) + "] " + sentences[i] + "\n"
    question = ("NARRATIVE:\n" + numbered + "\nFORM FIELDS: " + json.dumps(facts) +
                "\nLAWS THE OFFICER CITED: " + ", ".join(cited_laws) +
                "\nMAYBE MISSING: " + ", ".join(missing_names))

    reply = client.chat.completions.create(
        model=MODEL, temperature=0, max_tokens=3000,
        messages=[{"role": "system", "content": RULES}, {"role": "user", "content": question}])
    text = reply.choices[0].message.content or ""
    data = json.loads(text[text.find("{"): text.rfind("}") + 1])   # keep only the part between { and }

    # ---- clean the answer ----
    present = []
    for p in data.get("present", []):
        quote = str(p.get("quote", "")).lower()[:40]
        if quote != "" and quote in " ".join(sentences).lower():   # the quote must really be in the narrative
            present.append(p.get("element"))

    good_flags = []
    for f in data.get("flags", []):
        num = f.get("sentence")
        reason = str(f.get("reason", ""))
        if f.get("type") not in ["missing", "inconsistent", "unclear"] or reason == "":
            continue
        if not reason_is_safe(reason, cited_laws, known_laws):
            continue
        if not isinstance(num, int) or num < 1 or num > len(sentences):
            continue                                                # must point to a REAL sentence
        quote = str(f.get("quote", "")).lower()[:40]
        if quote not in sentences[num - 1].lower():
            continue                                                # quote must really be in that sentence
        good_flags.append({"type": f["type"], "element": f.get("element", "other"), "reason": reason,
                           "sentence": num, "field": None, "quote": sentences[num - 1], "source": "ai"})

    ambiguous = str(data.get("ambiguous", ""))
    if ambiguous != "" and not reason_is_safe(ambiguous, cited_laws, known_laws):
        ambiguous = "The AI judged the facts unclear."
    return {"flags": good_flags, "present": present, "ambiguous": ambiguous}
