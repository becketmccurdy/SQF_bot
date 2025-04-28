"""
Main event-loop – 60 second cadence for clarity.
"""
import time, logging, yaml

from datasource import DataSource
from strategy import Strategy
from portfolio import Portfolio
from execution import Executor
from risk import Risk

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("BOT")

def load_cfg():
    with open("config.yaml") as fh:
        return yaml.safe_load(fh)

def main():
    cfg = load_cfg()
    ds   = DataSource(cfg)
    strat= Strategy(cfg)
    port = Portfolio()
    risk = Risk(cfg)
    exe  = Executor(cfg, getattr(ds, "ib", None))

    start_equity = port.equity
    for tick in ds.ticks():
        decision = strat.on_tick(tick)

        # mark portfolio
        eq = port.mark(tick["fut"], tick["spy"])
        log.info(f"Tick F {tick['fut']:.2f}  S {tick['spy']:.2f}  Eq {eq:.2f}")

        if decision:
            action = decision["action"]
            notional = decision.get("notional", 0)
            log.info(f"Signal → {action}  Z={decision['z']:.2f}")

            # translate abstract action to legs
            if action == "LONG_BASIS":
                fut_qty = +notional         # $1 / pt notional
                spy_qty = -notional / 10    # SPY ~ 1/10th idx
            elif action == "SHORT_BASIS":
                fut_qty = -notional
                spy_qty = +notional / 10
            else:  # FLAT
                fut_qty = -port.fut_qty
                spy_qty = -port.spy_qty

            # risk check
            fut_val = (port.fut_qty + fut_qty) * tick["fut"]
            spy_val = (port.spy_qty + spy_qty) * tick["spy"]
            if not risk.check_leverage(eq, fut_val, spy_val):
                log.warning("Leverage cap hit – order skipped")
                continue

            # PLACE orders
            if fut_qty != 0:
                exe.place("FUT", "BUY" if fut_qty > 0 else "SELL",
                          abs(int(fut_qty)))
                port.fill("FUT", "BUY" if fut_qty > 0 else "SELL",
                          abs(int(fut_qty)), tick["fut"])
            if spy_qty != 0:
                exe.place("SPY", "BUY" if spy_qty > 0 else "SELL",
                          abs(int(spy_qty)))
                port.fill("SPY", "BUY" if spy_qty > 0 else "SELL",
                          abs(int(spy_qty)), tick["spy"])

            log.info(f"Post-trade equity {port.equity:.2f}")

        # stop-loss
        if risk.hit_stop(start_equity, eq):
            log.error("STOP-LOSS triggered – flattening & exiting.")
            break

        time.sleep(60)

if __name__ == "__main__":
    main()
