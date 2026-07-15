"""
Order placement orchestration: ties together validation, the API client,
logging, and console-friendly summaries.
"""

import logging

from bot.client import BinanceAPIError, BinanceNetworkError, BinanceFuturesClient
from bot.validators import ValidationError, validate_order_input

logger = logging.getLogger("trading_bot.orders")


def print_order_summary(order: dict) -> None:
    print("\n--- Order Request Summary ---")
    print(f"  Symbol:   {order['symbol']}")
    print(f"  Side:     {order['side']}")
    print(f"  Type:     {order['order_type']}")
    print(f"  Quantity: {order['quantity']}")
    if order["order_type"] == "LIMIT":
        print(f"  Price:    {order['price']}")
    print("------------------------------\n")


def print_order_response(response: dict) -> None:
    print("--- Order Response ---")
    print(f"  Order ID:     {response.get('orderId')}")
    print(f"  Status:       {response.get('status')}")
    print(f"  Executed Qty: {response.get('executedQty')}")
    avg_price = response.get("avgPrice")
    if avg_price is not None:
        print(f"  Avg Price:    {avg_price}")
    print("-----------------------\n")


def place_order(client: BinanceFuturesClient, symbol: str, side: str, order_type: str,
                 quantity, price=None) -> dict:
    """
    Validate input, place the order via the client, log and print results.
    Returns the raw API response dict on success. Raises on failure
    (ValidationError, BinanceAPIError, BinanceNetworkError).
    """
    order = validate_order_input(symbol, side, order_type, quantity, price)
    print_order_summary(order)
    logger.info("Placing order: %s", order)

    try:
        response = client.place_order(
            symbol=order["symbol"],
            side=order["side"],
            order_type=order["order_type"],
            quantity=order["quantity"],
            price=order["price"],
        )
    except (BinanceAPIError, BinanceNetworkError) as exc:
        logger.error("Order FAILED: %s", exc)
        print(f"❌ Order failed: {exc}")
        raise

    logger.info("Order SUCCESS: response=%s", response)
    print_order_response(response)
    print("✅ Order placed successfully.")
    return response
