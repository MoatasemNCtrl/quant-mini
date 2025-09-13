import pandas as pd
import numpy as np



def compute_factors(data, return_type="series"):

    bars = data.get("bars", {})
    if not bars:
        return {"error": "No bars data found"}

    symbol = next(iter(bars))
    quotes = bars[symbol]

    if not quotes:
        return {"error": "No quotes for symbol"}

    df = pd.DataFrame(quotes).sort_values("t")
    # ensure time index (and keep the name 't' for later reset)
    df["t"] = pd.to_datetime(df["t"])
    df = df.set_index("t")

    df = df.rename(columns={"o":"open","h":"high","l":"low","c":"close","v":"volume"})

    # core returns
    df["return_pct_1d"] = df["close"].pct_change()
    df["log_return_1d"]   = np.log(df["close"] / df["close"].shift(1))

    # moving avgs
    df["sma_5"]  = df["close"].rolling(window=5,  min_periods=5).mean()
    df["sma_20"] = df["close"].rolling(window=20, min_periods=20).mean()

    # EMAs
    df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()

    # rolling vol (needs 20 returns)
    df["vol_20"] = df["log_return_1d"].rolling(window=20, min_periods=20).std() * np.sqrt(252)

    # drawdown & cum return
    df["cum_max"] = df["close"].cummax()
    df["drawdown"] = df["close"] / df["cum_max"] - 1
    df["max_drawdown"] = df["drawdown"].cummin()
    df["cum_return"] = (1 + df["return_pct_1d"]).cumprod() - 1

    # choose only columns that are feasible for the available history
    n = len(df)
    available = ["open","high","low","close","volume",
                 "return_pct_1d","log_return_1d","drawdown","cum_return"]

    if n >= 5:   available.append("sma_5")
    # ema_12 is defined from start, but it’s unstable for very few points; include from 12 bars
    if n >= 12:  available.append("ema_12")
    if n >= 20:  available += ["sma_20","vol_20"]
    if n >= 26:  available.append("ema_26")

    if return_type == "latest":
        latest = df[available].iloc[-1]
        d = latest.where(pd.notnull(latest), None).to_dict()
        # cast NumPy types to plain Python
        return {k: (float(v) if isinstance(v, (np.floating,)) else v) for k, v in d.items()}

    # series
    out = df[available].reset_index()
    out = out.where(pd.notnull(out), None)   # NaN -> None for JSON
    out["t"] = out["t"].astype(str)

    recs = out.to_dict(orient="records")
    # cast NumPy scalars for safety
    cleaned = []
    for row in recs:
        cleaned.append({k: (float(v) if isinstance(v, (np.floating,)) else v) for k, v in row.items()})
    return cleaned