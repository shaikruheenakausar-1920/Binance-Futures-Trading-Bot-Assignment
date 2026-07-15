"""
Thin wrapper around the Binance USDT-M Futures Testnet REST API.

Uses plain `requests` calls (no python-binance dependency) so behaviour is
transparent and easy to debug. All requests/responses/errors are logged.

Docs: https://binance-docs.github.io/apidocs/futures/en/
"""

import hashlib
import hmac
import logging
import time
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot.client")

DEFAULT_BASE_URL = "https://testnet.binancefuture.com"


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, message, status_code=None, payload=None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class BinanceNetworkError(Exception):
    """Raised on connection/timeout issues talking to Binance."""


class BinanceFuturesClient:
    """
    Minimal signed REST client for Binance USDT-M Futures (Testnet by default).
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = DEFAULT_BASE_URL,
                 timeout: int = 10):
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret are required.")
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    # ---------- internal helpers ----------

    def _sign(self, params: dict) -> str:
        query_string = urlencode(params, doseq=True)
        signature = hmac.new(
            self.api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return signature

    def _signed_request(self, method: str, path: str, params: dict = None):
        params = dict(params or {})
        params["timestamp"] = int(time.time() * 1000)
        params.setdefault("recvWindow", 5000)
        params["signature"] = self._sign(params)

        url = f"{self.base_url}{path}"
        logger.debug("REQUEST %s %s | params=%s", method, url,
                      {k: v for k, v in params.items() if k != "signature"})

        try:
            response = self.session.request(method, url, params=params, timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            logger.error("NETWORK ERROR on %s %s: %s", method, url, exc)
            raise BinanceNetworkError(f"Network error while calling {path}: {exc}") from exc

        logger.debug("RESPONSE status=%s body=%s", response.status_code, response.text)

        if response.status_code != 200:
            logger.error("API ERROR status=%s body=%s", response.status_code, response.text)
            try:
                payload = response.json()
            except ValueError:
                payload = {"raw": response.text}
            raise BinanceAPIError(
                f"Binance API returned status {response.status_code}: {payload}",
                status_code=response.status_code,
                payload=payload,
            )

        return response.json()

    # ---------- public API ----------

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float,
                     price: float = None, time_in_force: str = "GTC"):
        """
        Place a MARKET or LIMIT order on USDT-M Futures.

        POST /fapi/v1/order
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }
        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force

        return self._signed_request("POST", "/fapi/v1/order", params)

    def get_order(self, symbol: str, order_id: int):
        """GET /fapi/v1/order - check status of an existing order."""
        return self._signed_request("GET", "/fapi/v1/order", {"symbol": symbol, "orderId": order_id})

    def get_account_balance(self):
        """GET /fapi/v2/balance - useful for sanity-checking connectivity/credentials."""
        return self._signed_request("GET", "/fapi/v2/balance")
