***Crypto Layering***
---

I am not affiliated with Binance or Bybit, use at your own risk.

This tool implements the [python-binance](https://github.com/sammchardy/python-binance) library to place an arbitrary number of limit orders in a specific price interval.

The interval is divided into equal parts and orders can be distributed in three ways:
- constant:
    the same amount of crypto is repeated for each order
- incrementalRising:
    the user can choose a constant increment to be added to the base order size for each order, total order size increases as the order price gets further from the market price.
    This could be useful if you want to long and you're afraid that the price could get far from your entry
- incrementalFalling: 
    like incrementalRising, though the total order size decreases as the order price gets further from the market price.
    This could be useful if you're trying to aim at a specific entry price

**Dependencies**
---
```
pip install -r requirements.txt
```
**How to try Crypto Layering**
---

You can grab your API key/secret on the Binance testnet by signing up on https://testnet.binancefuture.com/, paste them along with '*Testnet = true*' in *config.ini* and Crypto Layering will point to it so you can practice for free.

When creating new API keys, make sure the options *Enable Reading*, *Enable Spot & Margin Trading* and *Enable Futures* are checked, you can create a pair of official keys by browsing to Profile -> API Management on https://binance.com.

As for Bybit, its testnet is available at https://testnet.bybit.com/ and its configuration works pretty much the same way as Binance.
**Execution example in *constant* mode:**

---

```html
> python place-order.py
Connecting to Binance API...
Trading pair [BTCUSDT]: 
BTCUSDT price: 54956.66
Current balance: 100000 USDT
Leverage to use [1]: 3
Constant amount to layer in BTCUSDT: 0.8
First price: 54000
Last price: 53200
Long or Short? [short] long
How many orders [Max = 6]? 6
Changed leverage to 3
Setting order: BUY 0.8 of BTCUSDT @54000 USDT
Setting order: BUY 0.8 of BTCUSDT @53840 USDT
Setting order: BUY 0.8 of BTCUSDT @53680 USDT
Setting order: BUY 0.8 of BTCUSDT @53520 USDT
Setting order: BUY 0.8 of BTCUSDT @53360 USDT
Setting order: BUY 0.8 of BTCUSDT @53200 USDT
Done
```

**Execution example in *incrementalRising* mode:**
---

```html
> python place-order.py
Connecting to Binance API...
Trading pair [BTCUSDT]: ADAUSDT
ADAUSDT price: 1.28000
Current balance: 100000 USDT
Leverage to use [1]: 2
Initial amount to layer in ADAUSDT: 1320
Increment for each order: 100
First price: 1.32
Last price: 1.36
Long or Short? [short] 
How many orders [Max = 43]? 12
Setting order: SELL 1320 of ADAUSDT @1.32 USDT
Setting order: SELL 1420 of ADAUSDT @1.32364 USDT
Setting order: SELL 1520 of ADAUSDT @1.32727 USDT
Setting order: SELL 1620 of ADAUSDT @1.33091 USDT
Setting order: SELL 1720 of ADAUSDT @1.33455 USDT
Setting order: SELL 1820 of ADAUSDT @1.33818 USDT
Setting order: SELL 1920 of ADAUSDT @1.34182 USDT
Setting order: SELL 2020 of ADAUSDT @1.34545 USDT
Setting order: SELL 2120 of ADAUSDT @1.34909 USDT
Setting order: SELL 2220 of ADAUSDT @1.35273 USDT
Setting order: SELL 2320 of ADAUSDT @1.35636 USDT
Setting order: SELL 2420 of ADAUSDT @1.36 USDT
Done
```
Notes:
- Keep the executable and its config file in the same directory.
- Values in square brackets are the default ones.
- Support for more platforms is coming soon.

**Donations**
---
If you'd like to support this tool and future developments, feel free to leave a donation.

BTC: bc1q72v5magq9tjf85qzwjlhc4cs0glujnghqlzcn4

ETH: 0x3cAbd052d4e9B69830C4dd03209b98fc606DEc79
