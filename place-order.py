from client import Client
import numpy as np
import configparser
from utilities import *

# Handle configuration file
config = configparser.ConfigParser()
config.read('config.ini')
binance_config = config['Binance Futures']
order_layout_mode = binance_config['OrderLayoutMode']
if order_layout_mode not in ('constant', 'incrementalRising', 'incrementalFalling'):
    print('Wrong layout mode value in config.ini')
    exit(-1)
api_key = binance_config['ApiKey']
api_secret = binance_config['ApiSecret']
is_testnet = str2bool(binance_config['Testnet'])
margin_type = binance_config['MarginType'].upper()
is_post_only = str2bool(binance_config['PostOnly'])

print('Connecting to Binance...')
client = Client(api_key=api_key, api_secret=api_secret, testnet=is_testnet)
exchange_info = client.futures_exchange_info()
futures_account_positions = client.futures_account()['positions']
available_balance_usdt = float(client.futures_account()['availableBalance'])

symbol = input('Trading pair [BTCUSDT]: ').upper() or 'BTCUSDT'
# Show ticker info
tickers = client.get_symbol_ticker()
user_ticker = find_object(tickers, symbol, 'symbol')
try:
    print("%s price: %s" % (symbol, user_ticker['price']))
except NameError:
    print('Wrong symbol, use the same format as \'BTCUSDT\'')
    exit(-1)
print('Current balance: %g USDT' % available_balance_usdt)
leverage = int(input('Leverage to use [1]: ') or '1')
if order_layout_mode == 'constant':
    single_amount_crypto = float(input('Constant amount to layer in %s: ' % symbol))
    delta_amount_crypto = 0
else:
    single_amount_crypto = float(input('Initial amount to layer in %s: ' % symbol))
    delta_amount_crypto = float(input('Increment for each order: '))
from_price = float(input('First price: '))
to_price = float(input('Last price: '))
side = input('Long or Short? [short] ').lower()
futures_side = 'BUY' if side == 'long' else 'SELL'
# start layering from prices closer to market price
if (futures_side == 'BUY' and from_price < to_price) or (futures_side == 'SELL' and from_price > to_price):
    from_price, to_price = to_price, from_price

available_margin = available_balance_usdt * leverage
max_n = max_orders_per_interval(from_price, to_price, available_margin, single_amount_crypto, order_layout_mode, delta_amount_crypto)
max_n = max_n if max_n < 101 else '100+'
orders_input = 'How many orders [Max = {0}]? '.format(str(max_n))
order_num = int(input(orders_input))

cur_leverage = find_object(futures_account_positions, symbol, 'symbol')['leverage']
cur_isolated = find_object(futures_account_positions, symbol, 'symbol')['isolated']
exchange_symbols = exchange_info['symbols']
asset_precision = find_object(exchange_symbols, symbol, 'symbol')['quantityPrecision'] 
usdt_precision = find_object(exchange_symbols, symbol, 'symbol')['pricePrecision']

# Truncate inputs
if order_layout_mode == 'constant':
    single_amount_crypto = float(truncate(single_amount_crypto, asset_precision))
else:
    single_amount_crypto = float(truncate(single_amount_crypto, asset_precision))
    delta_amount_crypto = float(truncate(delta_amount_crypto, asset_precision))

if int(cur_leverage) != leverage:
    client.futures_change_leverage(symbol=symbol, leverage=leverage)
    print('Changed leverage to ' + str(leverage))

cur_margin = 'CROSS' if cur_isolated == False else 'ISOLATED'
if cur_margin != margin_type:
    client.futures_change_margin_type(symbol=symbol, marginType=margin_type)
    print('Changed margin type to ' + margin_type)

order_prices = np.linspace(from_price, to_price, num=order_num).round(usdt_precision)
if order_layout_mode == 'incrementalFalling':
    order_prices = np.flipud(order_prices)

time_in_force = 'GTC' if is_post_only == False else 'GTX'
if order_layout_mode == 'constant':
    for order_price in order_prices:
        print('Setting order: %s %g of %s @%g USDT' % (futures_side, single_amount_crypto, symbol, order_price))
        client.futures_create_order(symbol=symbol, side=futures_side, type='LIMIT', quantity=single_amount_crypto, price=order_price, timeInForce=time_in_force)
else:
    order_quantity = float(truncate(single_amount_crypto, asset_precision)) # python randomly adds decimals
    for x in range(order_num):
        print('Setting order: %s %g of %s @%g USDT' % (futures_side, order_quantity, symbol, order_prices[x]))
        client.futures_create_order(symbol=symbol, side=futures_side, type='LIMIT', quantity=order_quantity, price=order_prices[x], timeInForce=time_in_force)
        order_quantity = float(truncate(order_quantity + delta_amount_crypto, asset_precision))

print('Done')

