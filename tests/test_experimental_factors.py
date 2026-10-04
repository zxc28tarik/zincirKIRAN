from datetime import date, timedelta

import pytest

from zincir_kiran.experimental_factors import (
    DailyMarketObservation,
    FactorDirection,
    NonfinFactorInputs,
    YtdFlow,
    derive_quarter_flow,
    materialize_market_factors,
    materialize_nonfin_factors,
    trailing_four_quarter_sum,
)


def test_ytd_difference_derives_discrete_quarter() -> None:
    start = date(2025, 1, 1)
    q1 = YtdFlow("REVENUE", start, date(2025, 3, 31), 100.0)
    q2_ytd = YtdFlow("REVENUE", start, date(2025, 6, 30), 230.0)
    q2 = derive_quarter_flow(q2_ytd, q1)
    assert q2.value == pytest.approx(130.0)


def test_ytd_period_start_mismatch_is_rejected() -> None:
    previous = YtdFlow("REVENUE", date(2024, 1, 1), date(2024, 9, 30), 300.0)
    current = YtdFlow("REVENUE", date(2025, 1, 1), date(2025, 12, 31), 500.0)
    with pytest.raises(ValueError, match="period starts"):
        derive_quarter_flow(current, previous)


def test_ttm_requires_four_explicit_quarters() -> None:
    start = date(2025, 1, 1)
    q1 = derive_quarter_flow(YtdFlow("NET_INCOME", start, date(2025, 3, 31), 10.0), None)
    q2 = derive_quarter_flow(
        YtdFlow("NET_INCOME", start, date(2025, 6, 30), 25.0),
        YtdFlow("NET_INCOME", start, date(2025, 3, 31), 10.0),
    )
    q3 = derive_quarter_flow(
        YtdFlow("NET_INCOME", start, date(2025, 9, 30), 45.0),
        YtdFlow("NET_INCOME", start, date(2025, 6, 30), 25.0),
    )
    q4 = derive_quarter_flow(
        YtdFlow("NET_INCOME", start, date(2025, 12, 31), 70.0),
        YtdFlow("NET_INCOME", start, date(2025, 9, 30), 45.0),
    )
    assert trailing_four_quarter_sum((q1, q2, q3, q4)) == pytest.approx(70.0)
    with pytest.raises(ValueError, match="exactly four"):
        trailing_four_quarter_sum((q1, q2, q3))


def test_nonfin_factor_values_and_directions() -> None:
    factors = {
        row.factor_id: row
        for row in materialize_nonfin_factors(
            NonfinFactorInputs(
                sector_family="NONFIN",
                assets_now=1200.0,
                assets_year_ago=1000.0,
                gross_profit_ttm=330.0,
                operating_profit_ttm=220.0,
                net_income_ttm=165.0,
                cfo_ttm=150.0,
                capex_ttm=100.0,
                revenue_ttm=1100.0,
                gross_profit_ttm_year_ago=250.0,
                operating_profit_ttm_year_ago=160.0,
                revenue_ttm_year_ago=1000.0,
            )
        )
    }
    assert factors["gross_profitability"].value == pytest.approx(0.30)
    assert factors["roa"].value == pytest.approx(0.15)
    assert factors["asset_growth"].value == pytest.approx(0.20)
    assert factors["accruals"].direction is FactorDirection.LOWER_IS_BETTER
    assert factors["gross_margin_acceleration"].value == pytest.approx(0.05)
    assert factors["operating_margin_acceleration"].value == pytest.approx(0.04)


def test_specialist_financial_sector_cannot_use_nonfin_formula() -> None:
    with pytest.raises(ValueError, match="NONFIN/HOLDING"):
        NonfinFactorInputs(
            sector_family="BANK",
            assets_now=1200.0,
            assets_year_ago=1000.0,
            gross_profit_ttm=330.0,
            operating_profit_ttm=220.0,
            net_income_ttm=165.0,
            cfo_ttm=150.0,
            capex_ttm=100.0,
            revenue_ttm=1100.0,
        )


def _market_rows(count: int) -> tuple[DailyMarketObservation, ...]:
    start = date(2025, 1, 1)
    return tuple(
        DailyMarketObservation(
            trade_date=start + timedelta(days=index),
            close=100.0 + index,
            volume=1_000_000.0 + index,
        )
        for index in range(count)
    )


def test_market_factors_use_trading_positions() -> None:
    rows = _market_rows(253)
    factors = {row.factor_id: row for row in materialize_market_factors(rows)}
    expected_12_1 = rows[-22].close / rows[0].close - 1.0
    expected_6_1 = rows[-22].close / rows[-127].close - 1.0
    assert factors["momentum_12_1"].value == pytest.approx(expected_12_1)
    assert factors["momentum_6_1"].value == pytest.approx(expected_6_1)
    assert factors["high_52_proximity"].value == pytest.approx(1.0)
    assert factors["realized_volatility_63d"].value is not None
    assert factors["amihud_63d"].value is not None


def test_short_market_history_returns_explicit_unavailability() -> None:
    factors = {row.factor_id: row for row in materialize_market_factors(_market_rows(30))}
    assert factors["momentum_12_1"].value is None
    assert factors["momentum_12_1"].unavailable_reason == "INSUFFICIENT_HISTORY"
    assert factors["realized_volatility_63d"].value is None


def test_missing_prior_margin_inputs_are_unavailable_not_zero() -> None:
    factors = {
        row.factor_id: row
        for row in materialize_nonfin_factors(
            NonfinFactorInputs(
                sector_family="NONFIN",
                assets_now=1200.0,
                assets_year_ago=1000.0,
                gross_profit_ttm=330.0,
                operating_profit_ttm=220.0,
                net_income_ttm=165.0,
                cfo_ttm=150.0,
                capex_ttm=100.0,
                revenue_ttm=1100.0,
            )
        )
    }
    assert factors["gross_margin_acceleration"].value is None
    assert factors["gross_margin_acceleration"].unavailable_reason is not None
