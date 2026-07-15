#!/usr/bin/env python3
"""
CLI entry point for the Simplified Binance Futures Testnet Trading Bot.

Examples
--------
Market order (buy):
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

Limit order (sell):
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 65000

Credentials are read from environment variables BINANCE_API_KEY / BINANCE_API_SECRET,
or from a .env file (see README.md), or passed explicitly with --api-key/--api-secret.
"""

import argparse
import os
import sys

from bot.client import BinanceAPIError, BinanceFuturesClient, BinanceNetworkError, DEFAULT_BASE_URL
from bot.logging_config import setup_logging
from bot.orders import place_order
from bot.validators import ValidationError

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; env vars can be set directly instead


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Place MARKET or LIMIT orders on Binance USDT-M Futures Testnet.",
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"],
                         help="Order side")
    parser.add_argument("--type", dest="order_type", required=True,
                         choices=["MARKET", "LIMIT", "market", "limit"],
                         help="Order type")
    parser.add_argument("--quantity", required=True, type=float, help="Order quantity")
    parser.add_argument("--price", required=False, type=float,
                         help="Order price (required for LIMIT orders)")
    parser.add_argument("--api-key", default=os.environ.get("BINANCE_API_KEY"),
                         help="Binance Testnet API key (or set BINANCE_API_KEY env var)")
    parser.add_argument("--api-secret", default=os.environ.get("BINANCE_API_SECRET"),
                         help="Binance Testnet API secret (or set BINANCE_API_SECRET env var)")
    parser.add_argument("--base-url", default=os.environ.get("BINANCE_BASE_URL", DEFAULT_BASE_URL),
                         help=f"API base URL (default: {DEFAULT_BASE_URL})")
    return parser


def main(argv=None) -> int:
    logger = setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.api_key or not args.api_secret:
        print("❌ Missing API credentials. Set BINANCE_API_KEY / BINANCE_API_SECRET "
              "env vars, use a .env file, or pass --api-key/--api-secret.")
        return 1

    try:
        client = BinanceFuturesClient(
            api_key=args.api_key, api_secret=args.api_secret, base_url=args.base_url
        )
        place_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
        return 0

    except ValidationError as exc:
        logger.warning("Validation error: %s", exc)
        print(f"❌ Invalid input: {exc}")
        return 1

    except (BinanceAPIError, BinanceNetworkError):
        # Already logged with full detail inside client.py / orders.py
        return 1

    except Exception as exc:  # noqa: BLE001 - top-level CLI safety net
        logger.exception("Unexpected error: %s", exc)
        print(f"❌ Unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
