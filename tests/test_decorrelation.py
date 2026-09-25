import math

import pytest

from zincir_kiran.decorrelation import (
    CorrelationMethod,
    FactorPoint,
    pairwise_factor_correlation,
)


def test_pairwise_correlation_aligns_by_common_key_not_input_order() -> None:
    left = [
        FactorPoint("C", 3.0),
        FactorPoint("A", 1.0),
        FactorPoint("B", 2.0),
    ]
    right = [
        FactorPoint("B", 20.0),
        FactorPoint("C", 30.0),
        FactorPoint("A", 10.0),
    ]

    result = pairwise_factor_correlation(
        left,
        right,
        minimum_overlap=3,
        method=CorrelationMethod.PEARSON,
    )

    assert result.overlap_count == 3
    assert result.correlation == pytest.approx(1.0)


def test_missing_and_non_finite_values_are_excluded_with_explicit_overlap() -> None:
    left = [
        FactorPoint("A", 1.0),
        FactorPoint("B", None),
        FactorPoint("C", 3.0),
        FactorPoint("D", math.inf),
    ]
    right = [
        FactorPoint("A", 10.0),
        FactorPoint("B", 20.0),
        FactorPoint("C", 30.0),
        FactorPoint("D", 40.0),
    ]

    result = pairwise_factor_correlation(
        left,
        right,
        minimum_overlap=2,
        method=CorrelationMethod.PEARSON,
    )

    assert result.overlap_count == 2
    assert result.left_count == 4
    assert result.right_count == 4
    assert result.correlation == pytest.approx(1.0)


def test_insufficient_overlap_returns_unknown_not_zero() -> None:
    left = [FactorPoint("A", 1.0), FactorPoint("B", 2.0)]
    right = [FactorPoint("A", 10.0), FactorPoint("B", None)]

    result = pairwise_factor_correlation(
        left,
        right,
        minimum_overlap=2,
        method=CorrelationMethod.PEARSON,
    )

    assert result.overlap_count == 1
    assert result.has_sufficient_overlap is False
    assert result.correlation is None


def test_minimum_overlap_is_caller_supplied_not_hidden() -> None:
    left = [FactorPoint("A", 1.0), FactorPoint("B", 2.0), FactorPoint("C", 3.0)]
    right = [FactorPoint("A", 3.0), FactorPoint("B", 2.0), FactorPoint("C", 1.0)]

    accepted = pairwise_factor_correlation(
        left,
        right,
        minimum_overlap=3,
        method=CorrelationMethod.SPEARMAN,
    )
    rejected = pairwise_factor_correlation(
        left,
        right,
        minimum_overlap=4,
        method=CorrelationMethod.SPEARMAN,
    )

    assert accepted.correlation == pytest.approx(-1.0)
    assert rejected.correlation is None


def test_constant_vector_returns_unknown_correlation() -> None:
    left = [FactorPoint("A", 1.0), FactorPoint("B", 1.0), FactorPoint("C", 1.0)]
    right = [FactorPoint("A", 1.0), FactorPoint("B", 2.0), FactorPoint("C", 3.0)]

    result = pairwise_factor_correlation(
        left,
        right,
        minimum_overlap=3,
        method=CorrelationMethod.PEARSON,
    )

    assert result.overlap_count == 3
    assert result.correlation is None


def test_duplicate_observation_key_is_rejected() -> None:
    left = [FactorPoint("A", 1.0), FactorPoint("A", 2.0)]
    right = [FactorPoint("A", 1.0), FactorPoint("B", 2.0)]

    with pytest.raises(ValueError, match="duplicate left observation_key"):
        pairwise_factor_correlation(
            left,
            right,
            minimum_overlap=2,
            method=CorrelationMethod.PEARSON,
        )


def test_minimum_overlap_below_two_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least 2"):
        pairwise_factor_correlation(
            [FactorPoint("A", 1.0)],
            [FactorPoint("A", 2.0)],
            minimum_overlap=1,
            method=CorrelationMethod.PEARSON,
        )
