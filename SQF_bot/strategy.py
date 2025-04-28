"""
Basis-reversion strategy:
open ±$notional_per_trade when Z-score ≥ ± z_enter,
close when |Z| < z_exit.
"""
from collections import deque
import numpy as np

class Strategy:
    def __init__(self, cfg):
        self.w = cfg["window"]
        self.z_enter = cfg["z_enter"]
        self.z_exit  = cfg["z_exit"]
        self.notional = cfg["notional_per_trade"]
        self.hist = deque(maxlen=self.w)
        self.position = 0   # +1 = long basis (long fut / short SPY); -1 opposite

    # ------------ core -----------------------------------------------
    def on_tick(self, tick):
        basis = tick["fut"] - tick["spy"] * 10  # SPY is 1/10th the fut level
        self.hist.append(basis)

        if len(self.hist) < 30:          # warm-up
            return None

        mu, sigma = np.mean(self.hist), np.std(self.hist)
        if sigma == 0:
            return None
        z = (basis - mu) / sigma

        # decision
        if z >= self.z_enter and self.position != -1:
            self.position = -1
            return {"action": "SHORT_BASIS", "notional": self.notional, "z": z}

        if z <= -self.z_enter and self.position != 1:
            self.position = 1
            return {"action": "LONG_BASIS", "notional": self.notional, "z": z}

        if abs(z) < self.z_exit and self.position != 0:
            self.position = 0
            return {"action": "FLAT", "z": z}

        return None
