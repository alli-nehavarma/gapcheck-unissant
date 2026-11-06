# samples.py  --  20 fake cases with planted errors + an answer key, so we can SCORE the tool.
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
 {"id": "S7_clean_overstay", "facts": {},
  "narrative": "On August 21, 2025, ICE officers encountered 'Priya Nair', a citizen of India, near the Chicago field office. Subject stated she was admitted as an F-1 student and later stopped attending school. Subject presented her passport and visa. Subject has a prior visa history with no violations. Subject is removable under section 237(a)(1)(B) of the INA, in that she was admitted and remained in the United States in violation of her status."},
 {"id": "S8_fraud_missing_date", "facts": {},
  "narrative": "Officers encountered 'Luis Mora', a citizen of Ecuador, at the San Ysidro port of entry. Subject presented a counterfeit passport and stated that it was his own. Subject has no prior immigration history. Subject is inadmissible under section 212(a)(6)(C)(i) of the INA, in that he willfully misrepresented a material fact to gain entry."},
 {"id": "S9_clean_fraud_with_disposition", "facts": {},
  "narrative": "On September 2, 2025, CBP officers at the Hidalgo port of entry encountered 'Rafael Soto', a citizen of Mexico. Subject presented a counterfeit permit and stated that it was genuine. Subject has no prior immigration history. Subject is inadmissible under section 212(a)(6)(C)(i) of the INA, in that he willfully misrepresented a material fact to gain entry. Subject was processed for expedited removal and the case was reviewed by a supervisor."},
 {"id": "S10_missing_place", "facts": {},
  "narrative": "On October 11, 2025, agents apprehended 'Elena Vargas', a citizen of El Salvador. Subject stated she crossed on foot without inspection. Subject has no prior immigration history and no documents. Subject is inadmissible under section 212(a)(6)(A)(i) of the INA, in that she entered at a place not designated by the Attorney General."},
 {"id": "S11_missing_statements", "facts": {},
  "narrative": "On November 5, 2025, Border Patrol agents apprehended 'Tomas Rivera', a citizen of Mexico, near the Tucson station. Subject crossed on foot without inspection. Subject has no prior immigration history. Subject is inadmissible under section 212(a)(6)(A)(i) of the INA, in that he entered at a place not designated by the Attorney General and was not then admitted or paroled."},
 {"id": "S12_documents_conflict", "facts": {},
  "narrative": "On January 8, 2026, officers encountered 'Nadia Karim', a citizen of Jordan, at the Detroit airport. Subject stated she has no documents. Subject presented her passport and a visa to the inspecting officer. Subject has no prior immigration history. Subject is inadmissible under section 212(a)(7)(A)(i)(I) of the INA, in that she lacked a valid entry document."},
 {"id": "S13_missing_history_and_name", "facts": {},
  "narrative": "On February 19, 2026, agents apprehended a male subject, a citizen of Peru, near the Del Rio sector. Subject stated he entered without inspection at a place not designated by the Attorney General. Subject is inadmissible under section 212(a)(6)(A)(i) of the INA, in that he was not then admitted or paroled."},
 {"id": "S14_no_citation", "facts": {},
  "narrative": "On March 3, 2026, agents apprehended 'Omar Haddad', a citizen of Egypt, near the Laredo station. Subject stated he crossed the river without inspection. Subject has no prior immigration history. Subject has no documents."},
 {"id": "S15_clean_prior_removal", "facts": {},
  "narrative": "On April 17, 2026, agents apprehended 'Hector Salas', a citizen of Honduras, near the Brownsville, TX station. Subject stated he entered without inspection. Subject admitted he was previously removed from the United States in 2019. Records confirm he was ordered removed and deported. Subject is inadmissible under section 212(a)(9)(A) of the INA, in that he was previously removed and entered again. Subject was served with a notice of reinstatement."},
 {"id": "S16_overstay_status_conflict", "facts": {},
  "narrative": "On May 12, 2026, ICE officers encountered 'Wei Chen', a citizen of China, near the Los Angeles field office. Subject stated he entered without inspection in 2021 and has no documents. Subject has no prior immigration history. Subject is removable under section 237(a)(1)(B) of the INA, in that he was admitted and remained in violation of his status."},
 {"id": "S17_multi_charge_clean", "facts": {},
  "narrative": "On June 20, 2026, agents apprehended 'Pedro Ortiz', a citizen of Guatemala, near the Rio Grande station. Subject stated he crossed without inspection. Subject has no documents. Subject has no prior immigration history. Subject is inadmissible under section 212(a)(6)(A)(i) of the INA, in that he entered at a place not designated by the Attorney General. Subject is also inadmissible under section 212(a)(7)(A)(i)(I) of the INA, in that he lacked a valid entry document. Subject was detained and referred to a supervisor."},
 {"id": "S18_missing_country_and_date", "facts": {},
  "narrative": "Agents apprehended 'Lina Haddad' near the Calexico port of entry. Subject stated she presented a counterfeit card. Subject has no prior immigration history. Subject is inadmissible under section 212(a)(6)(C)(i) of the INA, in that she willfully misrepresented a material fact."},
 {"id": "S19_all_caps_clean", "facts": {},
  "narrative": "On 07/15/2026 Border Patrol agents located MARIO DIAZ, a citizen of Nicaragua, near the Eagle Pass checkpoint. Subject stated he crossed on foot without inspection and has no documents. Subject has no prior immigration history. Subject is inadmissible under 8 U.S.C. 1182(a)(6)(A)(i), in that he entered at a place not designated by the Attorney General. Subject was processed and a Form I-213 was prepared."},
 {"id": "S20_fraud_no_document", "facts": {},
  "narrative": "On August 30, 2026, officers encountered 'Sara Ali', a citizen of Somalia, at the Seattle airport. Subject stated she arrived on a flight and was admitted. Subject has no prior immigration history. Subject is inadmissible under section 212(a)(6)(C)(i) of the INA, in that she willfully misrepresented a material fact to gain entry."},
]

# Answer key: the (type, element) problems we planted in each case, and whether a human must review it.
KEY = {
 "S1_clean":                 {"planted": [], "human": False},
 "S2_missing_citizenship":   {"planted": [("missing", "country_of_citizenship")], "human": False},
 "S3_no_manner_of_entry":    {"planted": [("missing", "manner_of_entry")], "human": False},
 "S4_charge_mismatch":       {"planted": [("citation_mismatch", "charge_citation"), ("inconsistent", "manner_of_entry")], "human": True},
 "S5_prior_removal_conflict":{"planted": [("inconsistent", "immigration_history")], "human": False},
 "S6_multi_charge_incomplete":{"planted": [("missing", "date_of_encounter"), ("missing", "place_of_encounter"), ("unclear", "charge_citation"), ("missing", "subject_statements")], "human": True},
 "S7_clean_overstay":        {"planted": [], "human": False},
 "S8_fraud_missing_date":    {"planted": [("missing", "date_of_encounter")], "human": False},
 "S9_clean_fraud_with_disposition": {"planted": [], "human": False},
 "S10_missing_place":        {"planted": [("missing", "place_of_encounter")], "human": False},
 "S11_missing_statements":   {"planted": [("missing", "subject_statements"), ("missing", "documents")], "human": False},
 "S12_documents_conflict":   {"planted": [("inconsistent", "documents")], "human": False},
 "S13_missing_history_and_name": {"planted": [("missing", "subject_name"), ("missing", "immigration_history"), ("missing", "documents")], "human": False},
 "S14_no_citation":          {"planted": [("citation_mismatch", "charge_citation")], "human": True},
 "S15_clean_prior_removal":  {"planted": [("missing", "documents")], "human": False},
 "S16_overstay_status_conflict": {"planted": [("citation_mismatch", "charge_citation"), ("inconsistent", "manner_of_entry")], "human": True},
 "S17_multi_charge_clean":   {"planted": [], "human": True},
 "S18_missing_country_and_date": {"planted": [("missing", "country_of_citizenship"), ("missing", "date_of_encounter")], "human": False},
 "S19_all_caps_clean":       {"planted": [], "human": False},
 "S20_fraud_no_document":    {"planted": [("missing", "documents"), ("citation_mismatch", "charge_citation")], "human": False},
}

if __name__ == "__main__":
    caught, missed, wrong, human_ok, human_total = 0, 0, 0, 0, 0
    for s in SAMPLES:
        result = checker.review(s["narrative"], s["facts"], use_ai=False)
        found = [(f["type"], f["element"]) for f in result["flags"] if not f.get("advisory")]
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
