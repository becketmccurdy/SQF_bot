"""
Simple risk-manager: caps gross leverage & enforces stop-loss.
"""
class Risk:
    def __init__(self, cfg):
        self.cap = cfg["max_gross_leverage"]
        self.stop = cfg["stop_loss_pct"]

    def check_leverage(self, equity, fut_notional, spy_notional):
        gross = abs(fut_notional) + abs(spy_notional)
        return gross <= self.cap * equity

    def hit_stop(self, start_eq, now_eq):
        return (start_eq - now_eq) / start_eq >= self.stop
