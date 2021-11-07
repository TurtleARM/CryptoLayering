import bybit
import configparser
from utilities import *
from pybit import HTTP

# Handle configuration file
config = configparser.ConfigParser()
config.read('config.ini')
bybit_config = config['Bybit']
order_layout_mode = bybit_config['OrderLayoutMode']
if order_layout_mode not in ('constant', 'incrementalRising', 'incrementalFalling'):
    print('Wrong layout mode value in config.ini')
    exit(-1)
api_key = bybit_config['ApiKey']
api_secret = bybit_config['ApiSecret']
is_testnet = str2bool(bybit_config['Testnet'])
margin_type = bybit_config['MarginType'].upper()
inverse = True
print('Connecting to Bybit...')
client = bybit.bybit(test=is_testnet, api_key=api_key, api_secret=api_secret)
session = HTTP("https://api-testnet.bybit.com", api_key=api_key, api_secret=api_secret) if is_testnet else HTTP("https://api.bybit.com", api_key=api_key, api_secret=api_secret)
info = client.Market.Market_symbolInfo().result()
symbol = input('Trading pair [BTCUSD]: ').upper() or 'BTCUSD'
if symbol.endswith('USDT'):
    inverse = False
try:
    symbol_info = find_object(info[0]['result'], symbol, 'symbol')
    print("%s price: %s" % (symbol, symbol_info['last_price']))
except NameError:
    print('Wrong symbol, use the same format as \'BTCUSD\'')
    exit(-1)
available_balance_usdt = available_balance = 0
try:
    if inverse:
        crypto = symbol.replace('USD', '')
        available_balance = client.Wallet.Wallet_getBalance(coin=crypto).result()[0]['result'][crypto]['available_balance']
        available_balance_usdt = available_balance * float(symbol_info['last_price'])
        print('Current balance: %g %s' % (available_balance, crypto))
    else:
        available_balance_usdt = client.Wallet.Wallet_getBalance(coin='USDT').result()[0]['result']['USDT']['available_balance']
        available_balance = available_balance_usdt / float(symbol_info['last_price'])
        print('Current balance: %g USDT' % (available_balance_usdt))
except TypeError:
    print('recv window exceeded, fix it in the BybitAuthenticator module')
    exit(-1)

leverage = int(input('Leverage to use [1]: ') or '1')
position = client.Positions.Positions_myPosition(symbol=symbol).result() if inverse else client.LinearPositions.LinearPositions_myPosition(symbol=symbol).result()
cur_leverage = position[0]['result']['leverage'] if inverse else position[0]['result'][0]['leverage']
is_isolated = position[0]['result']['is_isolated'] if inverse else position[0]['result'][0]['is_isolated']
if inverse:
    if margin_type == "ISOLATED" and not is_isolated:
        session.cross_isolated_margin_switch(symbol=symbol, is_isolated=True, buy_leverage=leverage, sell_leverage=leverage)
    elif margin_type == "CROSS" and is_isolated:
        session.cross_isolated_margin_switch(symbol=symbol, is_isolated=False, buy_leverage=leverage, sell_leverage=leverage)
    else:
        print('Margin type is already correct')
    if int(cur_leverage) != leverage:
        session.set_leverage(symbol=symbol, leverage=leverage)
else:
    if margin_type == "ISOLATED" and not is_isolated:
        client.LinearPositions.LinearPositions_switchIsolated(symbol=symbol, is_isolated=True, buy_leverage=leverage, sell_leverage=leverage).result()
    elif margin_type == "CROSS" and is_isolated:
        client.LinearPositions.LinearPositions_switchIsolated(symbol=symbol, is_isolated=False, buy_leverage=leverage, sell_leverage=leverage).result()
    else:
        print('Margin type is already correct')
    if int(cur_leverage) != leverage:
        client.LinearPositions.LinearPositions_saveLeverage(symbol=symbol, buy_leverage=leverage, sell_leverage=leverage).result()
print('Leverage set to %g' % leverage)

if order_layout_mode == 'constant':
    single_amount_crypto = float(input('Constant amount to layer in USD(T): '))
    delta_amount_crypto = 0
else:
    single_amount_crypto = float(input('Initial amount to layer in USD(T): '))
    delta_amount_crypto = float(input('Increment for each order: '))
from_price = float(input('First price: '))
to_price = float(input('Last price: '))
side = input('Long or Short? [short] ').lower()
futures_side = 'BUY' if side == 'long' else 'SELL'
# start layering from prices closer to market price
if (futures_side == 'BUY' and from_price < to_price) or (futures_side == 'SELL' and from_price > to_price):
    from_price, to_price = to_price, from_price

available_margin = available_balance_usdt * leverage 
order_num = int(input('How many orders? '))
order_prices = np.linspace(from_price, to_price, num=order_num).round(4)
if order_layout_mode == 'incrementalFalling':
    order_prices = np.flipud(order_prices)
if order_layout_mode == 'constant':
    for order_price in order_prices:
        decimal_places = 3
        print('Setting order: %s %g of %s @%g USD' % (futures_side, single_amount_crypto, symbol, order_price))
        if inverse:
            order = client.Order.Order_new(side=futures_side.title(), symbol=symbol, order_type="Limit", qty=single_amount_crypto, price=order_price, time_in_force="GoodTillCancel").result()
        else:
            qty = float(truncate(single_amount_crypto / order_price, decimal_places))
            order = client.LinearOrder.LinearOrder_new(side=futures_side.title(), reduce_only=False, close_on_trigger=False, symbol=symbol, order_type="Limit", qty=qty, price=order_price, time_in_force="GoodTillCancel").result()
            while order[0]['ret_code'] == 10001 and decimal_places >= 0:
                decimal_places -= 1
                qty = float(truncate(qty, decimal_places))
                order = client.LinearOrder.LinearOrder_new(side=futures_side.title(), reduce_only=False, close_on_trigger=False, symbol=symbol, order_type="Limit", qty=qty, price=order_price, time_in_force="GoodTillCancel").result()
else:
    order_quantity = single_amount_crypto
    for x in range(order_num):
        decimal_places = 3
        print('Setting order: %s %g of %s @%g USDT' % (futures_side, order_quantity, symbol, order_prices[x]))
        if inverse:
            order = client.Order.Order_new(side=futures_side.title(), symbol=symbol, order_type="Limit", qty=order_quantity, price=order_prices[x], time_in_force="GoodTillCancel").result()
        else:
            qty = float(truncate(single_amount_crypto / order_prices[x], decimal_places))
            order = client.LinearOrder.LinearOrder_new(side=futures_side.title(), reduce_only=False, close_on_trigger=False, symbol=symbol, order_type="Limit", qty=qty, price=order_prices[x], time_in_force="GoodTillCancel").result()
            while order[0]['ret_code'] == 10001 and decimal_places >= 0:
                decimal_places -= 1
                qty = float(truncate(qty, decimal_places))
                order = client.LinearOrder.LinearOrder_new(side=futures_side.title(), reduce_only=False, close_on_trigger=False, symbol=symbol, order_type="Limit", qty=qty, price=order_prices[x], time_in_force="GoodTillCancel").result()
        order_quantity = order_quantity + delta_amount_crypto

print('Done')
# Only available after opening a position
# print(client.Positions.Positions_myPosition(symbol="BTCUSD").result())
