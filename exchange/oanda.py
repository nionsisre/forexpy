import datetime
import re
import time
import threading
import queue
from math import floor
import logging
import dateutil.parser
from exchange import oandapy
from logic.candle import Candle
from logic import MarketTrend
from util.watchdog import WatchDog


class OandaPriceStreamer(oandapy.Streamer):
    def __init__(self, environment, api_key, account_id, instrument):
        self._api_key = api_key
        self._account_id = account_id
        self._instrument = instrument
        oandapy.Streamer.__init__(
            self,
            account_id=self._account_id,
            environment=environment,
            access_token=api_key)
        self.ticker_subscribers = []
        self.heartbeat_subscribers = []
        self.upd_subscribers = []
        self.update_necessary = True
        self._queue = queue.Queue()
        self._thread = threading.Thread(
            target=OandaPriceStreamer._start, args=(self))
        self._thread.setDaemon(True)
        self._watchdog = WatchDog()

    def subscribe_ticker(self, obj):
        self.ticker_subscribers.append(obj)

    def subscribe_heartbeat(self, obj):
        self.heartbeat_subscribers.append(obj)

    def subscribe_updates(self, obj):
        self.upd_subscribers.append(obj)

    def is_running(self):
        return self._thread.isAlive()

    def _start(self):
        self.start(
            accountId=self._account_id,
            instruments=self._instrument,
            ignore_heartbeat=False)

    def _stop(self):
        self.disconnect()

    def start_streamer(self):
        self._watchdog.start()
        self._thread.start()

    def stop(self):
        self._watchdog.stop()
        self._stop()
        self._thread.join()

    def on_success(self, data):
        self._watchdog.reset()
        self._queue.put(data)

    def update_subscribers(self):
        # If watchdog fired, throw!
        if self._watchdog.IsExpired():
            txt = 'Watchdog: have not seen heartbeat from exchange for '
            txt += str(self._watchdog.watchdog_timeout_seconds) + ' seconds'
            raise Exception(txt)

        data = None

        try:
            data = self._queue.get(True, 0.1)
        except:
            return

        if not data:
            return

        if self.update_necessary:
            for obj in self.upd_subscribers:
                obj.update(None)
            self.update_necessary = False

        if data['type'] == 'HEARTBEAT':
            for obj in self.heartbeat_subscribers:
                obj.update(data)
            return

        if data['type'] != 'PRICE':
            return

        ask = float(data['asks'][0]['price'])
        bid = float(data['bids'][0]['price'])
        timestamp = dateutil.parser.parse(data['time'])
        price = (ask + bid) / 2.0

        datapoint = {}
        datapoint['now'] = time.mktime(
            timestamp.timetuple()) + timestamp.microsecond * 0.000001
        datapoint['value'] = price
        for obj in self.ticker_subscribers:
            obj.update(datapoint)

        return True


class Oanda(object):
    def __init__(self,
                 api_key,
                 account_id,
                 instrument,
                 account_currency,
                 home_base_pair,
                 home_base_default_exchange_rate=1.0,
                 environment='practice'):
        self._api_key = api_key
        self._account_id = account_id
        self._instrument = instrument
        self._home_base_pair = home_base_pair
        self._home_base_default_exchange_rate = home_base_default_exchange_rate
        self._account_currency = account_currency
        self._oanda = oandapy.API(
            environment=environment, access_token=self._api_key)
        self._oanda_price_streamer = OandaPriceStreamer(
            environment=environment,
            api_key=self._api_key,
            account_id=account_id,
            instrument=instrument)

    def subscribe_ticker(self, obj):
        self._oanda_price_streamer.subscribe_ticker(obj)

    def subscribe_heartbeat(self, obj):
        self._oanda_price_streamer.subscribe_heartbeat(obj)

    def subscribe_updates(self, obj):
        self._oanda_price_streamer.subscribe_updates(obj)

    def start_price_streaming(self):
        self._oanda_price_streamer.start()

    def stop_price_streaming(self):
        self._oanda_price_streamer.stop()

    def get_net_worth(self):
        try:
            response = self._oanda.get_account(self._account_id)
        except:
            self._oanda_price_streamer.update_necessary = True
            return 0.0
        return float(response['account']['balance'])

    def close_position(self, position):
        if position == 'both':
            self.close_position('short')
            self.close_position('long')
            return
        order_data = {'%sUnits' % position: 'ALL'}
        self._oanda.close_position(
            self._account_id, instrument=self._instrument, params=order_data)
        self._oanda_price_streamer.update_necessary = True

    def get_balance(self):
        ret_value = {}
        net_worth = self.get_net_worth()
        ret_value[self._account_currency] = net_worth

        try:
            response = self._oanda.get_positions(self._account_id)
        except:
            self._oanda_price_streamer.update_necessary = True
            return ret_value

        if not response or not response['positions']:
            return ret_value

        for item in response['positions']:
            if item['short']:
                value = item['short']['units']
            else:
                value = item['long']['units']
            ret_value[self._account_currency] = ret_value[self._account_currency] + \
                float(value)

        return ret_value

    def cash_invested(self):
        try:
            response = self._oanda.get_account(self._account_id)
            margin_used = float(response['margin_used'])
            return margin_used
        except:
            return 0.0

    def leverage(self):
        try:
            response = self._oanda.get_account(self._account_id)
        except:
            self._oanda_price_streamer.update_necessary = True
            return 0.0
        margin_rate = float(response['account']['marginRate'])
        leverage = 1.0 / margin_rate
        return leverage

    def unrealized_pnl(self):
        try:
            response = self._oanda.get_account(self._account_id)
        except:
            self._oanda_price_streamer.update_necessary = True
            return 0.0
        return float(response['account']['unrealizedPL'])

    def current_position(self):
        try:
            response = self._oanda.get_position(self._account_id,
                                                self._instrument)
            long_units = response['position']['long']['units']
            short_units = response['position']['short']['units']
            return int(long_units) + int(short_units)
        except Exception as error:
            logging.error(error)
            self._oanda_price_streamer.update_necessary = True
            return 0

    def current_side(self):
        try:
            response = self._oanda.get_position(self._account_id,
                                                self._instrument)
            long_units = response['position']['long']['units']
            short_units = response['position']['short']['units']
            units = int(long_units) + int(short_units)
            if units < 0:
                return MarketTrend.ENTER_SHORT
            if units > 0:
                return MarketTrend.ENTER_LONG
        except:
            self._oanda_price_streamer.update_necessary = True

        return MarketTrend.NONE

    def available_units(self):
        exchange_rate = self._home_base_default_exchange_rate
        response = self._oanda.get_prices(
            self._account_id, instruments=self._home_base_pair)
        exchange_rate = (
            float(response['prices'][0]['bids'][0]['price']) +
            float(response['prices'][0]['asks'][0]['price'])) / 2.0

        try:
            response = self._oanda.get_account(self._account_id)
            margin_available = float(response['account']['marginAvailable'])
            margin_rate = float(response['account']['marginRate'])
            leverage = 1.0 / margin_rate
            response = self._oanda.get_prices(
                self._account_id, instruments=self._instrument)
            return int(floor(margin_available * leverage / exchange_rate))
        except:
            self._oanda_price_streamer.update_necessary = True
            return 0

    def sell(self, units):
        order_data = {
            'order': {
                'type': 'MARKET',
                'instrument': self._instrument,
                'units': units * -1,
            },
        }

        self._oanda_price_streamer.update_necessary = True
        response = self._oanda.create_order(
            self._account_id, params=order_data)

        logging.debug(response)

        if 'errorCode' in response:
            return False

        return True

    def buy(self, units):
        order_data = {
            'order': {
                'type': 'MARKET',
                'instrument': self._instrument,
                'units': units,
            },
        }

        self._oanda_price_streamer.update_necessary = True
        response = self._oanda.create_order(
            self._account_id, params=order_data)

        logging.debug(response)

        if 'errorCode' in response:
            return False

        return True

    def get_candles(self, last_candles=0, size=120):
        candles = []

        if last_candles <= 0 or size <= 0:
            return candles

        _granularity = get_granularity(size)
        response = self._oanda.get_history(
            instrument=self._instrument,
            granularity=_granularity,
            count=last_candles + 1,
            candleFormat='midpoint')

        if 'candles' not in response:
            return candles

        for item in response['candles']:
            if item['complete'] is not True:
                continue

            close_ts = dateutil.parser.parse(item['time'])
            open_ts = close_ts - \
                datetime.timedelta(minutes=size)

            close_ts = time.mktime(close_ts.timetuple()) + \
                close_ts.microsecond * 0.000001
            open_ts = time.mktime(open_ts.timetuple()) + \
                open_ts.microsecond * 0.000001

            candle = Candle(open_ts, close_ts)
            candle.open = item['mid']['o']
            candle.high = item['mid']['h']
            candle.low = item['mid']['l']
            candle.close = item['mid']['c']
            candle.set_closed(True)
            candles.append(candle)

        self._oanda_price_streamer.update_necessary = True

        return sorted(candles, key=lambda candle: candle.CloseTime)

    def is_running(self):
        return self._oanda_price_streamer.is_running()

    def update_subscribers(self):
        self._oanda_price_streamer.update_subscribers()


def get_granularity(size_in_minutes):
    size = 'H2'
    if size_in_minutes == 2:
        size = 'M2'
    elif size_in_minutes == 3:
        size = 'M3'
    elif size_in_minutes == 4:
        size = 'M4'
    elif size_in_minutes == 5:
        size = 'M5'
    elif size_in_minutes == 10:
        size = 'M10'
    elif size_in_minutes == 15:
        size = 'M15'
    elif size_in_minutes == 30:
        size = 'M30'
    elif size_in_minutes == 60:
        size = 'H1'
    elif size_in_minutes == 120:
        size = 'H2'
    elif size_in_minutes == 240:
        size = 'H4'
    elif size_in_minutes == 480:
        size = 'H8'
    elif size_in_minutes == 1440:
        size = 'D1'
    return size


def oanda_exception_code(exception):
    if not exception:
        return 0
    match = re.match(r'OANDA API returned error code ([0-9]+)\s.*',
                     str(exception))
    if not match:
        return 1
    return match.group(1)
