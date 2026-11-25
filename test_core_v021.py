import unittest
import math

import numpy as np
import pandas as pd

from core_v021 import (
    true_range,
    atr,
    moving_averages,
    rsi,
    macd,
    window_context,
    score_window,
    Registry,
    Rule,
    swings,
)


def make_df(values, highs=None, lows=None):
    idx = pd.date_range("2024-01-01", periods=len(values))
    close = pd.Series(values, index=idx, dtype=float)

    high_values = highs if highs is not None else [value + 1 for value in values]
    low_values = lows if lows is not None else [value - 1 for value in values]

    high = pd.Series(high_values, index=idx, dtype=float)
    low = pd.Series(low_values, index=idx, dtype=float)

    return pd.DataFrame(
        {
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.ones(len(values)),
        },
        index=idx,
    )


class IndicatorTests(unittest.TestCase):
    def test_true_range_uses_previous_close(self):
        df = make_df(
            [10, 11],
            highs=[12, 13],
            lows=[9, 10],
        )

        tr = true_range(df)

        self.assertEqual(tr.iloc[0], 3)
        self.assertEqual(
            tr.iloc[1],
            max(
                3,
                abs(13 - 11),
                abs(10 - 11),
            ),
        )

    def test_atr_simple(self):
        df = make_df(list(range(1, 21)))

        self.assertAlmostEqual(
            atr(df, 14).iloc[-1],
            2.0,
        )

    def test_atr_future_invariance(self):
        df = make_df(list(range(1, 31)))
        as_of = df.index[19]

        before = atr(df, 14, as_of=as_of).loc[as_of]

        changed = df.copy()
        changed.iloc[-1, changed.columns.get_loc("high")] += 100

        after = atr(changed, 14, as_of=as_of).loc[as_of]

        self.assertEqual(before, after)

    def test_ma610_needs_history(self):
        df = make_df(np.ones(100))

        mas = moving_averages(df)

        self.assertTrue(mas[610].isna().all())
        self.assertFalse(mas[5].isna().all())

    def test_ma_future_invariance(self):
        df = make_df(np.arange(1, 101, dtype=float))
        as_of = df.index[49]

        before = moving_averages(df, as_of=as_of)[50].loc[as_of]

        changed = df.copy()
        changed.iloc[-1, changed.columns.get_loc("close")] += 100

        after = moving_averages(changed, as_of=as_of)[50].loc[as_of]

        self.assertEqual(before, after)

    def test_rsi_all_gains(self):
        close = pd.Series(np.arange(1, 31, dtype=float))

        self.assertEqual(rsi(close).iloc[-1], 100)

    def test_rsi_all_losses(self):
        close = pd.Series(np.arange(30, 0, -1, dtype=float))

        self.assertEqual(rsi(close).iloc[-1], 0)

    def test_rsi_flat(self):
        close = pd.Series(np.ones(30))

        self.assertTrue(math.isnan(rsi(close).iloc[-1]))

    def test_macd_known_values(self):
        close = pd.Series([1] * 30, dtype=float)

        line, signal, histogram = macd(close)

        self.assertAlmostEqual(line.iloc[-1], 0)
        self.assertAlmostEqual(signal.iloc[-1], 0)
        self.assertAlmostEqual(histogram.iloc[-1], 0)

    def test_macd_future_invariance(self):
        close = pd.Series(
            np.arange(1, 101, dtype=float),
            index=pd.date_range("2024-01-01", periods=100),
        )
        as_of = close.index[49]

        before = macd(close, as_of=as_of)[0].loc[as_of]

        changed = close.copy()
        changed.iloc[-1] += 100

        after = macd(changed, as_of=as_of)[0].loc[as_of]

        self.assertEqual(before, after)

    def test_window_causal(self):
        df = make_df(np.ones(10))

        history = window_context(
            df,
            df.index[5],
            df.index[4],
            df.index[6],
        )

        self.assertEqual(history.index[-1], df.index[5])

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
        idx = pd.date_range("2024-01-01", periods=4)
        equity = pd.Series(
            [100.0, 200.0, 220.0, 242.0],
            index=idx,
        )

        self.assertAlmostEqual(
            score_window(equity, idx[2], idx[3]),
            0.21,
        )

    def test_rule_registry(self):
        rule = Rule(
            "r1",
            "A",
            True,
            True,
            "v",
            "00:01:02",
            "q",
            "BIST",
            "1D",
        )

        registry = Registry()
        registry.register(rule, "faithful")

        self.assertEqual(
            [item.rule_id for item in registry.for_engine("faithful")],
            ["r1"],
        )

    def test_swing_confirmation(self):
        idx = pd.date_range("2024-01-01", periods=8)

        df = pd.DataFrame(
            {
                "high": [1, 2, 3, 4, 5, 4, 3, 2],
                "low": [0, 1, 2, 3, 4, 3, 2, 1],
            },
            index=idx,
        )

        peak = next(
            swing
            for swing in swings(df, idx[6])
            if swing.formed_at == idx[4]
        )

        self.assertEqual(peak.confirmed_at, idx[6])


if __name__ == "__main__":
    unittest.main()