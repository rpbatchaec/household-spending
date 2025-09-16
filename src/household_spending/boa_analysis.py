#!/usr/bin/env python3
"""
Household Spending Transform with Personal Category Mapping (pandas)

Features:
- Skip metadata; detect header
- Account (col 1) = "BOA-5670"
- AccountSeq (col 2) = "BOA-5670-0001", ...
- Parse Date -> YYYY-MM-DD
- Compute numeric Amount (Credit - Debit, or parse Amount)
- Category mapping:
   1) Apply user mapping CSV (exact → contains → regex)
   2) Fallback to keyword rules / aliases
   3) Otherwise 'Uncategorized'
- Output:
   * <stem>_transformed.csv
   * <stem>_uncategorized.csv (unique descriptions needing a map)
Optional: write Parquet if desired (requires pyarrow/fastparquet)
"""

import re
from pathlib import Path

import pandas as pd

# --- Configuration ---
ACCOUNT_ID = "BOA-5670"
BASE_DIR = Path(r"E:\Backup from Surface Pro 1\Personal\Financial\Household Spending Analysis")
SOURCE_PATH = BASE_DIR / "BOA-5670-Activity-2025 01 01 through 2025 07 31.csv"
OUTPUT_CSV = SOURCE_PATH.with_name(SOURCE_PATH.stem + "_transformed.csv")
UNCAT_CSV = SOURCE_PATH.with_name(SOURCE_PATH.stem + "_uncategorized.csv")
MAPPING_PATH = BASE_DIR / "CategoryMapping.csv"  # optional; script continues if missing
WRITE_PARQUET = False  # set True if you want .parquet too (needs pyarrow or fastparquet)

# Header detection
HEADER_CANDIDATES = [
    ("Date", "Description"),
    ("Posting Date", "Description"),
    ("Date", "Payee"),
    ("Transaction Date", "Description"),
]

# Canonical category list (edit to your taxonomy)
CANON = [
    "Art-Framing and Supplies",
    "Art-Lessons",
    "Art-Marketing",
    "Art-Printing",
    "Art-Ref Photos",
    "Automotive-Fuel",
    "Automotive-License/Registration",
    "Automotive-Maintenance",
    "Automotive-Parking and Tolls",
    "Bank Fees",
    "Bank Interest",
    "Books / Magazines",
    "Business-Equipment",
    "Camera/Photography",
    "Cash-ATM",
    "Charitable Giving",
    "Cleaning and Laundry",
    "Clothing-MJB",
    "Clothing-RPB",
    "Computers/Electronics",
    "Credit Card Fees",
    "Credit Card Payment",
    "Dental",
    "Deposit-Misc",
    "Deposit-Cash",
    "Deposit-Travel Reimbursement",
    "Entertainment",
    "Fitness",
    "Food-Eating Out",
    "Food-Snacks",
    "Gift",
    "Gift-Christmas",
    "Gift-Graduation",
    "Gift-Misc",
    "Gift-Wedding",
    "GPB Loan-Disbursement",
    "GPB Loan-Repayment",
    "Groceries",
    "Grooming-MJB",
    "Grooming-RPB",
    "HOA",
    "Home Imp / Renovation-GPB",
    "Home Imp / Renovation-JWB",
    "Home Imp / Renovation",
    "Home Imp-Landscape",
    "Home Maintenance and Repair",
    "Home-Exterminator",
    "Home-Furnishings",
    "Income",
    "Income-RF",
    "Income-Pension",
    "Income-SSA",
    "Insurance",
    "Insurance-Auto",
    "Insurance-Homeowners",
    "Insurance-Life",
    "Insurance-LTC",
    "Insurance-Medical",
    "Insurance-Personal Liability",
    "Landscape Maintenance",
    "Loan Payment-gpb",
    "Medical",
    "Medical-Chiro/Phys Ther",
    "Medical-Optical",
    "Mortgage",
    "Office Supplies",
    "Payments-Credit Cards",
    "Pet-Boarding/Pet Sitting",
    "Pet-Food",
    "Pet-Grooming",
    "Pet-Misc",
    "Pet-Registration",
    "Pet-Vet Svcs",
    "Pharmacy / Cosmetics",
    "Photographic Equipment & Supplies",
    "Political Contributions",
    "Professional Development",
    "Professional Org Dues",
    "Professional Services",
    "Refund-Misc",
    "Shopping",
    "Shipping",
    "Software License",
    "Subscriptions-Apps/Software",
    "Subscriptions-Music/Video Streaming",
    "Subscriptions-Publications",
    "Taxes",
    "Tax Prep",
    "Taxes-2025 Est",
    "Taxes-2024 Est",
    "Taxes-2023 Final",
    "Taxes-2023 Est",
    "Taxes-NH Business Registration",
    "Taxes-Refund-2023",
    "Taxes-Property Tax",
    "Transfer",
    "Transportation-Uber/Lyft",
    "Travel",
    "Travel-Hotels",
    "Travel-Misc",
    "Travel-Parking",
    "Travel-Transportation",
    "Unknown",
    "Utilities-Communications",
    "Utilities-Elec",
    "Utilities-Gas",
    "Utilities-Internet Service/TV",
    "Utilities-Mobile",
    "Utilities-Sewer & Trash",
    "Utilities-Water",
    "Utilities-Web Hosting",
    "Wine/Beer",
    "Uncategorized",
]

ALIASES = {
    "atm fee": "Bank Fees",
    "mortgage": "Mortgage",
    "hoa": "HOA",
    "electric": "Utilities-Elec",
    "water": "Utilities-Water",
    "gas bill": "Utilities-Gas",
    "internet": "Utilities-Internet Service/TV",
    "insurance": "Insurance",
    "doctor": "Medical",
    "dental": "Dental",
    "pharmacy": "Pharmacy / Cosmetics",
    "medical": "Medical",
    "hospital": "Medical",
    "transportation": "Transportation",
    "tolls": "Transportation",
    "parking": "Transportation",
    "fuel": "Fuel",
    "loan payment confirmation#": "Loan Payment-gpb",
    "grocery": "Groceries",
    "groceries": "Groceries",
    "restaurant": "Food-Eating Out",
    "dining": "Food-Eating Out",
    "coffee": "Food-Snacks",
    "shopping": "Shopping",
    "crossroads contr des": "Home Imp / Renovation",
    "entertainment": "Entertainment",
    "travel": "Travel",
    "airfare": "Travel-Transportation",
    "airline": "Travel-Transportation",
    "hotel": "Travel-Hotels",
    "household": "Home-Furnishings",
    "gift": "Charitable Giving",
    "charity": "Charitable Giving",
    "donation": "Charitable Giving",
    "tithe": "Charitable Giving",
    "transfer": "Transfers",
    "zelle": "Transfers",
    "online banking transfer": "Transfers",
    "salary": "Income",
    "payroll": "Income",
    "ssa": "Income-SSA",
    "deposit": "Income",
    "refund": "Refund-Misc",
    "tax": "Taxes",
    "irs": "Taxes",
}

# Keyword hints if mapping doesn’t hit
KEYWORD_RULES = [
    (
        [
            "whole foods",
            "market basket",
            "stop & shop",
            "hannaford",
            "trader joe",
            "aldi",
            "shaw's",
            "wegmans",
        ],
        "Groceries",
    ),
    (["chipotle", "pizza", "panera", "cafe", "restaurant"], "Food-Eating Out"),
    (["mcdonald", "starbucks", "dunkin", "chipotle", "pizza"], "Food-Snacks"),
    (["shell", "exxon", "bp ", "mobil", "sunoco"], "Automotive-Fuel"),
    (["uber", "lyft"], "Transportation-Uber/Lyft"),
    (["mbta", "amtrak"], "Travel-Transportation"),
    (["verizon", "xfinity mobile", "att ", "t-mobile"], "Utilities-Mobile"),
    (["comcast", "xfinity"], "Utilities-Internet Service/TV"),
    (
        ["netflix", "hulu", "spotify", "prime video", "apple tv+"],
        "Subscriptions-Music/Video Streaming",
    ),
    (["amazon", "walmart", "target", "costco", "best buy"], "Shopping"),
    (["marriott", "hilton", "airbnb"], "Travel-Hotels"),
    (
        ["delta", "american airlines", "united airlines", "jetblue", "southwest"],
        "Travel-Transportation",
    ),
    (["cvs", "walgreens", "rite aid"], "Pharmacy / Cosmetics"),
    (["geico", "progressive", "allstate", "state farm"], "Insurance"),
    (["irs", "tax"], "Taxes"),
    (["church", "salvation army", "red cross"], "Charitable Giving"),
]


# --- Helpers ---
def find_header_line(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f):
            for a, b in HEADER_CANDIDATES:
                if a in line and b in line:
                    return i
    raise ValueError("Could not find header row—adjust HEADER_CANDIDATES if needed.")


def coerce_money(x):
    if pd.isna(x):
        return 0.0
    s = str(x).strip()
    if s == "":
        return 0.0
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]
    s = s.replace("$", "").replace(",", "").strip()
    try:
        val = float(s)
    except ValueError:
        return pd.NA
    return -val if neg else val


def pick_first_present(df: pd.DataFrame, names: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower_map:
            return lower_map[n.lower()]
    return None


def clean_text(s: str | None) -> str:
    if s is None:
        return ""
    # lowercase, strip, collapse spaces, drop common store tokens
    t = str(s).lower().strip()
    t = re.sub(r"\s+", " ", t)
    # remove common transaction noise like store numbers or extra hashes
    t = re.sub(r"#\d+", "", t)
    t = re.sub(r"\d{3,}", "", t)  # drop long digit runs (terminal IDs, etc.)
    return t.strip()


def canonicalize(cat: str) -> str:
    if not cat:
        return "Uncategorized"
    # Exact match to CANON (case-insensitive)
    for c in CANON:
        if c.lower() == cat.lower():
            return c
    # Alias
    if cat.lower() in ALIASES:
        return ALIASES[cat.lower()]
    # Otherwise leave as-is if you want to allow custom, else force Uncategorized
    return cat


def load_mapping(path: Path):
    """Load mapping CSV with columns: type, pattern, category"""
    if not path.exists():
        return [], [], []
    m = pd.read_csv(path, dtype=str).fillna("")
    # Clean
    m["type"] = m["type"].str.lower().str.strip()
    m["pattern"] = m["pattern"].map(clean_text)
    m["category"] = m["category"].map(lambda x: canonicalize(str(x)))
    exact = [
        (row.pattern, row.category) for _, row in m[m["type"] == "exact"].iterrows() if row.pattern
    ]
    contains = [
        (row.pattern, row.category)
        for _, row in m[m["type"] == "contains"].iterrows()
        if row.pattern
    ]
    regex = []
    for _, row in m[m["type"] == "regex"].iterrows():
        if not row.pattern:
            continue
        try:
            regex.append((re.compile(row.pattern, flags=re.I), row.category))
        except re.error:
            # skip invalid regex patterns silently
            continue
    return exact, contains, regex


def apply_mapping(desc_clean: str, exact, contains, regex):
    # 1) exact
    for patt, cat in exact:
        if desc_clean == patt:
            return cat
    # 2) contains
    for patt, cat in contains:
        if patt and patt in desc_clean:
            return cat
    # 3) regex
    for rx, cat in regex:
        if rx.search(desc_clean):
            return cat
    return None


def fallback_keyword_rules(haystack: str):
    for keywords, canon in KEYWORD_RULES:
        if any(k in haystack for k in keywords):
            return canon
    # scan aliases as very loose fallback
    for key, canon in ALIASES.items():
        if key in haystack:
            return canon
    return None


# --- Main ---
def main():
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"Source file not found:\n{SOURCE_PATH}")

    header_line = find_header_line(SOURCE_PATH)

    df = pd.read_csv(
        SOURCE_PATH,
        skiprows=header_line,
        dtype=str,
        keep_default_na=False,
    )
    df.columns = [c.strip() for c in df.columns]

    # Account + AccountSeq
    df.insert(0, "Account", ACCOUNT_ID)
    seq = pd.Series(range(1, len(df) + 1), index=df.index).map(lambda i: f"{ACCOUNT_ID}-{i:04d}")
    df.insert(1, "AccountSeq", seq)

    # Date
    date_col = pick_first_present(df, ["Date", "Posting Date", "Transaction Date"])
    if date_col is None:
        raise ValueError("No date column found.")
    parsed_dates = pd.to_datetime(
        df[date_col].str.strip().replace("", pd.NA), errors="coerce", infer_datetime_format=True
    )
    if parsed_dates.isna().all():
        parsed_dates = pd.to_datetime(df[date_col], format="%m/%d/%Y", errors="coerce")
    df["Date"] = parsed_dates.dt.strftime("%Y-%m-%d")

    # Amount
    debit_col = pick_first_present(df, ["Debit", "Debits", "Withdrawal", "Withdrawals"])
    credit_col = pick_first_present(df, ["Credit", "Credits", "Deposit", "Deposits"])
    if debit_col or credit_col:
        debit = df[debit_col].map(coerce_money) if debit_col else 0.0
        credit = df[credit_col].map(coerce_money) if credit_col else 0.0
        df["Amount"] = pd.to_numeric(credit, errors="coerce") - pd.to_numeric(
            debit, errors="coerce"
        )
    else:
        amount_col = pick_first_present(df, ["Amount", "Transaction Amount"])
        if amount_col is None:
            raise ValueError("No amount columns found.")
        df["Amount"] = pd.to_numeric(df[amount_col].map(coerce_money), errors="coerce")

    # Optional numeric balance
    balance_col = pick_first_present(df, ["Running Balance", "Balance"])
    if balance_col:
        df["Running Balance (num)"] = pd.to_numeric(
            df[balance_col].map(coerce_money), errors="coerce"
        )

    # Prepare text for mapping
    desc_col = pick_first_present(df, ["Description", "Payee", "Memo", "Details"])
    df["Description (clean)"] = df[desc_col].map(clean_text) if desc_col else ""

    # Preserve raw Category if present
    if "Category" in df.columns:
        df["Category (raw)"] = df["Category"]
    else:
        df["Category (raw)"] = ""

    # Load user mapping
    exact, contains, regex = load_mapping(MAPPING_PATH)

    # Apply mapping → fallback rules → fallback aliases → Uncategorized
    def categorize_row(row):
        # Priority 0: if you trust existing Category, uncomment next lines:
        # if row["Category (raw)"].strip():
        #     return canonicalize(row["Category (raw)"])

        # Priority 1: user mapping file
        c = apply_mapping(row["Description (clean)"], exact, contains, regex)
        if c:
            return canonicalize(c)

        # Priority 2: keyword rules using description + raw category text
        hay = f"{row['Description (clean)']} {clean_text(row['Category (raw)'])}".strip()
        c = fallback_keyword_rules(hay)
        if c:
            return c

        # Priority 3: try aliasing raw category directly
        raw = clean_text(row["Category (raw)"])
        if raw in ALIASES:
            return ALIASES[raw]

        return "Uncategorized"

    df["Category"] = df.apply(categorize_row, axis=1)

    # Column order
    front = [c for c in ["Account", "AccountSeq", "Date", "Amount", "Category"] if c in df.columns]
    remaining = [c for c in df.columns if c not in front]
    df = df[front + remaining]

    # Write output
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Done. Wrote transformed CSV to:\n{OUTPUT_CSV}")

    # Emit uncategorized summary to help you grow the map
    unc = (
        df.loc[df["Category"] == "Uncategorized", ["Description (clean)"]]
        .rename(columns={"Description (clean)": "pattern"})
        .assign(type="exact", category="")
        .value_counts("pattern")
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    if not unc.empty:
        unc.to_csv(UNCAT_CSV, index=False)
        print(f"Wrote suggestions for mapping (uncategorized descriptions) to:\n{UNCAT_CSV}")
        print(
            "Tip: open that CSV, add 'category' values and move rows into your CategoryMapping.csv."
        )

    if WRITE_PARQUET:
        pq_path = OUTPUT_CSV.with_suffix(".parquet")
        try:
            df.to_parquet(pq_path, engine="pyarrow", index=False)
        except Exception:
            df.to_parquet(pq_path, engine="fastparquet", index=False)
        print(f"Also wrote Parquet to:\n{pq_path}")


if __name__ == "__main__":
    main()
