import pandas as pd

from household_spending.boa_transform import coerce_money, normalize_merchant


def test_coerce_money_basic():
    assert coerce_money("$1,234.56") == 1234.56
    assert coerce_money("(45.10)") == -45.10
    assert coerce_money("") == 0.0
    assert pd.isna(coerce_money("not-a-number"))


def test_normalize_merchant_simple():
    assert normalize_merchant("STARBUCKS STORE #1234  BOSTON MA".lower()) == "Starbucks"
    assert normalize_merchant("AMZN Mktp US*2H3K  SEATTLE WA".lower()) == "Amazon"
