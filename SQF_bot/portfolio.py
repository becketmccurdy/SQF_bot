"""
Tracks positions & P/L in memory (USD).
"""
class Portfolio:
    def __init__(self):
        self.fut_qty = 0   # +1 qty = $1 × fut_index notional
        self.spy_qty = 0   # +1 qty = 1 share of SPY
        self.cash = 0
        self.equity = 10_000  # start demo equity

    # ------------- order fills ---------------------------------------
    def fill(self, contract, action, qty, price):
        mult = 1 if action in ("BUY", "COVER") else -1
        if contract == "FUT":
            self.fut_qty += mult * qty
            self.cash -= mult * qty * price
        else:  # SPY
            self.spy_qty += mult * qty
            self.cash -= mult * qty * price

    # ------------- mark-to-market ------------------------------------
    def mark(self, fut_px, spy_px):
        fut_val = self.fut_qty * fut_px
        spy_val = self.spy_qty * spy_px
        self.equity = self.cash + fut_val + spy_val
        return self.equity
