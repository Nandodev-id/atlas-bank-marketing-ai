"""Source CSV contract; derived from the user's case-study data dictionary."""

CSV_DELIMITER = ";"
TARGET_COLUMN = "y"
TARGET_VALUES = frozenset({"yes", "no"})
EXPECTED_COLUMNS = (
    "age",
    "job",
    "marital",
    "education",
    "default",
    "housing",
    "loan",
    "contact",
    "month",
    "day_of_week",
    "duration",
    "campaign",
    "pdays",
    "previous",
    "poutcome",
    "emp.var.rate",
    "cons.price.idx",
    "cons.conf.idx",
    "euribor3m",
    "nr.employed",
    "y",
)

# Availability and fairness decisions will be finalized in Phase 1/Phase 2.
KNOWN_POST_CONTACT_FEATURES = frozenset({"duration"})
ETHICS_REVIEW_FEATURES = frozenset({"age", "job", "marital", "education"})
