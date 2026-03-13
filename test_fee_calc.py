import json
import pathlib

import pytest

from fee_calc import (
    FeeCalc,
    FeeCalcError,
    ERROR_INVALID_PARAGRAPH,
    ERROR_INVALID_ZONE,
    ERROR_INVALID_FEE_RANGE,
    ERROR_APPLICABLE_COST_OUT_OF_RANGE,
)


HERE = pathlib.Path(__file__).parent
DATA_PATH = HERE / "data" / "hoai2013.json"


@pytest.fixture(scope="module")
def tables():
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_fee_calc_valid_inputs(tables):
    # paragraph 0 (first), zone 3, mid fee range, mid applicable cost
    feetable = tables["paragraphs"][0]["feetable"]
    low = feetable[0][0]
    high = feetable[-1][0]
    mid_cost = (low + high) / 2

    calc = FeeCalc(
        tables=tables,
        zone=3,
        fee_range=0.5,
        applicable_cost=mid_cost,
        paragraph_index=0,
    )

    assert calc.fee > 0.0
    settings = calc.get_settings()
    assert settings["zone"] == 3
    assert settings["paragraph_index"] == 0


def test_invalid_paragraph_index_raises(tables):
    with pytest.raises(FeeCalcError) as excinfo:
        FeeCalc(
            tables=tables,
            zone=3,
            fee_range=0.5,
            applicable_cost=2000.0,
            paragraph_index=999,  # clearly out of range
        )
    assert excinfo.value.code == ERROR_INVALID_PARAGRAPH


def test_invalid_zone_raises(tables):
    feetable = tables["paragraphs"][0]["feetable"]
    cost = feetable[0][0]

    # zone 0 is below valid range
    with pytest.raises(FeeCalcError) as excinfo:
        FeeCalc(
            tables=tables,
            zone=0,
            fee_range=0.5,
            applicable_cost=cost,
            paragraph_index=0,
        )
    assert excinfo.value.code == ERROR_INVALID_ZONE


def test_invalid_fee_range_raises(tables):
    feetable = tables["paragraphs"][0]["feetable"]
    cost = feetable[0][0]

    with pytest.raises(FeeCalcError) as excinfo:
        FeeCalc(
            tables=tables,
            zone=2,
            fee_range=1.5,  # above 1.0
            applicable_cost=cost,
            paragraph_index=0,
        )
    assert excinfo.value.code == ERROR_INVALID_FEE_RANGE


def test_applicable_cost_out_of_range_raises(tables):
    feetable = tables["paragraphs"][0]["feetable"]
    low = feetable[0][0]
    high = feetable[-1][0]

    below_low = low - 1.0
    above_high = high + 1.0

    with pytest.raises(FeeCalcError) as excinfo_low:
        FeeCalc(
            tables=tables,
            zone=2,
            fee_range=0.5,
            applicable_cost=below_low,
            paragraph_index=0,
        )
    assert excinfo_low.value.code == ERROR_APPLICABLE_COST_OUT_OF_RANGE

    with pytest.raises(FeeCalcError) as excinfo_high:
        FeeCalc(
            tables=tables,
            zone=2,
            fee_range=0.5,
            applicable_cost=above_high,
            paragraph_index=0,
        )
    assert excinfo_high.value.code == ERROR_APPLICABLE_COST_OUT_OF_RANGE


def test_setters_also_validate(tables):
    feetable = tables["paragraphs"][0]["feetable"]
    low = feetable[0][0]

    calc = FeeCalc(
        tables=tables,
        zone=2,
        fee_range=0.5,
        applicable_cost=low,
        paragraph_index=0,
    )

    # invalid fee_range via setter
    with pytest.raises(FeeCalcError) as exc_fee:
        calc.fee_range = -0.1
    assert exc_fee.value.code == ERROR_INVALID_FEE_RANGE

    # invalid zone via setter
    with pytest.raises(FeeCalcError) as exc_zone:
        calc.zone = 0
    assert exc_zone.value.code == ERROR_INVALID_ZONE

    # invalid applicable_cost via setter
    with pytest.raises(FeeCalcError) as exc_cost:
        calc.applicable_cost = low - 1
    assert exc_cost.value.code == ERROR_APPLICABLE_COST_OUT_OF_RANGE

