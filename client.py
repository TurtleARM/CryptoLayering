# https://github.com/sammchardy/python-binance/

import hashlib
import hmac
import requests
import time
from operator import itemgetter
from exceptions import BinanceAPIException, BinanceRequestException, BinanceWithdrawException

class Client(object):
    API_URL = 'https://api.binance.{}/api'
    FUTURES_URL = 'https://fapi.binance.{}/fapi'
    API_URL_TEST = 'https://testnet.binancefuture.{}/fapi'
    FUTURES_URL_TEST = 'https://testnet.binancefuture.{}/fapi'

    FUTURES_DATA_URL = 'https://fapi.binance.{}/futures/data'
    PUBLIC_API_VERSION = 'v1'
    PRIVATE_API_VERSION = 'v1'#'v3'
    FUTURES_API_VERSION = 'v1'
    FUTURES_API_VERSION2 = 'v2'

    def __init__(self, api_key=None, api_secret=None, requests_params=None, tld='com', testnet=False):
        """Binance API Client constructor

        :param api_key: Api Key
        :type api_key: str.
        :param api_secret: Api Secret
        :type api_secret: str.
        :param requests_params: optional - Dictionary of requests params to use for all calls
        :type requests_params: dict.

        """
        if testnet == True:
            self.API_URL = self.API_URL_TEST.format(tld)
            self.FUTURES_URL = self.FUTURES_URL_TEST.format(tld)
        else:
            self.API_URL = self.API_URL.format(tld)
            self.FUTURES_URL = self.FUTURES_URL.format(tld)
        self.FUTURES_DATA_URL = self.FUTURES_DATA_URL.format(tld)

        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.session = self._init_session()
        self._requests_params = requests_params
        self.response = None
        self.timestamp_offset = 0

        # init DNS and SSL cert
        #self.ping()
        # calculate timestamp offset between local and binance server
        res = self.get_server_time()
        self.timestamp_offset = res['serverTime'] - int(time.time() * 1000)

    def _init_session(self):
        session = requests.session()
        session.headers.update({'Accept': 'application/json',
                                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
                                'X-MBX-APIKEY': self.API_KEY})
        return session

    def _create_api_uri(self, path, signed=True, version=PUBLIC_API_VERSION):
        v = self.PRIVATE_API_VERSION if signed else version
        return self.API_URL + '/' + v + '/' + path

    def _create_futures_api_uri(self, path):
        return self.FUTURES_URL + '/' + self.FUTURES_API_VERSION + '/' + path

    def _generate_signature(self, data):
        ordered_data = self._order_params(data)
        query_string = '&'.join(["{}={}".format(d[0], d[1]) for d in ordered_data])
        m = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256)
        return m.hexdigest()

    def _order_params(self, data):
        """Convert params to list with signature as last element

        :param data:
        :return:

        """
        has_signature = False
        params = []
        for key, value in data.items():
            if key == 'signature':
                has_signature = True
            else:
                params.append((key, value))
        # sort parameters by key
        params.sort(key=itemgetter(0))
        if has_signature:
            params.append(('signature', data['signature']))
        return params

    def _request(self, method, uri, signed, force_params=False, **kwargs):
        # set default requests timeout
        kwargs['timeout'] = 10

        # add our global requests params
        if self._requests_params:
            kwargs.update(self._requests_params)

        data = kwargs.get('data', None)
        if data and isinstance(data, dict):
            kwargs['data'] = data

            # find any requests params passed and apply them
            if 'requests_params' in kwargs['data']:
                # merge requests params into kwargs
                kwargs.update(kwargs['data']['requests_params'])
                del(kwargs['data']['requests_params'])

        if signed:
            # generate signature
            kwargs['data']['timestamp'] = int(time.time() * 1000 + self.timestamp_offset)
            kwargs['data']['signature'] = self._generate_signature(kwargs['data'])

        # sort get and post params to match signature order
        if data:
            # sort post params
            kwargs['data'] = self._order_params(kwargs['data'])
            # Remove any arguments with values of None.
            null_args = [i for i, (key, value) in enumerate(kwargs['data']) if value is None]
            for i in reversed(null_args):
                del kwargs['data'][i]

        # if get request assign data array to params value for requests lib
        if data and (method == 'get' or force_params):
            kwargs['params'] = '&'.join('%s=%s' % (data[0], data[1]) for data in kwargs['data'])
            del(kwargs['data'])

        self.response = getattr(self.session, method)(uri, **kwargs)
        return self._handle_response()

    def _request_api(self, method, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        uri = self._create_api_uri(path, signed, version)

        return self._request(method, uri, signed, **kwargs)

    def _request_futures_api(self, method, path, signed=False, **kwargs):
        uri = self._create_futures_api_uri(path)

        return self._request(method, uri, signed, True, **kwargs)
        
    def _handle_response(self):
        """Internal helper for handling API responses from the Binance server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """
        # print(self.response.json())
        if not (200 <= self.response.status_code < 300):
            raise BinanceAPIException(self.response)
        try:
            return self.response.json()
        except ValueError:
            raise BinanceRequestException('Invalid Response: %s' % self.response.text)

    def _get(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        return self._request_api('get', path, signed, version, **kwargs)

    def _post(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        return self._request_api('post', path, signed, version, **kwargs)

    def _put(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        return self._request_api('put', path, signed, version, **kwargs)

    def _delete(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        return self._request_api('delete', path, signed, version, **kwargs)

    # General Endpoints

    def ping(self):
        """Test connectivity to the Rest API.

        https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#test-connectivity

        :returns: Empty array

        .. code-block:: python

            {}

        :raises: BinanceRequestException, BinanceAPIException

        """
        return self._get('ping', version=self.PRIVATE_API_VERSION)

    def get_server_time(self):
        """Test connectivity to the Rest API and get the current server time.

        https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#check-server-time

        :returns: Current server time

        .. code-block:: python

            {
                "serverTime": 1499827319559
            }

        :raises: BinanceRequestException, BinanceAPIException

        """
        return self._get('time', version=self.PRIVATE_API_VERSION)

    # Market Data Endpoints

    def get_symbol_ticker(self, **params):
        """Latest price for a symbol or symbols.

        https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#24hr-ticker-price-change-statistics

        :param symbol:
        :type symbol: str

        :returns: API response

        .. code-block:: python

            {
                "symbol": "LTCBTC",
                "price": "4.00000200"
            }

        OR

        .. code-block:: python

            [
                {
                    "symbol": "LTCBTC",
                    "price": "4.00000200"
                },
                {
                    "symbol": "ETHBTC",
                    "price": "0.07946600"
                }
            ]

        :raises: BinanceRequestException, BinanceAPIException

        """
        return self._get('ticker/price', data=params, version=self.PRIVATE_API_VERSION)

    def futures_create_order(self, **params):
        """Send in a new order.

        https://binance-docs.github.io/apidocs/futures/en/#new-order-trade

        """
        return self._request_futures_api('post', 'order', True, data=params)

    def futures_change_leverage(self, **params):
        """Change user's initial leverage of specific symbol market

        https://binance-docs.github.io/apidocs/futures/en/#change-initial-leverage-trade

        """
        return self._request_futures_api('post', 'leverage', True, data=params)

    def futures_change_margin_type(self, **params):
        """Change the margin type for a symbol

        https://binance-docs.github.io/apidocs/futures/en/#change-margin-type-trade

        """
        return self._request_futures_api('post', 'marginType', True, data=params)

    def futures_account(self, **params):
        """Get current account information.

        https://binance-docs.github.io/apidocs/futures/en/#account-information-user_data

        """
        return self._request_futures_api('get', 'account', True, data=params)
    
    def futures_exchange_info(self):
        """Current exchange trading rules and symbol information
        https://binance-docs.github.io/apidocs/futures/en/#exchange-information-market_data
        """
        return self._request_futures_api('get', 'exchangeInfo')