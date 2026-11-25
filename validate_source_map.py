import csv
import re
from pathlib import Path


REQUIRED = [
    "rule_id",
    "asset",
    "timeframe",
    "indicator",
    "usage_context",
    "proposed_decision_role",
    "source_video",
    "source_timestamp",
    "source_quote",
    "class",
    "engine",
    "status",
    "verification_notes",
]

ROLES = {
    "CONTEXT_ONLY",
    "CONFIRMATION",
    "PRIMARY_CONDITION",
    "RISK_RULE",
    "NO_AUTOMATIC_RULE",
}

CLASSES = {"A", "B", "C"}

ENGINES = {
    "FAITHFUL",
    "EXPERIMENTAL",
    "FAITHFUL_PENDING",
}

STATUSES = {
    "VERIFIED",
    "UNVERIFIED",
}

TIMESTAMP_PATTERN = re.compile(r"^(?:\d{1,2}:\d{2}(?::\d{2})?)$")


def valid_timestamp(value: str) -> bool:
    if not TIMESTAMP_PATTERN.match(value):
        return False

    parts = [int(part) for part in value.split(":")]

    if len(parts) == 2:
        hours = 0
        minutes = parts[0]
        seconds = parts[1]
    else:
        hours = parts[0]
        minutes = parts[1]
        seconds = parts[2]

    return (
        0 <= hours < 24
        and 0 <= minutes < 60
        and 0 <= seconds < 60
    )


def validate(path):
    with open(path, newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))

    if not rows:
        raise ValueError("CSV empty")

    missing_columns = [
        column
        for column in REQUIRED
        if column not in rows[0]
    ]

    if missing_columns:
        raise ValueError(f"missing columns: {missing_columns}")

    seen_rule_ids = set()

    for row_number, row in enumerate(rows, start=2):
        rule_id = row["rule_id"].strip()

        if not rule_id:
            raise ValueError(f"row {row_number}: empty rule_id")

        rule_id_key = rule_id.upper()

        if rule_id_key in seen_rule_ids:
            raise ValueError(f"row {row_number}: duplicate rule_id")

        seen_rule_ids.add(rule_id_key)

        role = row["proposed_decision_role"].strip().upper()

        if role not in ROLES:
            raise ValueError(f"row {row_number}: invalid role")

        rule_class = row["class"].strip().upper()

        if rule_class not in CLASSES:
            raise ValueError(f"row {row_number}: invalid class")

        engine = row["engine"].strip().upper()

        if engine not in ENGINES:
            raise ValueError(f"row {row_number}: invalid engine")

        status = row["status"].strip().upper()

        if status not in STATUSES:
            raise ValueError(f"row {row_number}: invalid status")

        if engine == "FAITHFUL" and (
            rule_class == "C"
            or status != "VERIFIED"
        ):
            raise ValueError(f"row {row_number}: ineligible faithful rule")

        if status == "VERIFIED":
            if engine != "FAITHFUL":
                raise ValueError(
                    f"row {row_number}: verified rule must use FAITHFUL engine"
                )

            required_fields = (
                "source_video",
                "source_timestamp",
                "source_quote",
                "asset",
                "timeframe",
            )

            for field in required_fields:
                if not row[field].strip():
                    raise ValueError(
                        f"row {row_number}: verified rule missing {field}"
                    )

            if not valid_timestamp(row["source_timestamp"].strip()):
                raise ValueError(f"row {row_number}: invalid timestamp")

    return len(rows)


if __name__ == "__main__":
    print(validate("source_usage_map_v022.csv"))