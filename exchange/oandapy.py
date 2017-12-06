import json
import requests
import logging
""" OANDA API wrapper for OANDA's REST API """
""" EndpointsMixin provides a mixin for the API instance
Parameters that need to be embedded in the API url just need to be passed as a
keyword argument.
E.g. oandapy_instance.get_instruments(instruments="EUR_USD")
"""


class EndpointsMixin(object):
    """Rates"""

    def get_instruments(self, account_id, **params):
        """ Get an instrument list
        Docs: http://developer.oanda.com/docs/v3/rates/#get-an-instrument-list
        """
        endpoint = 'v3/instruments'
        return self.request(endpoint, params=params)

    def get_prices(self, account_id, **params):
        """ Get current prices
        Docs: http://developer.oanda.com/docs/v3/rates/#get-current-prices
        """
        endpoint = 'v3/accounts/%s/pricing' % account_id
        return self.request(endpoint, params=params)

    def get_history(self, instrument, **params):
        """ Retrieve instrument history
        Docs: http://developer.oanda.com/docs/v3/rates/#retrieve-instrument-history
        """
        endpoint = 'v3/instruments/' + instrument + '/candles'
        response = self.request(endpoint, params=params)
        return response

    """Accounts"""

    def create_account(self, **params):
        """ Create an account. Valid only in sandbox.
        Docs: http://developer.oanda.com/docs/v3/accounts/#get-accounts-for-a-user
        """
        endpoint = 'v3/accounts'
        return self.request(endpoint, "POST", params=params)

    def get_accounts(self, account_id, **params):
        """ Get accounts for a user.
        Docs: http://developer.oanda.com/docs/v3/accounts/#get-accounts-for-a-user
        """
        endpoint = 'v3/accounts/' + account_id
        return self.request(endpoint, params=params)

    def get_account(self, account_id, **params):
        """ Get account information
        Docs: http://developer.oanda.com/docs/v3/accounts/#get-account-information
        """
        endpoint = 'v3/accounts/%s' % (account_id)
        return self.request(endpoint, params=params)

    """Orders"""

    def get_orders(self, account_id, **params):
        """ Get orders for an account
        Docs: http://developer.oanda.com/docs/v1/orders/#get-orders-for-an-account
        """
        endpoint = 'v3/accounts/%s/orders' % (account_id)
        return self.request(endpoint, params=params)

    def create_order(self, account_id, **params):
        endpoint = 'v3/accounts/%s/orders' % account_id
        return self.request(endpoint, 'POST', params=params)

    def get_order(self, account_id, order_id, **params):
        """ Get information for an order
        Docs: http://developer.oanda.com/docs/v3/orders/#get-information-for-an-order
        """
        endpoint = 'v3/accounts/%s/orders/%s' % (account_id, order_id)
        return self.request(endpoint, params=params)

    def modify_order(self, account_id, order_id, **params):
        """ Modify an existing order
        Docs: http://developer.oanda.com/docs/v3/orders/#modify-an-existing-order
        """
        endpoint = 'v3/accounts/%s/orders/%s' % (account_id, order_id)
        return self.request(endpoint, "PATCH", params=params)

    def close_order(self, account_id, order_id, **params):
        """ Close an order
        Docs: http://developer.oanda.com/docs/v3/orders/#close-an-order
        """
        endpoint = 'v3/accounts/%s/orders/%s/cancel' % (account_id, order_id)
        return self.request(endpoint, "PUT", params=params)

    """Trades"""

    def get_trades(self, account_id, **params):
        """ Get a list of open trades
        Docs: http://developer.oanda.com/docs/v3/trades/#get-a-list-of-open-trades
        """
        endpoint = 'v3/accounts/%s/trades' % (account_id)
        return self.request(endpoint, params=params)

    def get_trade(self, account_id, trade_id, **params):
        """ Get information on a specific trade
        Docs: http://developer.oanda.com/docs/v3/trades/#get-information-on-a-specific-trade
        """
        endpoint = 'v3/accounts/%s/trades/%s' % (account_id, trade_id)
        return self.request(endpoint, params=params)

    def modify_trade(self, account_id, trade_id, **params):
        """ Modify an existing trade
        Docs: http://developer.oanda.com/docs/v3/trades/#modify-an-existing-trade
        """
        endpoint = 'v3/accounts/%s/trades/%s' % (account_id, trade_id)
        return self.request(endpoint, "PATCH", params=params)

    def close_trade(self, account_id, trade_id, **params):
        """ Close an open trade
        Docs: http://developer.oanda.com/docs/v3/trades/#close-an-open-trade
        """
        endpoint = 'v3/accounts/%s/trades/%s/close' % (account_id, trade_id)
        return self.request(endpoint, "PUT", params=params)

    """Positions"""

    def get_positions(self, account_id, **params):
        """ Get a list of all open positions
        Docs: http://developer.oanda.com/docs/v3/positions/#get-a-list-of-all-open-positions
        """
        endpoint = 'v3/accounts/%s/positions' % (account_id)
        return self.request(endpoint, params=params)

    def get_position(self, account_id, instrument, **params):
        """ Get the position for an instrument
        Docs: http://developer.oanda.com/docs/v3/positions/#get-the-position-for-an-instrument
        """
        endpoint = 'v3/accounts/%s/positions/%s' % (account_id, instrument)
        return self.request(endpoint, params=params)

    def close_position(self, account_id, instrument, **params):
        endpoint = "v3/accounts/%s/positions/%s/close" % (account_id,
                                                          instrument)
        return self.request(endpoint, "PUT", params=params)

    """Transaction History"""

    def get_transaction_history(self, account_id, **params):
        """ Get transaction history
        Docs: http://developer.oanda.com/docs/v3/transactions/#get-transaction-history
        """
        endpoint = 'v3/accounts/%s/transactions' % (account_id)
        return self.request(endpoint, params=params)

    def get_transaction(self, account_id, transaction_id):
        """ Get information for a transaction
        Docs: http://developer.oanda.com/docs/v3/transactions/#get-information-for-a-transaction
        """
        endpoint = 'v3/accounts/%s/transactions/%s' % (account_id,
                                                       transaction_id)
        return self.request(endpoint)

    """Forex Labs"""

    def get_eco_calendar(self, **params):
        """Returns up to 1 year of economic calendar info
        Docs: http://developer.oanda.com/rest-live/forex-labs/
        """
        endpoint = 'labs/v3/calendar'
        return self.request(endpoint, params=params)

    def get_historical_position_ratios(self, **params):
        """Returns up to 1 year of historical position ratios
        Docs: http://developer.oanda.com/rest-live/forex-labs/
        """
        endpoint = 'labs/v3/historical_position_ratios'
        return self.request(endpoint, params=params)

    def get_historical_spreads(self, **params):
        """Returns up to 1 year of spread information
        Docs: http://developer.oanda.com/rest-live/forex-labs/
        """
        endpoint = 'labs/v3/spreads'
        return self.request(endpoint, params=params)

    def get_commitments_of_traders(self, **params):
        """Returns up to 4 years of Commitments of Traders data from the CFTC
        Docs: http://developer.oanda.com/rest-live/forex-labs/
        """
        endpoint = 'labs/v3/commitments_of_traders'
        return self.request(endpoint, params=params)

    def get_orderbook(self, **params):
        """Returns up to 1 year of OANDA Order book data
        Docs: http://developer.oanda.com/rest-live/forex-labs/
        """
        endpoint = 'labs/v3/orderbook_data'
        return self.request(endpoint, params=params)


""" Provides functionality for access to core OANDA API calls """


class API(EndpointsMixin, object):
    def __init__(self, environment="practice", access_token=None,
                 headers=None):
        """Instantiates an instance of OandaPy's API wrapper
        :param environment: (optional) Provide the environment for oanda's \
          REST api, either 'sandbox', 'practice', or 'live'. Default: practice
        :param access_token: (optional) Provide a valid access token if you \
          have one. This is required if the environment is not sandbox.
        """

        if environment == 'sandbox':
            self.api_url = 'http://api-sandbox.oanda.com'
        elif environment == 'practice':
            self.api_url = 'https://api-fxpractice.oanda.com'
        elif environment == 'live':
            self.api_url = 'https://api-fxtrade.oanda.com'

        self.access_token = access_token
        self.client = requests.Session()

        if self.access_token:
            self.client.headers[
                'Authorization'] = 'Bearer ' + self.access_token

        if headers:
            self.client.headers.update(headers)

    def request(self, endpoint, method='GET', params=None):
        """Returns dict of response from OANDA's open API
        :param endpoint: (required) OANDA API endpoint (e.g. v3/instruments)
        :type endpoint: string
        :param method: (optional) Method of accessing data, either GET or \
          POST. (default GET)
        :type method: string
        :param params: (optional) Dict of parameters (if any) accepted the by \
          OANDA API endpoint you are trying to access (default None)
        :type params: dict or None
        """

        url = '%s/%s' % (self.api_url, endpoint)

        method = method.lower()
        params = params or {}

        func = getattr(self.client, method)

        request_args = {}
        if method == 'get':
            request_args['params'] = params
            header = {}
        else:
            header = {'Content-type': 'application/json'}
            request_args['json'] = params['params']

        try:
            response = func(url, headers=header, **request_args)
        except requests.RequestException as e:
            raise OandaError(e)
        content = response.content.decode('utf-8')

        content = json.loads(content)

        # error message
        if response.status_code >= 400:
            if 'errorCode' in content:
                if content['errorCode'] != 'CLOSEOUT_POSITION_DOESNT_EXIST':
                    raise OandaError(content)
            else:
                raise OandaError(content)

        return content


"""HTTPS Streaming"""


class Streamer():
    """ Provides functionality for HTTPS Streaming
    Docs: http://developer.oanda.com/docs/v3/stream/#rates-streaming
    """

    def __init__(self, account_id, environment="practice", access_token=None):
        """Instantiates an instance of OandaPy's streaming API wrapper.
        :param environment: (optional) Provide the environment for oanda's \
          REST api, either 'practice', or 'live'. Default: practice
        :param access_token: (optional) Provide a valid access token if you \
          have one. This is required if the environment is not sandbox.
        """

        if environment == 'practice':
            self.api_url = 'https://stream-fxpractice.oanda.com/v3/accounts/%s/pricing/stream' % account_id
        elif environment == 'live':
            self.api_url = 'https://stream-fxtrade.oanda.com/v3/accounts/%s/pricing/stream' % account_id

        self.access_token = access_token
        self.client = requests.Session()
        self.client.stream = True
        self.connected = False

        if self.access_token:
            self.client.headers[
                'Authorization'] = 'Bearer ' + self.access_token

    def start(self, ignore_heartbeat=True, **params):
        """ Starts the stream with the given parameters
        :param accountId: (Required) The account that prices are applicable for.
        :param instruments: (Required) A (URL encoded) comma separated list of\
          instruments to fetch prices for.
        :param ignore_heartbeat: (optional) Whether or not to display the \
          heartbeat. Default: True
        """
        self.connected = True

        request_args = {}
        request_args['params'] = params

        while self.connected:
            response = self.client.get(self.api_url, **request_args)

            if response.status_code != 200:
                self.on_error(response.content)

            for line in response.iter_lines(90):
                if not self.connected:
                    break

                if line:
                    data = json.loads(line.decode("utf-8"))
                    if not (ignore_heartbeat and "heartbeat" in data):
                        self.on_success(data)

    def on_success(self, data):
        """ Called when data is successfully retrieved from the stream
        Override this to handle your streaming data.
        :param data: response object sent from stream
        """

        return True

    def on_error(self, data):
        """ Called when stream returns non-200 status code
        Override this to handle your streaming data.
        :param data: error response object sent from stream
        """

        return

    def disconnect(self):
        self.connected = False


class OandaError(Exception):
    def __init__(self, error_response):
        msg = "OANDA API returned error: %s " % error_response
        logging.error(msg)
        super(OandaError, self).__init__(msg)
