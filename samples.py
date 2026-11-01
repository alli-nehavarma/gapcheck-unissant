# samples.py  --  6 fake cases with planted errors + an answer key, so we can SCORE the tool.
# Run:  python samples.py

import checker

SAMPLES = [
 {"id": "S1_clean", "facts": {},
  "narrative": "On March 14, 2025, Border Patrol agents encountered 'John Doe' near the Yuma Station area. Subject is a citizen of Mexico. Subject stated he crossed on foot without inspection and has never had any documents allowing him to remain in the United States. Subject has no prior immigration history. Subject is inadmissible under section 212(a)(6)(A)(i) of the INA, in that he entered at a place not designated by the Attorney General and was not then admitted or paroled."},
 {"id": "S2_missing_citizenship", "facts": {},
  "narrative": "On March 14, 2025, agents apprehended 'Maria Lopez' near the Nogales checkpoint. Subject stated she crossed on foot without inspection and has no documents. She has no prior immigration history. Subject is inadmissible under section 212(a)(6)(A)(i) of the INA, in that she entered without being admitted or paroled."},
 {"id": "S3_no_manner_of_entry", "facts": {},
  "narrative": "On 05/02/2025 officers encountered 'Carlos Ruiz', a citizen of Honduras, near the Laredo port of entry. Subject stated he has no passport or visa. Subject has no prior immigration history. Subject is inadmissible under section 212(a)(7)(A)(i)(I) of the INA, in that he lacked a valid entry document."},
 {"id": "S4_charge_mismatch", "facts": {},
  "narrative": "On June 3, 2025, agents encountered 'Ana Torres', a citizen of Colombia, at the El Paso airport. Subject was inspected and admitted as a B-2 visitor and presented her passport and visa. Subject stated she stayed past her authorized period. Subject is inadmissible under section 212(a)(6)(A)(i) of the INA, in that she entered without inspection."},
 {"id": "S5_prior_removal_conflict", "facts": {},
  "narrative": "On July 9, 2025, agents encountered 'Jose Perez', a citizen of Guatemala, near the McAllen station. Subject stated he crossed the river without inspection and has papers from no one. Subject has no prior immigration history. Subject is inadmissible under Section 212(A)(9)(A)(I) of the INA in that he was previously ordered removed and entered without being admitted."},
 {"id": "S6_multi_charge_incomplete", "facts": {},
  "narrative": "INADMISSIBILITY: 'John Doe' a citizen of Mexico. He has never had any documents that would allow him to be, or remain, in the United States legally. 'John Doe' is inadmissible under section 212(a) (6) (A) (i) of the INA, in that he entered the United States at a place not designated by the Attorney General and was not then admitted or paroled after inspection by an immigration officer.\nINADMISSIBILITY: Subject is inadmissible under Section 212(A) (9) (A) (I) of the Immigration and Nationality Act, as amended, in that he was previously ordered removed and entered or attempted to enter without being admitted.\nREMOVABILITY: Subject is removable under Section 212 because he was found inadmissible as an arriving alien in proceedings under section 235(b)l of the Act."},
]

# Answer key: the (type, element) problems we planted in each case, and whether a human must review it.
KEY = {
 "S1_clean":                 {"planted": [], "human": False},
 "S2_missing_citizenship":   {"planted": [("missing", "country_of_citizenship")], "human": False},
 "S3_no_manner_of_entry":    {"planted": [("missing", "manner_of_entry")], "human": False},
 "S4_charge_mismatch":       {"planted": [("citation_mismatch", "charge_citation"), ("inconsistent", "manner_of_entry")], "human": True},
 "S5_prior_removal_conflict":{"planted": [("inconsistent", "immigration_history")], "human": False},
 "S6_multi_charge_incomplete":{"planted": [("missing", "date_of_encounter"), ("missing", "place_of_encounter"), ("unclear", "charge_citation"), ("missing", "subject_statements")], "human": True},
}

if __name__ == "__main__":
    caught, missed, wrong, human_ok, human_total = 0, 0, 0, 0, 0
    for s in SAMPLES:
        result = checker.review(s["narrative"], s["facts"], use_ai=False)
        found = [(f["type"], f["element"]) for f in result["flags"]]
        planted = KEY[s["id"]]["planted"]
        for p in planted:
            if p in found:
                caught += 1
            else:
                missed += 1
                print("  MISSED in", s["id"], p)
        for f in found:
            if f not in planted:
                wrong += 1
                print("  EXTRA flag in", s["id"], f)
        if KEY[s["id"]]["human"]:
            human_total += 1
            if result["human_review"]:
                human_ok += 1
    print("Caught", caught, "of", caught + missed, "planted errors. Extra flags:", wrong)
    print("Human review sent:", human_ok, "of", human_total)
