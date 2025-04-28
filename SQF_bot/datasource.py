"""
Market-data service.
In SIM mode → generates synthetic prices that gently wander.
In LIVE mode → streams real ticks from Interactive Brokers via ib_insync.
"""
import random, math, time, datetime as dt
from collections import deque

import pandas as pd
from ib_insync import IB, Future, Stock

class DataSource:
    def __init__(self, cfg):
        self.cfg = cfg
        self.mode = cfg["mode"]
        if self.mode == "live":
            self._init_ib()

        # starting synthetic levels (S&P 5 600, SPY 560)
        self.sim_fut, self.sim_spy = 5600.0, 560.0

    # ---------- Live --------------------------------------------------
    def _init_ib(self):
        ib_cfg = self.cfg["ib"]
        self.ib = IB()
        self.ib.connect(ib_cfg["host"], ib_cfg["port"], ib_cfg["client_id"])

        fut_cfg = self.cfg["contracts"]["sqf"]
        self.qspx = Future(
            symbol=fut_cfg["symbol"],
            exchange="CME",
            currency="USD",
            lastTradeDateOrContractMonth=str(fut_cfg["expiry"])
        )
        self.spy = Stock(self.cfg["contracts"]["spy"]["symbol"], "ARCA", "USD")

        self.ib.qualifyContracts(self.qspx, self.spy)
        self.q_fut = self.ib.reqMktData(self.qspx, snapshot=False, regulatorySnapshot=False)
        self.q_spy = self.ib.reqMktData(self.spy, snapshot=False, regulatorySnapshot=False)

    # ---------- Unified tick iterator --------------------------------
    def ticks(self):
        """
        Yields dicts:
        {'ts': pd.Timestamp, 'fut': float, 'spy': float}
        at ~1 second cadence.
        """
        if self.mode == "sim":
            return self._sim_ticks()
        return self._live_ticks()

    def _sim_ticks(self):
        while True:
            # Brownian drift
            self.sim_fut += random.gauss(0, 0.5)
            self.sim_spy = self.sim_fut / 10  # keep 10:1 ratio
            yield {"ts": pd.Timestamp.utcnow(),
                   "fut": round(self.sim_fut, 2),
                   "spy": round(self.sim_spy, 2)}
            time.sleep(1)

    def _live_ticks(self):
        while True:
            self.ib.sleep(1)
            fut_px = self.q_fut.last or self.q_fut.close
            spy_px = self.q_spy.last or self.q_spy.close
            if fut_px and spy_px:
                yield {"ts": pd.Timestamp.utcnow(),
                       "fut": fut_px,
                       "spy": spy_px}
