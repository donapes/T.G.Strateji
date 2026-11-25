from dataclasses import dataclass
import math

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Rule:
    rule_id: str
    grade: str
    verified: bool
    allowed: bool
    video: str
    timestamp: str
    quote: str
    asset: str
    timeframe: str


class Registry:
    def __init__(self):
        self._rules = {}

    def register(self, rule, engine):
        if engine not in ("faithful", "experimental"):
            raise ValueError("unknown engine")

        if rule.grade not in ("A", "B", "C"):
            raise ValueError("unknown grade")

        if not rule.rule_id.strip() or rule.rule_id in self._rules:
            raise ValueError("empty or duplicate rule ID")

        if engine == "faithful":
            source = (
                rule.video,
                rule.timestamp,
                rule.quote,
                rule.asset,
                rule.timeframe,
            )

            if (
                rule.grade == "C"
                or not rule.verified
                or not rule.allowed
                or not all(source_field.strip() for source_field in source)
            ):
                raise ValueError("faithful eligibility failed")

            timestamp_parts = rule.timestamp.split(":")

            if (
                len(timestamp_parts) != 3
                or not all(part.isdigit() for part in timestamp_parts)
                or int(timestamp_parts[1]) >= 60
                or int(timestamp_parts[2]) >= 60
            ):
                raise ValueError("timestamp must be HH:MM:SS")

        self._rules[rule.rule_id] = (engine, rule)

    def for_engine(self, engine):
        return tuple(
            rule
            for rule_engine, rule in self._rules.values()
            if rule_engine == engine
        )


@dataclass(frozen=True)
class Swing:
    kind: str
    price: float
    formed_at: object
    confirmed_at: object


def swings(df, as_of, left=2, right=2):
    if left < 1 or right < 1:
        raise ValueError("left/right must be positive")

    if not df.index.is_monotonic_increasing or not df.index.is_unique:
        raise ValueError("sorted unique index required")

    history = df.loc[:as_of]
    result = []

    for index in range(left, len(history) - right):
        window = history.iloc[index - left:index + right + 1]

        for kind, column, extreme in (
            ("HIGH", "high", max),
            ("LOW", "low", min),
        ):
            values = window[column].tolist()

            if not all(math.isfinite(value) for value in values):
                continue

            value = float(history.iloc[index][column])

            if value == extreme(values) and values.count(value) == 1:
                result.append(
                    Swing(
                        kind,
                        value,
                        history.index[index],
                        history.index[index + right],
                    )
                )

    return result


def true_range(df, as_of=None):
    if as_of is not None:
        df = df.loc[:as_of]

    if len(df) == 0:
        return pd.Series(dtype=float)

    previous_close = df["close"].shift(1)

    true_range_values = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - previous_close).abs(),
            (df["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    true_range_values.iloc[0] = (
        df["high"].iloc[0] - df["low"].iloc[0]
    )

    return true_range_values


def atr(df, period=14, as_of=None):
    if period < 1:
        raise ValueError("period must be positive")

    return true_range(df, as_of).rolling(period).mean()


def moving_averages(
    df,
    periods=(5, 21, 34, 55, 89, 144, 233, 377, 610),
    as_of=None,
):
    if as_of is not None:
        df = df.loc[:as_of]

    close = df["close"]

    return {
        period: close.rolling(period).mean()
        for period in periods
    }


def rsi(close, period=14, as_of=None):
    if period < 2:
        raise ValueError("RSI period must be at least 2")

    if as_of is not None:
        close = close.loc[:as_of]

    delta = close.diff()

    gain = (
        delta.clip(lower=0)
        .ewm(alpha=1 / period, adjust=False)
        .mean()
    )

    loss = (
        (-delta.clip(upper=0))
        .ewm(alpha=1 / period, adjust=False)
        .mean()
    )

    result = pd.Series(index=close.index, dtype=float)

    positive_gain = gain > 0
    zero_loss = loss == 0

    all_gains = positive_gain & zero_loss
    result[all_gains] = 100.0

    normal_case = ~(zero_loss & positive_gain)
    relative_strength = gain / loss.replace(0, np.nan)

    result[normal_case] = 100 - (100 / (1 + relative_strength))

    return result


def macd(close, fast=12, slow=26, signal=9, as_of=None):
    if fast >= slow or signal < 1:
        raise ValueError("invalid MACD parameters")

    if as_of is not None:
        close = close.loc[:as_of]

    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()

    return (
        macd_line,
        signal_line,
        macd_line - signal_line,
    )


def window_context(df, as_of, start, end):
    if not start <= as_of <= end:
        raise ValueError("decision outside scoring window")

    if not df.index.is_monotonic_increasing or not df.index.is_unique:
        raise ValueError("sorted unique index required")

    return df.loc[:as_of].copy()


def score_window(equity, start, end):
    returns = equity.pct_change(fill_method=None)
    selected_returns = returns.loc[start:end]

    if selected_returns.empty or selected_returns.isna().any():
        raise ValueError("missing scoring returns or prior baseline")

    return float((1 + selected_returns).prod() - 1)