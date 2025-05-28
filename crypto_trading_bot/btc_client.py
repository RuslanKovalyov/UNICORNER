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
  quit/exit  leave program
"""
from __future__ import annotations
import os, sys, time, platform
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

# ── public helpers -----------------------------------------------------
def get_price() -> float:
    """Return current BTC price in USDT."""
    return float(cli.ticker_price(symbol=SYMBOL)["price"])

def get_balances() -> tuple[float,float]:
    """Return (USDT_free, BTC_free)."""
    acc = cli.call(cli.account)
    bal = {b["asset"]: float(b["free"]) for b in acc["balances"]}
    return bal.get("USDT", 0.0), bal.get("BTC", 0.0)

# ── interactive shell --------------------------------------------------
COMMANDS = ("help","price","balance","quit","exit")

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
                continue

            cls()
            if cmd == "price":
                val = get_price()
                print(f'Current BTC price: {val:.2f} USDT')
            elif cmd == "balance":
                u,b = get_balances()
                print(f'USDT {u:.2f} | BTC {b:.8f}')
        except KeyboardInterrupt:
            print("\nbye"); break
        except Exception as exc:
            print("error:", exc)

if __name__ == "__main__":
    shell()
