# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%
from household_spending.boa_transform import transform_main

transform_main(
    [
        "--source",
        r"E:\\path\\to\\your.csv",
        "--category-mapping",
        r"E:\\path\\to\\CategoryMapping.csv",
        "--report",
    ]
)
