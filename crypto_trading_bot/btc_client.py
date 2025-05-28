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
  quit/exit  leave program
"""
from __future__ import annotations
import os, sys, time, platform
from decimal import Decimal
from dotenv import load_dotenv
from binance.spot import Spot as Client
from binance.error import ClientError

# ─────────────────────────────────────────────────────
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
    result = cli.call(cli.new_order,
                      symbol=SYMBOL, side="BUY", type="MARKET",
                      quoteOrderQty=round(float(usdt), 2))
    return result

def sell(btc: float) -> dict:
    """Sell given BTC, checking min/max restrictions."""
    btc = Decimal(str(btc))
    if btc < FILTERS["minQty"]:
        raise ValueError(f"Order size too low, minQty is {FILTERS['minQty']}")
    # round down to stepSize
    step = FILTERS["stepSize"]
    qty = (btc // step) * step
    result = cli.call(cli.new_order,
                      symbol=SYMBOL, side="SELL", type="MARKET",
                      quantity=f"{qty:f}")
    return result

# ── interactive shell --------------------------------------------------
COMMANDS = ("help","price","balance","buy","sell","quit","exit")

def show_buy_sell_restrictions():
    print(f"Buy:  value in USDT (minNotional: {FILTERS['minNotional']:.2f})")
    print(f"Sell: amount in BTC (minQty: {FILTERS['minQty']}, stepSize: {FILTERS['stepSize']})")

def shell():
    cls()
    print(f"btc_client  |  {MODE.upper()}  |  {SYMBOL}\n")
    while True:
        try:
            cmd = input("> ").strip().lower()
            if not cmd: continue
            if cmd not in COMMANDS:
                print("unknown command – type 'help'"); continue
            if cmd in ("quit","exit"):
                print("bye"); break
            if cmd == "help":
                print(" ".join(COMMANDS))
                print("Command output format examples:")
                print('  price   → "Current BTC price: <float> USDT"')
                print('  balance → "USDT <float> | BTC <float>"')
                print('  buy     → "Bought: <BTC> BTC for <USDT> USDT at price <fill price>"')
                print('  sell    → "Sold: <BTC> BTC for <USDT> USDT at price <fill price>"')
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
        except KeyboardInterrupt:
            print("\nbye"); break
        except Exception as exc:
            print("error:", exc)

if __name__ == "__main__":
    shell()
