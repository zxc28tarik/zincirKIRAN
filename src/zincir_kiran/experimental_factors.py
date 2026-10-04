"""First experimental real-data factor materialization primitives.

Financial factors are intentionally limited to NONFIN/HOLDING semantic profiles.
BANK, INSURANCE and FINANCIAL companies require separate specialist definitions.
All outputs remain EXPERIMENTAL_VERSION_RISK.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from statistics import stdev


class FactorDirection(StrEnum):
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    LOWER_IS_BETTER = "LOWER_IS_BETTER"


@dataclass(frozen=True)
class YtdFlow:
    field: str
    period_start: date
    period_end: date
    value: float

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise ValueError("field is required")
        if self.period_start > self.period_end:
            raise ValueError("period_start cannot follow period_end")
        if not math.isfinite(self.value):
            raise ValueError("YTD value must be finite")


@dataclass(frozen=True)
class QuarterFlow:
    field: str
    period_start: date
    period_end: date
    value: float


def derive_quarter_flow(
    current_ytd: YtdFlow,
    previous_ytd: YtdFlow | None,
) -> QuarterFlow:
    """Convert YTD to a discrete quarter without inventing period alignment."""
    if previous_ytd is None:
        return QuarterFlow(
            field=current_ytd.field,
            period_start=current_ytd.period_start,
            period_end=current_ytd.period_end,
            value=current_ytd.value,
        )
    if current_ytd.field != previous_ytd.field:
        raise ValueError("YTD fields do not match")
    if current_ytd.period_start != previous_ytd.period_start:
        raise ValueError("YTD period starts do not match")
    if previous_ytd.period_end >= current_ytd.period_end:
        raise ValueError("previous YTD period must end before current YTD period")
    return QuarterFlow(
        field=current_ytd.field,
        period_start=previous_ytd.period_end,
        period_end=current_ytd.period_end,
        value=current_ytd.value - previous_ytd.value,
    )


def trailing_four_quarter_sum(quarters: tuple[QuarterFlow, ...]) -> float:
    if len(quarters) != 4:
        raise ValueError("TTM requires exactly four explicit quarter flows")
    ordered = tuple(sorted(quarters, key=lambda item: item.period_end))
    if ordered != quarters:
        raise ValueError("quarter flows must be chronologically sorted")
    fields = {item.field for item in quarters}
    if len(fields) != 1:
        raise ValueError("TTM quarter fields must match")
    ends = [item.period_end for item in quarters]
    if len(set(ends)) != 4:
        raise ValueError("TTM quarter period_end values must be unique")
    total = sum(item.value for item in quarters)
    if not math.isfinite(total):
        raise ValueError("TTM value must be finite")
    return total


@dataclass(frozen=True)
class NonfinFactorInputs:
    sector_family: str
    assets_now: float
    assets_year_ago: float
    gross_profit_ttm: float
    operating_profit_ttm: float
    net_income_ttm: float
    cfo_ttm: float
    capex_ttm: float
    revenue_ttm: float
    gross_profit_ttm_year_ago: float | None = None
    operating_profit_ttm_year_ago: float | None = None
    revenue_ttm_year_ago: float | None = None

    def __post_init__(self) -> None:
        if self.sector_family not in {"NONFIN", "HOLDING"}:
            raise ValueError("first financial factor set applies only to NONFIN/HOLDING")
        for name in (
            "assets_now",
            "assets_year_ago",
            "gross_profit_ttm",
            "operating_profit_ttm",
            "net_income_ttm",
            "cfo_ttm",
            "capex_ttm",
            "revenue_ttm",
        ):
            value = getattr(self, name)
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.assets_now <= 0 or self.assets_year_ago <= 0:
            raise ValueError("asset values must be positive")
        for name in (
            "gross_profit_ttm_year_ago",
            "operating_profit_ttm_year_ago",
            "revenue_ttm_year_ago",
        ):
            value = getattr(self, name)
            if value is not None and not math.isfinite(value):
                raise ValueError(f"{name} must be finite when supplied")


@dataclass(frozen=True)
class FactorValue:
    factor_id: str
    value: float | None
    direction: FactorDirection
    authority: str = "EXPERIMENTAL_VERSION_RISK"
    unavailable_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.factor_id.strip():
            raise ValueError("factor_id is required")
        if self.value is not None and not math.isfinite(self.value):
            raise ValueError("factor value must be finite when supplied")
        if (self.value is None) != (self.unavailable_reason is not None):
            raise ValueError("unavailable factor must carry exactly one reason")


def _ratio(
    factor_id: str,
    numerator: float,
    denominator: float,
    direction: FactorDirection,
) -> FactorValue:
    if denominator == 0:
        return FactorValue(
            factor_id=factor_id,
            value=None,
            direction=direction,
            unavailable_reason="ZERO_DENOMINATOR",
        )
    return FactorValue(
        factor_id=factor_id,
        value=numerator / denominator,
        direction=direction,
    )


def materialize_nonfin_factors(inputs: NonfinFactorInputs) -> tuple[FactorValue, ...]:
    average_assets = (inputs.assets_now + inputs.assets_year_ago) / 2.0
    factors: list[FactorValue] = [
        _ratio(
            "gross_profitability",
            inputs.gross_profit_ttm,
            average_assets,
            FactorDirection.HIGHER_IS_BETTER,
        ),
        _ratio(
            "roa",
            inputs.net_income_ttm,
            average_assets,
            FactorDirection.HIGHER_IS_BETTER,
        ),
        _ratio(
            "operating_profitability",
            inputs.operating_profit_ttm,
            average_assets,
            FactorDirection.HIGHER_IS_BETTER,
        ),
        _ratio(
            "cfo_to_assets",
            inputs.cfo_ttm,
            average_assets,
            FactorDirection.HIGHER_IS_BETTER,
        ),
        _ratio(
            "accruals",
            inputs.net_income_ttm - inputs.cfo_ttm,
            average_assets,
            FactorDirection.LOWER_IS_BETTER,
        ),
        FactorValue(
            factor_id="asset_growth",
            value=inputs.assets_now / inputs.assets_year_ago - 1.0,
            direction=FactorDirection.LOWER_IS_BETTER,
        ),
        _ratio(
            "gross_margin",
            inputs.gross_profit_ttm,
            inputs.revenue_ttm,
            FactorDirection.HIGHER_IS_BETTER,
        ),
        _ratio(
            "operating_margin",
            inputs.operating_profit_ttm,
            inputs.revenue_ttm,
            FactorDirection.HIGHER_IS_BETTER,
        ),
        _ratio(
            "capex_to_assets",
            inputs.capex_ttm,
            average_assets,
            FactorDirection.LOWER_IS_BETTER,
        ),
    ]

    if (
        inputs.gross_profit_ttm_year_ago is None
        or inputs.revenue_ttm_year_ago is None
        or inputs.revenue_ttm == 0
        or inputs.revenue_ttm_year_ago == 0
    ):
        factors.append(
            FactorValue(
                factor_id="gross_margin_acceleration",
                value=None,
                direction=FactorDirection.HIGHER_IS_BETTER,
                unavailable_reason="PRIOR_TTM_MARGIN_INPUT_UNAVAILABLE",
            )
        )
    else:
        current_margin = inputs.gross_profit_ttm / inputs.revenue_ttm
        prior_margin = inputs.gross_profit_ttm_year_ago / inputs.revenue_ttm_year_ago
        factors.append(
            FactorValue(
                factor_id="gross_margin_acceleration",
                value=current_margin - prior_margin,
                direction=FactorDirection.HIGHER_IS_BETTER,
            )
        )

    if (
        inputs.operating_profit_ttm_year_ago is None
        or inputs.revenue_ttm_year_ago is None
        or inputs.revenue_ttm == 0
        or inputs.revenue_ttm_year_ago == 0
    ):
        factors.append(
            FactorValue(
                factor_id="operating_margin_acceleration",
                value=None,
                direction=FactorDirection.HIGHER_IS_BETTER,
                unavailable_reason="PRIOR_TTM_MARGIN_INPUT_UNAVAILABLE",
            )
        )
    else:
        current_margin = inputs.operating_profit_ttm / inputs.revenue_ttm
        prior_margin = inputs.operating_profit_ttm_year_ago / inputs.revenue_ttm_year_ago
        factors.append(
            FactorValue(
                factor_id="operating_margin_acceleration",
                value=current_margin - prior_margin,
                direction=FactorDirection.HIGHER_IS_BETTER,
            )
        )

    return tuple(sorted(factors, key=lambda item: item.factor_id))


@dataclass(frozen=True)
class DailyMarketObservation:
    trade_date: date
    close: float
    volume: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.close) or self.close <= 0:
            raise ValueError("close must be positive and finite")
        if not math.isfinite(self.volume) or self.volume < 0:
            raise ValueError("volume must be finite and non-negative")


def _ordered_market(rows: tuple[DailyMarketObservation, ...]) -> tuple[DailyMarketObservation, ...]:
    ordered = tuple(sorted(rows, key=lambda item: item.trade_date))
    if ordered != rows:
        raise ValueError("market observations must be chronologically sorted")
    if len({item.trade_date for item in rows}) != len(rows):
        raise ValueError("market observation dates must be unique")
    return rows


def _past_return(
    rows: tuple[DailyMarketObservation, ...],
    *,
    start_offset: int,
    end_offset: int,
) -> float | None:
    if len(rows) <= start_offset:
        return None
    start = rows[-1 - start_offset].close
    end = rows[-1 - end_offset].close
    return end / start - 1.0


def materialize_market_factors(
    rows: tuple[DailyMarketObservation, ...],
) -> tuple[FactorValue, ...]:
    rows = _ordered_market(rows)
    if not rows:
        raise ValueError("market observations are required")

    momentum_12_1 = _past_return(rows, start_offset=252, end_offset=21)
    momentum_6_1 = _past_return(rows, start_offset=126, end_offset=21)

    high_52 = None
    if len(rows) >= 252:
        window = rows[-252:]
        max_close = max(item.close for item in window)
        high_52 = rows[-1].close / max_close

    volatility = None
    amihud = None
    if len(rows) >= 64:
        window = rows[-64:]
        returns = [
            window[index].close / window[index - 1].close - 1.0
            for index in range(1, len(window))
        ]
        volatility = stdev(returns)
        illiquidity = []
        for index, ret in enumerate(returns, start=1):
            traded_value = window[index].close * window[index].volume
            if traded_value > 0:
                illiquidity.append(abs(ret) / traded_value)
        if illiquidity:
            amihud = sum(illiquidity) / len(illiquidity)

    values = (
        FactorValue(
            "momentum_12_1",
            momentum_12_1,
            FactorDirection.HIGHER_IS_BETTER,
            unavailable_reason=None if momentum_12_1 is not None else "INSUFFICIENT_HISTORY",
        ),
        FactorValue(
            "momentum_6_1",
            momentum_6_1,
            FactorDirection.HIGHER_IS_BETTER,
            unavailable_reason=None if momentum_6_1 is not None else "INSUFFICIENT_HISTORY",
        ),
        FactorValue(
            "high_52_proximity",
            high_52,
            FactorDirection.HIGHER_IS_BETTER,
            unavailable_reason=None if high_52 is not None else "INSUFFICIENT_HISTORY",
        ),
        FactorValue(
            "realized_volatility_63d",
            volatility,
            FactorDirection.LOWER_IS_BETTER,
            unavailable_reason=None if volatility is not None else "INSUFFICIENT_HISTORY",
        ),
        FactorValue(
            "amihud_63d",
            amihud,
            FactorDirection.LOWER_IS_BETTER,
            unavailable_reason=None if amihud is not None else "NO_POSITIVE_TRADED_VALUE",
        ),
    )
    return tuple(sorted(values, key=lambda item: item.factor_id))
