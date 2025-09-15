#!/usr/bin/env python3
"""
Household Spending Transform (pandas) package entry point.

Features:
- transform_main(argv=None): CLI entrypoint & callable for notebooks
- Account + AccountSeq
- Date parsing -> YYYY-MM-DD
- Amount numeric (Credit - Debit, or parsed Amount)
- Vendor normalization -> Merchant
- Category via personal mapping first, then rules; emits *_uncategorized.csv
- Learning step: --learn / --learn-from to append labeled patterns into mapping CSV
- --category-mapping to choose a mapping file
- --report to print quick stats

Public helpers (used in tests): coerce_money, normalize_merchant
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

CANON = [
    "Income",
    "Transfers",
    "Fees",
    "Taxes",
    "Housing",
    "Utilities",
    "Insurance",
    "Healthcare",
    "Transportation",
    "Fuel",
    "Groceries",
    "Dining",
    "Shopping",
    "Subscriptions",
    "Entertainment",
    "Travel",
    "Household",
    "Gifts/Charity",
    "Uncategorized",
]

ALIASES = {
    "atm fee": "Fees",
    "service fee": "Fees",
    "fee": "Fees",
    "mortgage": "Housing",
    "rent": "Housing",
    "hoa": "Housing",
    "electric": "Utilities",
    "water": "Utilities",
    "sewer": "Utilities",
    "gas bill": "Utilities",
    "internet": "Utilities",
    "phone": "Utilities",
    "insurance": "Insurance",
    "doctor": "Healthcare",
    "dental": "Healthcare",
    "pharmacy": "Healthcare",
    "medical": "Healthcare",
    "hospital": "Healthcare",
    "transportation": "Transportation",
    "tolls": "Transportation",
    "parking": "Transportation",
    "fuel": "Fuel",
    "gas": "Fuel",
    "grocery": "Groceries",
    "groceries": "Groceries",
    "restaurant": "Dining",
    "dining": "Dining",
    "coffee": "Dining",
    "shopping": "Shopping",
    "subscription": "Subscriptions",
    "subscriptions": "Subscriptions",
    "entertainment": "Entertainment",
    "travel": "Travel",
    "airfare": "Travel",
    "airline": "Travel",
    "hotel": "Travel",
    "household": "Household",
    "gift": "Gifts/Charity",
    "charity": "Gifts/Charity",
    "donation": "Gifts/Charity",
    "tithe": "Gifts/Charity",
    "transfer": "Transfers",
    "zelle": "Transfers",
    "online banking transfer": "Transfers",
    "salary": "Income",
    "payroll": "Income",
    "ssa": "Income",
    "deposit": "Income",
    "refund": "Income",
    "tax": "Taxes",
    "irs": "Taxes",
}

KEYWORD_RULES = [
    (["whole foods", "market basket", "stop & shop", "trader joe", "aldi", "shaw's"], "Groceries"),
    (
        ["mcdonald", "starbucks", "dunkin", "chipotle", "pizza", "panera", "cafe", "restaurant"],
        "Dining",
    ),
    (["shell", "exxon", "bp ", "mobil", "sunoco"], "Fuel"),
    (["uber", "lyft", "mbta", "amtrak"], "Transportation"),
    (["comcast", "verizon", "xfinity", "spectrum", "att ", "t-mobile"], "Utilities"),
    (["netflix", "hulu", "spotify", "max ", "disney+"], "Subscriptions"),
    (["amazon", "walmart", "target", "costco", "best buy"], "Shopping"),
    (
        [
            "marriott",
            "hilton",
            "airbnb",
            "delta",
            "american airlines",
            "united airlines",
            "jetblue",
        ],
        "Travel",
    ),
    (["cvs", "walgreens", "rite aid"], "Healthcare"),
    (["geico", "progressive", "allstate", "state farm"], "Insurance"),
    (["irs", "tax"], "Taxes"),
    (["church", "salvation army", "red cross"], "Gifts/Charity"),
]

HEADER_CANDIDATES = [
    ("Date", "Description"),
    ("Posting Date", "Description"),
    ("Date", "Payee"),
    ("Transaction Date", "Description"),
]

_VENDOR_STOPWORDS = {
    "authorization",
    "auth",
    "purchase",
    "pos",
    "debit",
    "credit",
    "recurring",
    "online",
    "banking",
    "transfer",
    "zelle",
    "visa",
    "mastercard",
    "mc",
    "card",
    "payment",
    "payment thank you",
    "pymt",
    "apple pay",
    "google pay",
    "ach",
    "echeck",
    "ck",
    "trnsfr",
    "fee",
    "adj",
    "refund",
}
_VENDOR_STRIP_REGEXES = [
    re.compile(r"#\d+"),
    re.compile(r"\b\d{3,}\b"),
    re.compile(r"\s{2,}"),
    re.compile(r"[^a-z0-9 &.'-]"),
]
MERCHANT_ALIASES = {
    "the home depot": "Home Depot",
    "home depot": "Home Depot",
    "walmart.com": "Walmart",
    "wal-mart": "Walmart",
    "amazon marketplace": "Amazon",
    "amzn mktp": "Amazon",
    "amzn digital": "Amazon",
    "starbucks coffee": "Starbucks",
    "dunkin donuts": "Dunkin",
    "wholefoods": "Whole Foods",
    "whole foods market": "Whole Foods",
    "trader joes": "Trader Joe's",
    "market basket": "Market Basket",
    "stop & shop": "Stop & Shop",
    "shell oil": "Shell",
    "exxonmobil": "Exxon",
    "geico insurance": "GEICO",
}


def coerce_money(x) -> float | pd.NA:
    """Convert money-like strings to float."""
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


def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _clean_text(s: str | None) -> str:
    if s is None:
        return ""
    t = str(s).lower()
    for rx in _VENDOR_STRIP_REGEXES:
        t = rx.sub(" ", t)
    return _normalize_ws(t)


def normalize_merchant(desc_clean: str) -> str:
    """Return a normalized vendor name from a cleaned description string."""
    if not desc_clean:
        return ""
    tokens = [tok for tok in desc_clean.split(" ") if tok and tok not in _VENDOR_STOPWORDS]
    base = _normalize_ws(" ".join(tokens))
    base = re.sub(r"^(debit|credit)\s+card\s+purchase\s+", "", base)
    base = re.sub(r"^(purchase|pos)\s+", "", base)
    alias_key = re.sub(r"\b(store|stn|st|unit|loc)\b.*$", "", base).strip()
    for k, v in MERCHANT_ALIASES.items():
        if k in alias_key:
            return v
    if not base:
        return ""
    name = base.title()
    for keep in ["GEICO", "IRS", "MBTA", "BP", "AT&T"]:
        name = re.sub(rf"\b{keep.title()}\b", keep, name)
    return name


def _canonicalize(cat: str) -> str:
    if not cat:
        return "Uncategorized"
    for c in CANON:
        if c.lower() == cat.lower():
            return c
    if cat.lower() in ALIASES:
        return ALIASES[cat.lower()]
    return cat


def _pick_first_present(df: pd.DataFrame, names: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower_map:
            return lower_map[n.lower()]
    return None


def _find_header_line(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f):
            for a, b in HEADER_CANDIDATES:
                if a in line and b in line:
                    return i
    raise ValueError("Could not find header rowâ€”adjust HEADER_CANDIDATES.")


def _load_mapping(path: Path | None):
    if not path or not path.exists():
        return [], [], []
    m = pd.read_csv(path, dtype=str).fillna("")
    if not {"type", "pattern", "category"}.issubset(m.columns):
        raise ValueError(f"Mapping file {path} must have columns: type, pattern, category")
    m["type"] = m["type"].str.lower().str.strip()
    m["pattern"] = m["pattern"].map(_clean_text)
    m["category"] = m["category"].map(_canonicalize)
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
            continue
    return exact, contains, regex


def _apply_mapping(desc_clean: str, exact, contains, regex):
    for patt, cat in exact:
        if desc_clean == patt:
            return cat, "mapping_exact"
    for patt, cat in contains:
        if patt and patt in desc_clean:
            return cat, "mapping_contains"
    for rx, cat in regex:
        if rx.search(desc_clean):
            return cat, "mapping_regex"
    return None, None


def _fallback_keyword_rules(haystack: str):
    for keywords, canon in KEYWORD_RULES:
        if any(k in haystack for k in keywords):
            return canon, "keyword_rule"
    for key, canon in ALIASES.items():
        if key in haystack:
            return canon, "alias_rule"
    return None, None


def _default_mapping_path_for(source_path: Path) -> Path | None:
    p1 = source_path.parent / "CategoryMapping.csv"
    if p1.exists():
        return p1
    p2 = source_path.parent.parent / "mappings" / "CategoryMapping.csv"
    if p2.exists():
        return p2
    return None


def transform(
    source: Path,
    category_mapping: Path | None = None,
    learn_from: Path | None = None,
    learn: bool = False,
    report: bool = False,
    write_parquet: bool = False,
    account_id: str = "BOA-5670",
) -> Path:
    """Transform a bank CSV and write outputs next to the source file."""
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    header_line = _find_header_line(source)
    df = pd.read_csv(source, skiprows=header_line, dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]

    df.insert(0, "Account", account_id)
    seq = pd.Series(range(1, len(df) + 1), index=df.index).map(lambda i: f"{account_id}-{i:04d}")
    df.insert(1, "AccountSeq", seq)

    date_col = _pick_first_present(df, ["Date", "Posting Date", "Transaction Date"])
    if date_col is None:
        raise ValueError("No date column found.")
    parsed_dates = pd.to_datetime(
        df[date_col].str.strip().replace("", pd.NA), errors="coerce", infer_datetime_format=True
    )
    if parsed_dates.isna().all():
        parsed_dates = pd.to_datetime(df[date_col], format="%m/%d/%Y", errors="coerce")
    df["Date"] = parsed_dates.dt.strftime("%Y-%m-%d")

    debit_col = _pick_first_present(df, ["Debit", "Debits", "Withdrawal", "Withdrawals"])
    credit_col = _pick_first_present(df, ["Credit", "Credits", "Deposit", "Deposits"])
    if debit_col or credit_col:
        debit = df[debit_col].map(coerce_money) if debit_col else 0.0
        credit = df[credit_col].map(coerce_money) if credit_col else 0.0
        df["Amount"] = pd.to_numeric(credit, errors="coerce") - pd.to_numeric(
            debit, errors="coerce"
        )
    else:
        amount_col = _pick_first_present(df, ["Amount", "Transaction Amount"])
        if amount_col is None:
            raise ValueError("No amount columns found.")
        df["Amount"] = pd.to_numeric(df[amount_col].map(coerce_money), errors="coerce")

    balance_col = _pick_first_present(df, ["Running Balance", "Balance"])
    if balance_col:
        df["Running Balance (num)"] = pd.to_numeric(
            df[balance_col].map(coerce_money), errors="coerce"
        )

    desc_col = _pick_first_present(df, ["Description", "Payee", "Memo", "Details"])
    df["Description (clean)"] = df[desc_col].map(_clean_text) if desc_col else ""
    df["Merchant"] = df["Description (clean)"].map(normalize_merchant)

    if "Category" in df.columns:
        df["Category (raw)"] = df["Category"]
    else:
        df["Category (raw)"] = ""

    if category_mapping is None:
        category_mapping = _default_mapping_path_for(source)

    if learn and learn_from:
        _ = learn_mappings(category_mapping, learn_from)

    exact, contains, regex = _load_mapping(category_mapping) if category_mapping else ([], [], [])
    prov_counter = Counter()
    cats = []
    for _, row in df.iterrows():
        c, prov = _apply_mapping(row["Description (clean)"], exact, contains, regex)
        if c:
            prov_counter[prov] += 1
            cats.append(_canonicalize(c))
            continue
        hay = f"{row['Description (clean)']} {_clean_text(row['Category (raw)'])}".strip()
        c, prov = _fallback_keyword_rules(hay)
        if c:
            prov_counter[prov] += 1
            cats.append(c)
            continue
        raw = _clean_text(row["Category (raw)"])
        if raw in ALIASES:
            prov_counter["alias_raw"] += 1
            cats.append(ALIASES[raw])
            continue
        prov_counter["uncategorized"] += 1
        cats.append("Uncategorized")
    df["Category"] = cats

    front = [
        c
        for c in ["Account", "AccountSeq", "Date", "Amount", "Category", "Merchant"]
        if c in df.columns
    ]
    remaining = [c for c in df.columns if c not in front]
    df = df[front + remaining]

    out_csv = source.with_name(source.stem + "_transformed.csv")
    df.to_csv(out_csv, index=False)

    unc = (
        df.loc[df["Category"] == "Uncategorized", ["Merchant", "Description (clean)"]]
        .rename(columns={"Description (clean)": "pattern"})
        .assign(type="exact", category="")
        .value_counts(["Merchant", "pattern"])
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    if not unc.empty:
        out_unc = source.with_name(source.stem + "_uncategorized.csv")
        unc.to_csv(out_unc, index=False)

    if write_parquet:
        out_pq = out_csv.with_suffix(".parquet")
        try:
            df.to_parquet(out_pq, engine="pyarrow", index=False)
        except Exception:
            df.to_parquet(out_pq, engine="fastparquet", index=False)

    if report:
        total = len(df)
        print("\n=== Transform Report ===")
        print(f"Rows: {total}")
        for key in [
            "mapping_exact",
            "mapping_contains",
            "mapping_regex",
            "keyword_rule",
            "alias_rule",
            "alias_raw",
            "uncategorized",
        ]:
            if prov_counter.get(key, 0):
                print(f"{key:>18}: {prov_counter[key]:5d}  ({prov_counter[key]/total:6.1%})")
        top_merchants = df["Merchant"].replace("", pd.NA).dropna().value_counts().head(10)
        if not top_merchants.empty:
            print("\nTop merchants:")
            for name, cnt in top_merchants.items():
                print(f"  {name:<25} {cnt:5d}")
        if not unc.empty:
            print(f"\nUncategorized patterns: {len(unc)} â†’ {out_unc}")
        print(f"Output: {out_csv}")
    return out_csv


def learn_mappings(mapping_path: Path | None, learn_src: Path) -> tuple[int, int, int, int]:
    if mapping_path is None:
        print("[learn] No mapping file path provided; skipping learn step.")
        return (0, 0, 0, 0)
    if not learn_src.exists():
        print(f"[learn] No learn-from file found at: {learn_src}")
        return (0, 0, 0, 0)
    new_df = pd.read_csv(learn_src, dtype=str).fillna("")
    cols = {c.lower() for c in new_df.columns}
    if not {"pattern", "category"}.issubset(cols):
        print(f"[learn] '{learn_src}' must contain 'pattern' and 'category' columns.")
        return (0, 0, 0, 0)

    def getcol(df: pd.DataFrame, name: str):
        mm = {c.lower(): c for c in df.columns}
        return df[mm[name]] if name in mm else None

    patt_col = getcol(new_df, "pattern").map(_clean_text)
    cat_col = getcol(new_df, "category").map(_canonicalize)
    type_col = getcol(new_df, "type")
    if type_col is None:
        type_col = pd.Series(["exact"] * len(new_df))
    else:
        type_col = type_col.str.lower().str.strip().replace("", "exact")
    learned = pd.DataFrame({"type": type_col, "pattern": patt_col, "category": cat_col})
    learned = learned[(learned["pattern"] != "") & (learned["category"] != "Uncategorized")]
    if learned.empty:
        print(f"[learn] No labeled rows (non-empty 'category') found in: {learn_src}")
        return (0, 0, 0, 0)
    if mapping_path.exists():
        base = pd.read_csv(mapping_path, dtype=str).fillna("")
        if not {"type", "pattern", "category"}.issubset(base.columns):
            base = pd.DataFrame(columns=["type", "pattern", "category"])
    else:
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        base = pd.DataFrame(columns=["type", "pattern", "category"])
    base["type"] = base["type"].str.lower().str.strip().replace("", "exact")
    base["pattern"] = base["pattern"].map(_clean_text)
    base["category"] = base["category"].map(_canonicalize)
    base["key"] = base["type"] + "\t" + base["pattern"]
    learned["key"] = learned["type"] + "\t" + learned["pattern"]
    existing = dict(zip(base["key"], base["category"]))
    add_rows = []
    dup = 0
    conf = 0
    for _, r in learned.iterrows():
        key = r["key"]
        cat = r["category"]
        if key in existing:
            if existing[key].lower() == cat.lower():
                dup += 1
            else:
                conf += 1
            continue
        add_rows.append(
            {"type": r["type"], "pattern": r["pattern"], "category": r["category"], "key": key}
        )
    added = len(add_rows)
    if added:
        base = pd.concat([base, pd.DataFrame(add_rows)], ignore_index=True)
    base = base.drop(columns=["key"], errors="ignore").drop_duplicates(
        subset=["type", "pattern"], keep="last"
    )
    base = base.sort_values(["type", "pattern"]).reset_index(drop=True)
    base.to_csv(mapping_path, index=False)
    total = len(base)
    print(
        f"[learn] Added: {added}, duplicates: {dup}, conflicts (skipped): {conf}. Mapping size: {total}."
    )
    print(f"[learn] Mapping updated at: {mapping_path}")
    return (added, dup, conf, total)


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Transform BOA CSV with vendor normalization and category mapping."
    )
    p.add_argument("--source", required=True, help="Path to source CSV to transform.")
    p.add_argument("--category-mapping", help="Path to CategoryMapping.csv (optional).")
    p.add_argument(
        "--learn", action="store_true", help="Merge labeled rows into mapping BEFORE transform."
    )
    p.add_argument("--learn-from", help="CSV to learn from (default: <source>_uncategorized.csv).")
    p.add_argument("--report", action="store_true", help="Print a brief summary report.")
    p.add_argument("--account-id", default="BOA-5670", help="Account designation for new columns.")
    p.add_argument(
        "--parquet",
        action="store_true",
        help="Also write a Parquet file (requires pyarrow or fastparquet).",
    )
    return p


def transform_main(argv=None) -> int:
    """CLI-compatible entry point. Returns process exit code (0 ok)."""
    parser = _build_argparser()
    args = parser.parse_args(argv)
    source = Path(args.source)
    category_mapping = Path(args.category_mapping) if args.category_mapping else None
    learn_from = (
        Path(args.learn_from)
        if args.learn_from
        else source.with_name(source.stem + "_uncategorized.csv")
    )
    try:
        transform(
            source=source,
            category_mapping=category_mapping,
            learn_from=learn_from,
            learn=args.learn,
            report=args.report,
            write_parquet=args.parquet,
            account_id=args.account_id,
        )
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(transform_main())
