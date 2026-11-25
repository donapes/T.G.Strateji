import math
import unittest

import numpy as np
import pandas as pd

from core_v021 import (
    Registry,
    Rule,
    atr,
    macd,
    moving_averages,
    rsi,
    score_window,
    swings,
    true_range,
    window_context,
)


def make_df(values, highs=None, lows=None):
    values = list(values)
    index = pd.date_range("2024-01-01", periods=len(values))

    close = pd.Series(values, index=index, dtype=float)

    high_values = (
        highs
        if highs is not None
        else [value + 1 for value in values]
    )
    low_values = (
        lows
        if lows is not None
        else [value - 1 for value in values]
    )

    return pd.DataFrame(
        {
            "open": close,
            "high": pd.Series(
                high_values,
                index=index,
                dtype=float,
            ),
            "low": pd.Series(
                low_values,
                index=index,
                dtype=float,
            ),
            "close": close,
            "volume": np.ones(len(values)),
        },
        index=index,
    )


class IndicatorTests(unittest.TestCase):
    def test_true_range_uses_previous_close(self):
        df = make_df(
            [10, 11],
            highs=[12, 13],
            lows=[9, 10],
        )

        result = true_range(df)
        previous_close = df["close"].iloc[0]

        self.assertAlmostEqual(result.iloc[0], 3.0)
        self.assertAlmostEqual(
            result.iloc[1],
            max(
                13 - 10,
                abs(13 - previous_close),
                abs(10 - previous_close),
            ),
        )

    def test_atr_simple(self):
        df = make_df(range(1, 21))
        result = atr(df, period=14).iloc[-1]

        self.assertTrue(math.isfinite(result))
        self.assertAlmostEqual(result, 2.0)

    def test_atr_future_invariance(self):
        df = make_df(range(1, 31))
        as_of = df.index[19]

        before = atr(
            df,
            period=14,
            as_of=as_of,
        ).loc[as_of]

        changed = df.copy()
        changed.loc[
            changed.index > as_of,
            "high",
        ] += 1000.0

        after = atr(
            changed,
            period=14,
            as_of=as_of,
        ).loc[as_of]

        self.assertTrue(math.isfinite(before))
        self.assertTrue(math.isfinite(after))
        self.assertAlmostEqual(before, after)

    def test_ma610_needs_history(self):
        df = make_df(np.ones(100))

        averages = moving_averages(df)

        self.assertTrue(averages[610].isna().all())
        self.assertFalse(averages[5].isna().all())

    def test_ma_future_invariance(self):
        df = make_df(np.arange(1, 101, dtype=float))
        as_of = df.index[49]

        before = moving_averages(
            df,
            periods=(50,),
            as_of=as_of,
        )[50].loc[as_of]

        changed = df.copy()
        changed.loc[
            changed.index > as_of,
            "close",
        ] += 1000.0

        after = moving_averages(
            changed,
            periods=(50,),
            as_of=as_of,
        )[50].loc[as_of]

        self.assertTrue(math.isfinite(before))
        self.assertTrue(math.isfinite(after))
        self.assertAlmostEqual(before, 25.5)
        self.assertAlmostEqual(before, after)

    def test_rsi_all_gains(self):
        close = pd.Series(
            np.arange(1, 31, dtype=float),
        )

        self.assertEqual(rsi(close).iloc[-1], 100.0)

    def test_rsi_all_losses(self):
        close = pd.Series(
            np.arange(30, 0, -1, dtype=float),
        )

        self.assertEqual(rsi(close).iloc[-1], 0.0)

    def test_rsi_flat(self):
        close = pd.Series(
            np.ones(30),
            dtype=float,
        )

        self.assertTrue(
            math.isnan(rsi(close).iloc[-1])
        )

    def test_macd_known_values(self):
        close = pd.Series(
            [1.0] * 30,
            dtype=float,
        )

        line, signal, histogram = macd(close)

        self.assertAlmostEqual(line.iloc[-1], 0.0)
        self.assertAlmostEqual(signal.iloc[-1], 0.0)
        self.assertAlmostEqual(histogram.iloc[-1], 0.0)

    def test_macd_future_invariance(self):
        index = pd.date_range(
            "2024-01-01",
            periods=100,
        )
        close = pd.Series(
            np.arange(1, 101, dtype=float),
            index=index,
        )
        as_of = close.index[49]

        before = tuple(
            series.loc[as_of]
            for series in macd(close, as_of=as_of)
        )

        changed = close.copy()
        changed.loc[changed.index > as_of] += 1000.0

        after = tuple(
            series.loc[as_of]
            for series in macd(changed, as_of=as_of)
        )

        for name, before_value, after_value in zip(
            ("line", "signal", "histogram"),
            before,
            after,
        ):
            with self.subTest(component=name):
                self.assertTrue(
                    math.isfinite(before_value)
                )
                self.assertTrue(
                    math.isfinite(after_value)
                )
                self.assertAlmostEqual(
                    before_value,
                    after_value,
                )

    def test_window_causal(self):
        df = make_df(np.ones(10))

        history = window_context(
            df,
            df.index[5],
            df.index[4],
            df.index[6],
        )

        self.assertEqual(
            history.index[-1],
            df.index[5],
        )

    def test_window_outside(self):
        df = make_df(np.ones(10))

        with self.assertRaises(ValueError):
            window_context(
                df,
                df.index[7],
                df.index[4],
                df.index[6],
            )

    def test_score_warmup_excluded(self):
        index = pd.date_range(
            "2024-01-01",
            periods=4,
        )
        equity = pd.Series(
            [100.0, 200.0, 220.0, 242.0],
            index=index,
        )

        self.assertAlmostEqual(
            score_window(
                equity,
                index[2],
                index[3],
            ),
            0.21,
        )

    def test_rule_registry(self):
        rule = Rule(
            rule_id="r1",
            grade="A",
            verified=True,
            allowed=True,
            video="v",
            timestamp="00:01:02",
            quote="q",
            asset="BIST",
            timeframe="1D",
        )

        registry = Registry()
        registry.register(rule, "faithful")

        self.assertEqual(
            [
                item.rule_id
                for item in registry.for_engine("faithful")
            ],
            ["r1"],
        )

    def test_swing_confirmation(self):
        index = pd.date_range(
            "2024-01-01",
            periods=8,
        )

        df = pd.DataFrame(
            {
                "high": [1, 2, 3, 4, 5, 4, 3, 2],
                "low": [0, 1, 2, 3, 4, 3, 2, 1],
            },
            index=index,
        )

        peak = next(
            swing
            for swing in swings(df, index[6])
            if (
                swing.kind == "HIGH"
                and swing.formed_at == index[4]
            )
        )

        self.assertEqual(
            peak.confirmed_at,
            index[6],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
