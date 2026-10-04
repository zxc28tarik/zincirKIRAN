from datetime import date

import pytest

from zincir_kiran.baselines import Horizon
from zincir_kiran.experimental_dataset import (
    ResearchDatasetAuthority,
    default_experimental_factor_dataset_manifest,
    forward_excess_label,
    require_experimental_factor_lab_use,
)


def test_manifest_combines_real_market_universe_and_financial_evidence() -> None:
    manifest = default_experimental_factor_dataset_manifest()
    assert manifest.authority is ResearchDatasetAuthority.EXPERIMENTAL_VERSION_RISK
    assert manifest.historical_cells == 6000
    assert manifest.cells_with_visible_financial_facts == 5633
    assert manifest.production_eligible is False
    assert len(manifest.inputs) == 6


def test_h20_label_uses_exact_twentieth_future_trading_day() -> None:
    dates = tuple(date(2026, 1, day) for day in range(1, 23))
    stock = {day: 100.0 for day in dates}
    market = {day: 100.0 for day in dates}
    stock[dates[20]] = 110.0
    market[dates[20]] = 105.0

    label = forward_excess_label(
        security_id="AAA",
        signal_date=dates[0],
        horizon=Horizon.H20,
        trading_dates=dates,
        stock_closes=stock,
        market_closes=market,
    )
    assert label is not None
    assert label.future_date == dates[20]
    assert label.stock_return == pytest.approx(0.10)
    assert label.market_return == pytest.approx(0.05)
    assert label.excess_return == pytest.approx(0.05)


def test_unmatured_horizon_is_unavailable_not_zero() -> None:
    dates = tuple(date(2026, 1, day) for day in range(1, 22))
    stock = {day: 100.0 for day in dates}
    market = {day: 100.0 for day in dates}
    label = forward_excess_label(
        security_id="AAA",
        signal_date=dates[1],
        horizon=Horizon.H20,
        trading_dates=dates,
        stock_closes=stock,
        market_closes=market,
    )
    assert label is None


def test_missing_future_stock_price_is_unavailable() -> None:
    dates = tuple(date(2026, 1, day) for day in range(1, 23))
    stock = {day: 100.0 for day in dates}
    market = {day: 100.0 for day in dates}
    del stock[dates[20]]
    assert (
        forward_excess_label(
            security_id="AAA",
            signal_date=dates[0],
            horizon=Horizon.H20,
            trading_dates=dates,
            stock_closes=stock,
            market_closes=market,
        )
        is None
    )


def test_unsorted_or_duplicate_calendar_is_rejected() -> None:
    with pytest.raises(ValueError, match="unique and sorted"):
        forward_excess_label(
            security_id="AAA",
            signal_date=date(2026, 1, 1),
            horizon=Horizon.H20,
            trading_dates=(date(2026, 1, 2), date(2026, 1, 1)),
            stock_closes={},
            market_closes={},
        )


def test_dataset_cannot_be_promoted_to_authoritative_research() -> None:
    manifest = default_experimental_factor_dataset_manifest()
    require_experimental_factor_lab_use(
        manifest,
        requested_authority="EXPERIMENTAL_VERSION_RISK",
    )
    with pytest.raises(ValueError, match="cannot be promoted"):
        require_experimental_factor_lab_use(
            manifest,
            requested_authority="AUTHORITATIVE_PIT",
        )
