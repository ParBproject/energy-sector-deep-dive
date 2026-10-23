import pandas as pd

from src.data import edgar

PAYLOAD = {
    "cik": 34088,
    "facts": {
        "us-gaap": {
            "NetIncomeLoss": {
                "units": {
                    "USD": [
                        # FY2019 10-K: period ends 2019-12-31, but only public on 2020-02-26
                        {
                            "start": "2019-01-01",
                            "end": "2019-12-31",
                            "val": 100,
                            "fy": 2019,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2020-02-26",
                            "accn": "a",
                        },
                        # restated in the FY2020 10-K a year later
                        {
                            "start": "2019-01-01",
                            "end": "2019-12-31",
                            "val": 90,
                            "fy": 2020,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2021-02-24",
                            "accn": "b",
                        },
                        {
                            "start": "2019-01-01",
                            "end": "2019-12-31",
                            "val": 1,
                            "form": "8-K",
                            "filed": "2020-01-31",
                            "end_": None,
                        },
                    ]
                }
            }
        }
    },
}


def facts():
    return edgar.flatten_facts(PAYLOAD, "XOM")


def test_flatten_keeps_filed_and_end_and_drops_non_periodic_forms():
    f = facts()
    assert {"filed", "end"} <= set(f.columns)
    assert set(f["form"]) == {"10-K"}


def test_as_of_uses_filing_date_not_period_end():
    # On 2020-01-15 the period has ended but nothing has been filed: nothing is known.
    assert edgar.as_of(facts(), "2020-01-15").empty
    # After the original filing the first-reported value is used ...
    assert edgar.as_of(facts(), "2020-03-01")["value"].tolist() == [100]
    # ... and the restatement only appears once it was filed.
    assert edgar.as_of(facts(), "2021-03-01")["value"].tolist() == [90]


def test_as_of_would_differ_if_period_end_were_used():
    f = facts()
    leaky = f[pd.to_datetime(f["end"]) <= "2020-01-15"]
    assert not leaky.empty  # the naive filter leaks data that as_of correctly hides
