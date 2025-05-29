#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
btc_client.py  –  minimal reusable console client for BTC/USDT
──────────────────────────────────────────────────────────────
• Choose TESTNET or MAINNET interactively.
• API keys & endpoints are pulled from a .env file.
• Helper functions return raw numeric values (no strings),
  so trading algorithms can simply `import btc_client as bc`.

Available shell commands
  help       show commands
  price      current BTC price (float USDT)
  balance    two floats: <USDT> <BTC>
  buy        buy BTC with USDT (see restrictions)
  sell       sell BTC for USDT (see restrictions)
  imbalance  show USDT minus BTC-in-USDT value (rebalance helper)
  fee        show current taker fee (%) and update internal var
  rebalance  makes USDT ≈ BTC value, fee-aware
  mid <N>    mean close price of last N minutes (N ≥ 1)
  quit/exit  leave program
"""

from __future__ import annotations
import os, sys, time, platform
from decimal import Decimal
from dotenv import load_dotenv
from binance.spot import Spot as Client
from binance.error import ClientError
import statistics

TAKER_FEE = 0.001  # default 0.1%

CLEAR = "cls" if platform.system() == "Windows" else "clear"
cls = lambda: os.system(CLEAR)

def choose_mode() -> str:
    while True:
        m = input("Select network [test / live] > ").strip().lower()
        if m in ("test", "live"):
            return m
        print("Type exactly 'test' or 'live'")

MODE = choose_mode()

# ── load env vars ------------------------------------------------------
load_dotenv()
if MODE == "test":
    API_KEY    = os.getenv("BINANCE_TEST_KEY")
    API_SECRET = os.getenv("BINANCE_TEST_SECRET")
    BASE_URL   = os.getenv("BINANCE_TEST_URL", "https://testnet.binance.vision")
else:
    API_KEY    = os.getenv("BINANCE_KEY")
    API_SECRET = os.getenv("BINANCE_SECRET")
    BASE_URL   = os.getenv("BINANCE_URL", "https://api.binance.com")

if not API_KEY or not API_SECRET:
    sys.exit("API keys missing – fill .env")

SYMBOL = "BTCUSDT"

# ── Safe Binance client (auto clock sync) ------------------------------
class Safe(Client):
    def __init__(s,*a,**k):
        super().__init__(*a,**k)
        s.off = 0
        s._sync()
    def _sync(s):
        s.off = super().time()["serverTime"] - int(time.time()*1000)
    def call(s, fn, **p):
        p |= {"timestamp": int(time.time()*1000) + s.off, "recvWindow": 3000}
        try:
            return fn(**p)
        except ClientError as e:
            if e.error_code == -1021:
                s._sync()
                return fn(**p)
            raise

cli = Safe(API_KEY, API_SECRET, base_url=BASE_URL)

# ── exchange restrictions for SYMBOL -----------------------------------
def get_symbol_filters():
    info = cli.exchange_info(symbol=SYMBOL)["symbols"][0]["filters"]
    lot  = next(x for x in info if x["filterType"]=="LOT_SIZE")
    notnl= next((x for x in info if x["filterType"] in ("MIN_NOTIONAL","NOTIONAL")), None)
    return {
        "minQty": Decimal(lot["minQty"]),
        "maxQty": Decimal(lot["maxQty"]),
        "stepSize": Decimal(lot["stepSize"]),
        "minNotional": float(notnl["minNotional"]) if notnl else 0.0
    }
FILTERS = get_symbol_filters()

# ── public helpers (for import/algorithm use) --------------------------
def get_price() -> float:
    """Return current BTC price in USDT."""
    return float(cli.ticker_price(symbol=SYMBOL)["price"])

def get_balances() -> tuple[float,float]:
    """Return (USDT_free, BTC_free)."""
    acc = cli.call(cli.account)
    bal = {b["asset"]: float(b["free"]) for b in acc["balances"]}
    return bal.get("USDT", 0.0), bal.get("BTC", 0.0)

def buy(usdt: float) -> dict:
    """Buy BTC with given USDT, checking min/max restrictions."""
    price = get_price()
    min_notnl = FILTERS["minNotional"]
    if usdt < min_notnl:
        raise ValueError(f"Order value too low, minNotional is {min_notnl:.2f} USDT")
    # max notional for BUY is not strictly enforced by Binance, but could be added here if desired
    result = cli.call(cli.new_order,
                      symbol=SYMBOL, side="BUY", type="MARKET",
                      quoteOrderQty=round(float(usdt), 2))
    return result

def sell(btc: float) -> dict:
    """Sell given BTC, checking min/max restrictions."""
    btc = Decimal(str(btc))
    if btc < FILTERS["minQty"]:
        raise ValueError(f"Order size too low, minQty is {FILTERS['minQty']}")
    if btc > FILTERS["maxQty"]:
        raise ValueError(f"Order size too high, maxQty is {FILTERS['maxQty']}")
    # round down to stepSize
    step = FILTERS["stepSize"]
    qty = (btc // step) * step
    if qty < FILTERS["minQty"]:
        raise ValueError(f"Order size too low after rounding, minQty is {FILTERS['minQty']}")
    result = cli.call(cli.new_order,
                      symbol=SYMBOL, side="SELL", type="MARKET",
                      quantity=f"{qty:f}")
    return result

def get_pair_imbalance() -> float:
    """
    Returns the difference between USDT balance and the USDT-equivalent value of BTC balance:
      > 0 if USDT > BTC-in-USDT (more cash)
      < 0 if BTC-in-USDT > USDT (more BTC value)
    """
    usdt, btc = get_balances()
    price = get_price()
    return usdt - btc * price

def get_taker_fee() -> float:
    """
    Return current taker fee for SYMBOL (e.g. 0.001 for 0.1%)
    """
    try:
        # Try user-level fee (Spot: takerCommission, in basis points)
        acc = cli.call(cli.account)
        return float(acc.get("takerCommission", 0)) / 10000
    except Exception:
        return 0.001  # fallback to typical default

def get_mid_price(minutes: int) -> float:
    """
    Returns mean close price of the last N minutes. N ≥ 1.
    """
    if minutes < 1:
        raise ValueError("Minimum supported interval is 1 minute.")
    klines = cli.klines(symbol=SYMBOL, interval="1m", limit=minutes)
    closes = [float(k[4]) for k in klines]
    return statistics.mean(closes)

# ── interactive shell --------------------------------------------------
COMMANDS = ("help","price","balance","buy","sell","imbalance","fee","rebalance","mid","quit","exit")

def show_buy_sell_restrictions():
    print(f"Buy:  value in USDT (minNotional: {FILTERS['minNotional']:.2f})")
    print(f"Sell: amount in BTC (minQty: {FILTERS['minQty']}, maxQty: {FILTERS['maxQty']}, stepSize: {FILTERS['stepSize']})")

def shell():
    global TAKER_FEE
    cls()
    print(f"btc_client  |  {MODE.upper()}  |  {SYMBOL}\n")
    while True:
        try:
            cmdline = input("> ").strip().lower()
            if not cmdline: continue
            parts = cmdline.split()
            cmd = parts[0]
            if cmd not in COMMANDS:
                print("unknown command – type 'help'"); continue
            if cmd in ("quit","exit"):
                print("bye"); break
            if cmd == "help":
                print(" ".join(COMMANDS))
                print("Command output format examples:")
                print('  price      → "Current BTC price: <float> USDT"')
                print('  balance    → "USDT <float> | BTC <float>"')
                print('  buy        → "Bought: <BTC> BTC for <USDT> USDT at price <fill price>"')
                print('  sell       → "Sold: <BTC> BTC for <USDT> USDT at price <fill price>"')
                print('  imbalance  → "Imbalance: +/-<float> USDT (USDT-heavy/BTC-heavy)"')
                print('  fee        → "Taker fee: <float>%"')
                print('  rebalance  → "Buy/sell to equalize USDT and BTC-in-USDT balances"')
                print('  mid <N>    → "Mean close price of last N minutes"')
                show_buy_sell_restrictions()
                continue

            cls()
            if cmd == "price":
                val = get_price()
                print(f'Current BTC price: {val:.2f} USDT')
            elif cmd == "balance":
                u,b = get_balances()
                print(f'USDT {u:.2f} | BTC {b:.8f}')
            elif cmd == "buy":
                show_buy_sell_restrictions()
                usdt = float(input("Amount to spend in USDT: "))
                try:
                    res = buy(usdt)
                    fills = res.get("fills", [])
                    btc_amt = sum(float(f["qty"]) for f in fills)
                    price = float(fills[0]["price"]) if fills else get_price()
                    print(f"Bought: {btc_amt:.8f} BTC for {usdt:.2f} USDT at price {price:.2f}")
                except Exception as e:
                    print("error:", e)
            elif cmd == "sell":
                show_buy_sell_restrictions()
                btc = float(input("Amount to sell in BTC: "))
                try:
                    res = sell(btc)
                    fills = res.get("fills", [])
                    usdt_amt = sum(float(f["qty"])*float(f["price"]) for f in fills)
                    price = float(fills[0]["price"]) if fills else get_price()
                    print(f"Sold: {btc:.8f} BTC for {usdt_amt:.2f} USDT at price {price:.2f}")
                except Exception as e:
                    print("error:", e)
            elif cmd == "imbalance":
                val = get_pair_imbalance()
                sign = "+" if val >= 0 else "-"
                print(f"Imbalance: {sign}{abs(val):.2f} USDT "
                      f"({'USDT-heavy' if val>=0 else 'BTC-heavy'})")
            elif cmd == "fee":
                fee = get_taker_fee()
                if fee > 0:
                    TAKER_FEE = fee
                    print(f"Taker fee: {fee*100:.3f}% (updated)")
                else:
                    print(f"Taker fee: {TAKER_FEE*100:.3f}% (default, update failed)")
            elif cmd == "rebalance":
                usdt, btc = get_balances()
                price = get_price()
                btc_val = btc * price
                diff = usdt - btc_val
                print(f"Before: USDT {usdt:.2f} | BTC {btc:.8f} (≈ {btc_val:.2f} USDT)")
                if abs(diff) < FILTERS["minNotional"]:
                    print("Imbalance below min notional, nothing to do.")
                    continue
                # Target: both sides = (usdt + btc_val)/2 (minus fee)
                target_val = (usdt + btc_val)/2
                if diff > 0:
                    # Buy BTC with excess USDT
                    usdt_to_spend = diff/2  # spend to reach equality
                    usdt_to_spend = usdt_to_spend / (1 + TAKER_FEE)
                    if usdt_to_spend < FILTERS["minNotional"]:
                        print("Required buy below min notional.")
                        continue
                    try:
                        res = buy(usdt_to_spend)
                        fills = res.get("fills", [])
                        btc_amt = sum(float(f["qty"]) for f in fills)
                        fill_price = float(fills[0]["price"]) if fills else price
                        print(f"Bought: {btc_amt:.8f} BTC for {usdt_to_spend:.2f} USDT at price {fill_price:.2f}")
                    except Exception as e:
                        print("error:", e)
                else:
                    # Sell BTC to reach equality
                    btc_to_sell = (-diff/2) / price
                    btc_to_sell = btc_to_sell / (1 + TAKER_FEE)
                    step = FILTERS["stepSize"]
                    btc_to_sell = float((Decimal(str(btc_to_sell)) // step) * step)
                    if btc_to_sell < float(FILTERS["minQty"]):
                        print("Required sell below min qty.")
                        continue
                    if btc_to_sell > float(FILTERS["maxQty"]):
                        print("Required sell above max qty.")
                        continue
                    try:
                        res = sell(btc_to_sell)
                        fills = res.get("fills", [])
                        usdt_amt = sum(float(f["qty"])*float(f["price"]) for f in fills)
                        fill_price = float(fills[0]["price"]) if fills else price
                        print(f"Sold: {btc_to_sell:.8f} BTC for {usdt_amt:.2f} USDT at price {fill_price:.2f}")
                    except Exception as e:
                        print("error:", e)
                u2, b2 = get_balances()
                print(f"After:  USDT {u2:.2f} | BTC {b2:.8f} (≈ {b2*price:.2f} USDT)")
            elif cmd == "mid":
                if len(parts) != 2 or not parts[1].isdigit():
                    print("Usage: mid <N>  (N = minutes ≥ 1)")
                    continue
                n = int(parts[1])
                if n < 1:
                    print("Minimum supported interval is 1 minute.")
                    continue
                try:
                    mid_val = get_mid_price(n)
                    print(f"Mean close price of last {n} min: {mid_val:.2f} USDT")
                except Exception as e:
                    print("error:", e)
        except KeyboardInterrupt:
            print("\nbye"); break
        except Exception as exc:
            print("error:", exc)

if __name__ == "__main__":
    shell()
