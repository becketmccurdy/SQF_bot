"""
Very thin layer: sim = instant fills at mid-price;
live = market orders via IBKR paper account.
"""
from ib_insync import MarketOrder

class Executor:
    def __init__(self, cfg, ib=None):
        self.mode = cfg["mode"]
        self.ib = ib

    # ---- wrappers ----------------------------------------------------
    def place(self, contract, action, qty):
        if self.mode == "sim":
            # caller passes price separately for book-keeping
            return True
        # live
        ord = MarketOrder(action, qty)
        trade = self.ib.placeOrder(contract, ord)
        trade.waitUntilFilled()
        return trade
