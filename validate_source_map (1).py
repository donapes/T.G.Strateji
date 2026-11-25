import csv
REQUIRED = ["rule_id","asset","timeframe","indicator","usage_context","proposed_decision_role","source_video","source_timestamp","source_quote","class","engine","status","verification_notes"]
ROLES = {"CONTEXT_ONLY","CONFIRMATION","PRIMARY_CONDITION","RISK_RULE","NO_AUTOMATIC_RULE"}
CLASSES = {"A","B","C"}
ENGINES = {"FAITHFUL","EXPERIMENTAL","FAITHFUL_PENDING"}

def validate(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("CSV empty")
    missing = [c for c in REQUIRED if c not in rows[0]]
    if missing:
        raise ValueError(f"missing columns: {missing}")
    ids = set()
    for i, r in enumerate(rows, 2):
        if not r["rule_id"].strip():
            raise ValueError(f"row {i}: empty rule_id")
        if r["rule_id"] in ids:
            raise ValueError(f"row {i}: duplicate rule_id")
        ids.add(r["rule_id"])
        if r["proposed_decision_role"] not in ROLES:
            raise ValueError(f"row {i}: invalid role")
        if r["class"] not in CLASSES:
            raise ValueError(f"row {i}: invalid class")
        if r["engine"] not in ENGINES:
            raise ValueError(f"row {i}: invalid engine")
        if r["engine"] == "FAITHFUL" and r["status"] == "VERIFIED":
            parts = r["source_timestamp"].split(":")
            if len(parts) != 3 or not all(p.isdigit() for p in parts) or int(parts[1]) >= 60 or int(parts[2]) >= 60:
                raise ValueError(f"row {i}: invalid timestamp")
        if r["engine"] == "FAITHFUL" and (r["class"] == "C" or r["status"] != "VERIFIED"):
            raise ValueError(f"row {i}: ineligible faithful rule")
        if r["status"] == "VERIFIED":
            for field in ("source_video","source_timestamp","source_quote","asset","timeframe"):
                if not r[field].strip():
                    raise ValueError(f"row {i}: verified rule missing {field}")
    return len(rows)

if __name__ == "__main__":
    print(validate("source_usage_map_v022.csv"))
