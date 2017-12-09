from datetime import datetime, timedelta
import time
import math
import os
import logging
from tqdm import tqdm
from logic import MarketTrend
from logic.candle import Candle

logging.basicConfig(
    filename='backtest.log',
    filemode='w',
    level=logging.INFO,
    format='%(asctime)-15s %(message)s')

HOME_CURRENCY = 'HOME'
INSTRUMENT = 'INSTR'


class OandaBacktest(object):

    def __init__(self, in_filename, leverage=20.0, account_value=10000.0):
        self.leverage = leverage
        self.net_worth = account_value
        self.ticker_subscribers = []
        self.file = None
        self.in_filename = in_filename
        self.position = 0
        self.position_side = MarketTrend.NONE
        self.cash_invested = 0.0
        self.current_price = 0.0
        self.last_entered_price = 0.0
        self.balance = {HOME_CURRENCY: account_value, INSTRUMENT: 0.0}
        self.total_pnl = 0.0
        self.last_update_timestamp = None
        self.shorts = 0
        self.longs = 0
        self.won_shorts = 0
        self.won_longs = 0
        self.pbar = None
        self.plot_data = {}
        self.plot_data['RawPrice'] = []
        self.plot_data['Sell'] = []
        self.plot_data['Buy'] = []
        self.plot_data['Close'] = []
        self.plot_data['StopLoss'] = []
        self.plot_data['TrailingStop'] = []
        self.plot_data['TakeProfit'] = []
        self.plot_data['NetWorth'] = []
        self.plot_data['short'] = []
        self.plot_data['medium'] = []
        self.plot_data['long'] = []

    def subscribe_ticker(self, obj):
        self.ticker_subscribers.append(obj)

    def start_price_streaming(self):
        file_size = os.stat(self.in_filename).st_size
        self.pbar = tqdm(total=file_size, leave=False, mininterval=1,
                         ascii=True)
        self.file = open(self.in_filename, 'r')

    def stop_price_streaming(self):
        if not self.file:
            return
        self.file.close()
        self.file = None
        self.pbar.close()
        longwons = float('{0:.2f}'.format(self.won_longs / self.longs * 100))
        shortwons = float('{0:.2f}'.format(self.won_shorts / self.shorts * 100))
        print('Total PnL: ' + '{0:.2f}'.format(self.total_pnl) + ' NetWorth: ' +
              '{0:.2f}'.format(self.get_net_worth()))
        print('Longs: {} ({}% won)'.format(self.longs, longwons))
        print('Shorts: {} ({}% won)'.format(self.shorts, shortwons))

    def get_net_worth(self):
        net_worth = 0.0
        for position in self.balance:
            if position == HOME_CURRENCY:
                net_worth += self.balance[position]
            else:
                net_worth += self.balance[position] * \
                    self.current_price / self.leverage
        return net_worth

    def get_balance(self):
        return self.balance

    def get_cash_invested(self):
        return self.cash_invested

    def current_position(self):
        return self.position

    def current_side(self):
        return self.position_side

    def get_leverage(self):
        return self.leverage

    def available_units(self):
        result = self.get_net_worth() * self.leverage / self.current_price
        result = max(0, int(math.floor(result)))
        return result

    def unrealized_pnl(self):
        price_diff = 0.0

        if self.position_side == MarketTrend.ENTER_LONG:
            price_diff = self.current_price - self.last_entered_price

        if self.position_side == MarketTrend.ENTER_SHORT:
            price_diff = self.last_entered_price - self.current_price

        return self.position * price_diff

    def close_position(self, _):
        # Nothing to close - no positions open
        if (INSTRUMENT not in self.balance) or (not self.balance[INSTRUMENT]):
            return

        if self.balance[INSTRUMENT] > 0.0:
            realized_pnl = (abs(self.balance[INSTRUMENT]) *
                            self.current_price) - (self.cash_invested)
            realized_pnl *= self.leverage
            self.balance[HOME_CURRENCY] += self.cash_invested / self.leverage
        else:
            realized_pnl = (self.cash_invested) - \
                (abs(self.balance[INSTRUMENT]) * self.current_price)
            realized_pnl *= self.leverage
            self.balance[HOME_CURRENCY] -= self.cash_invested / self.leverage

        self.balance[HOME_CURRENCY] += realized_pnl
        self.balance[INSTRUMENT] = 0.0
        self.position = 0.0

        if self.position_side == MarketTrend.ENTER_LONG:
            self.longs += 1
            if realized_pnl >= 0:
                self.won_longs += 1
        else:
            self.shorts += 1
            if realized_pnl >= 0:
                self.won_shorts += 1

        logging_str = 'Trade closed (' + str(
            datetime.fromtimestamp(self.last_update_timestamp)) + '): '
        logging_str += str(self.position_side)
        logging_str += ' from: ' + str(self.last_entered_price)
        logging_str += ' to: ' + str(self.current_price)
        logging_str += '. Realized PnL: ' + str(realized_pnl)
        logging_str += ' NetWorth: ' + str(self.get_net_worth())
        logging.info(logging_str)

        self.position_side = MarketTrend.NONE

        self.total_pnl += realized_pnl

        self._create_plot_record('Close')

    def sell(self, units):
        self.position = units
        self.position_side = MarketTrend.ENTER_SHORT
        self.balance[INSTRUMENT] -= units
        self.balance[HOME_CURRENCY] += (
            units * self.current_price) / self.leverage
        self.cash_invested = units * self.current_price
        self.last_entered_price = self.current_price

        self._create_plot_record('Sell')

    def buy(self, units):
        self.position = units
        self.position_side = MarketTrend.ENTER_LONG

        self.balance[HOME_CURRENCY] -= (
            units * self.current_price) / self.leverage
        self.balance[INSTRUMENT] += units
        self.cash_invested = units * self.current_price
        self.last_entered_price = self.current_price

        self._create_plot_record('Buy')

    def get_candles(self,
                    number_of_last_candles_to_get=0,
                    size_of_candles_in_minutes=120):
        candles = []
        for _ in range(1, number_of_last_candles_to_get):
            candles.append(self.get_candle(size_of_candles_in_minutes))
        return candles

    def get_candle(self, candle_size):
        _, datapoint = self.get_next_line()
        open_time = datapoint['now']
        close_time = datetime.fromtimestamp(
            datapoint['now']) + timedelta(minutes=candle_size)
        close_time = time.mktime(close_time.timetuple()) + \
            close_time.microsecond * 0.000001
        candle = Candle(open_time, close_time)
        candle.update(datapoint)
        while not candle.seen_enough_data():
            _, datapoint = self.get_next_line()
            candle.update(datapoint)
        return candle

    def is_running(self):
        return self.file is not None

    def get_next_line(self):
        if not self.file:
            return
        line = self.file.readline()
        self.pbar.update(len(line))
        if not line:
            self.stop_price_streaming()

        date, bid, _, _, _ = line.split(',')

        price = float(bid)
        timestamp = self.parseTime(date)

        # form a ticker
        datapoint = {}
        datapoint['now'] = timestamp
        datapoint['value'] = price

        return price, datapoint

    def parseTime(self, input_date):
        year = int(input_date[:4])
        month = int(input_date[5:7])
        day = int(input_date[8:10])
        hour = int(input_date[11:13])
        minute = int(input_date[14:16])
        second = int(input_date[17:19])
        microsecond = input_date[20:26]
        if microsecond == '':
            microsecond = 0
        else:
            microsecond = int(microsecond)
        return datetime(year, month, day, hour, minute, second,
                        microsecond).timestamp()

    def update_subscribers(self):
        # get a line
        if not self.file:
            return

        try:
            price, datapoint = self.get_next_line()
        except:
            return

        self.last_update_timestamp = datapoint['now']
        self.current_price = price

        # push to all subscribers
        for obj in self.ticker_subscribers:
            obj.update(datapoint)
            # For plotting stops
            self._create_plot_record('StopLoss', obj.GetStopLossPrice())
            self._create_plot_record('TrailingStop', obj.GetTrailingStopPrice())
            self._create_plot_record('TakeProfit', obj.GetTakeProfitPrice())

        self._create_plot_record('RawPrice')
        self._create_plot_record('NetWorth', self.get_net_worth())

    def get_plot_data(self):
        return self.plot_data

    def _create_plot_record(self, plot_name, value=None):
        if not value:
            value = self.current_price
        tmp = {}
        tmp['now'] = self.last_update_timestamp
        tmp['value'] = value
        self.plot_data[plot_name].append(tmp)
        del tmp
