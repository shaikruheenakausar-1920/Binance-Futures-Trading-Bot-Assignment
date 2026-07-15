# Simplified Trading Bot — Binance Futures Testnet (USDT-M)

A small, structured Python CLI application that places **MARKET** and **LIMIT**
orders on the Binance USDT-M Futures **Testnet**, with input validation,
structured logging, and clean error handling.

## Project Structure

```
trading_bot/
  bot/
    __init__.py
    client.py          # Signed REST client for Binance Futures Testnet
    orders.py           # Order placement logic + console output
    validators.py        # CLI input validation
    logging_config.py    # Logging setup (console + rotating file)
  cli.py                 # CLI entry point (argparse)
  requirements.txt
  .env.example
  README.md
  logs/                  # Created automatically at runtime
```

## 1. Setup

### a) Create a Binance Futures Testnet account
1. Go to https://testnet.binancefuture.com
2. Log in / register using your GitHub account.
3. Once inside, go to **API Key** (top right / account menu) and generate a new
   API Key + Secret. This is a *separate* key from real Binance — it only
   works on the testnet.
4. (Optional) Use the testnet UI to fund your test wallet with test USDT — new
   accounts usually start with test funds already.

### b) Install dependencies
```bash
cd trading_bot
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### c) Configure your API credentials
Copy the example env file and fill in your testnet keys:
```bash
cp .env.example .env
```
Edit `.env`:
```
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```
The CLI automatically loads `.env` via `python-dotenv`. Alternatively, export
the variables directly in your shell, or pass `--api-key` / `--api-secret`
flags explicitly.

## 2. Running the bot

### Market order
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Limit order
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 65000
```

### CLI arguments
| Flag           | Required          | Description                              |
|----------------|--------------------|-------------------------------------------|
| `--symbol`     | Yes                | Trading pair, e.g. `BTCUSDT`             |
| `--side`       | Yes                | `BUY` or `SELL`                          |
| `--type`       | Yes                | `MARKET` or `LIMIT`                      |
| `--quantity`   | Yes                | Order quantity (float, > 0)              |
| `--price`      | Only for `LIMIT`   | Limit price (float, > 0)                 |
| `--api-key`    | No (if in `.env`)  | Overrides `BINANCE_API_KEY`              |
| `--api-secret` | No (if in `.env`)  | Overrides `BINANCE_API_SECRET`           |
| `--base-url`   | No                 | Defaults to the Futures Testnet base URL |

On success, the CLI prints an order request summary, then the response
(`orderId`, `status`, `executedQty`, `avgPrice` if available), followed by a
success message. On failure (bad input, API error, or network error) a clear
`❌` message is printed and the process exits with code `1`.

## 3. Logs

Every request, response, and error is logged to `logs/trading_bot.log`
(rotates at 2MB, keeps 5 backups) and a summary is also printed to the
console. Example log line:
```
2026-07-15 14:24:49 | DEBUG | trading_bot.client | REQUEST POST https://testnet.binancefuture.com/fapi/v1/order | params={'symbol': 'BTCUSDT', ...}
```
The `logs/` folder is created automatically on first run and is git-ignored
(you should attach sample log files separately as deliverables, per the task
instructions, rather than committing the whole folder).

## 4. Assumptions

- Only `MARKET` and `LIMIT` order types are required; `timeInForce` for
  `LIMIT` orders defaults to `GTC` (Good-Til-Canceled).
- Symbol format is validated generically (`[A-Z0-9]{5,20}`) rather than
  cross-checked against Binance's live exchange-info list, to keep the tool
  dependency-free and fast; Binance itself will reject genuinely invalid
  symbols with a clear API error, which the bot surfaces and logs.
- Credentials are only ever read from environment variables / `.env` /
  explicit CLI flags — never hard-coded.
- This is a testnet-only tool; no mainnet trading logic is included.

## 5. Error Handling Covered

- **Invalid input**: missing/invalid symbol, side, order type, quantity, or a
  missing price on a `LIMIT` order — caught before any API call is made.
- **API errors**: non-200 responses from Binance (e.g. invalid symbol,
  insufficient balance, bad signature) are caught, logged, and shown clearly.
- **Network errors**: timeouts / connection failures are caught separately
  and reported without crashing.

## Bonus Ideas (not implemented by default)

The `bot/client.py` module already exposes a signed `_signed_request` helper
that can be reused to add a `STOP` / `STOP_MARKET` order type, an OCO order,
or a simple TWAP loop that slices a large order into smaller timed pieces.
