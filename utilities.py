import numpy as np

def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '%.12f' % f
    i, p, d = s.partition('.')
    return '.'.join([i, (d+'0'*n)[:n]])

def str2bool(v):
    '''Converts a string to its boolean form'''
    return v.lower() in ("yes", "true", "t", "1")

def find_object(json_array, symbol, key):
    '''Finds the correct object from the Binance response'''
    for json_object in json_array:
        if json_object[key] == symbol:
            return json_object

def max_orders_per_interval(bottom, top, available, single_amount, layer_mode, increment):
    '''Calculates the maximum number of placeable orders with the available margin'''
    for n in range(2, 101):
        if not(is_layering_executable(bottom, top, n, available, single_amount, layer_mode, increment)):
            return n - 1
    return 101

def is_layering_executable(bottom, top, n, available, single_amount, layer_mode, increment):
    interval_prices = np.linspace(bottom, top, num=n)
    return get_order_total(interval_prices, single_amount, increment, layer_mode) <= available

def get_order_total(interval, crypto_amount, increment, layer_mode):
    total = 0
    if layer_mode == 'constant':
        for price in interval:
            total += crypto_amount * price
        return total
    elif layer_mode == 'incrementalFalling':
        interval = np.flipud(interval)
    for price in interval:
        total += crypto_amount * price
        crypto_amount += increment
    return total