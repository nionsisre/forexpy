import datetime
import time
import math
import os
import logging
from tqdm import tqdm
from exchange import oandapy
from logic import MarketTrend
from logic.candle import Candle
from logic.strategy import Strategy

logging.basicConfig(filename='backtest.log',
                    level=logging.INFO,
                    format="%(asctime)-15s %(message)s"
                    )

HOME_CURRENCY = "HOME"
INSTRUMENT = "INSTR"

class OandaBacktest(object):

    def __init__(self, in_filename, leverage = 20.0, account_value = 10000.0):
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
        self.total_PnL = 0.0
        self.last_update_timestamp = None

        self.plot_data = {}
        self.plot_data["RawPrice"] = []
        self.plot_data["Sell"] = []
        self.plot_data["Buy"] = []
        self.plot_data["Close"] = []
        self.plot_data["StopLoss"] = []
        self.plot_data["TrailingStop"] = []
        self.plot_data["NetWorth"] = []
        self.plot_data["short"] = []
        self.plot_data["medium"] = []
        self.plot_data["long"] = []

    def SubscribeTicker(self, obj):
        self.ticker_subscribers.append(obj)

    def StartPriceStreaming(self):
        if self.file:
            return
        self.file_size = os.stat(self.in_filename).st_size
        self.pbar = tqdm(total=self.file_size)
        self.file = open(self.in_filename, "r")

    def StopPriceStreaming(self):
        if not self.file:
            return
        self.file.close()
        self.file = None
        self.pbar.close()
        print(("Total PnL: " + str(self.total_PnL) + " NetWorth: " + str(self.GetNetWorth())))

    def GetNetWorth(self):
        net_worth = 0.0
        for position in self.balance:
            if position == HOME_CURRENCY:
                net_worth += self.balance[position]
            else:
                net_worth += self.balance[position] * self.current_price / self.Leverage()
        return net_worth

    def GetBalance(self):
        return self.balance

    def CashInvested(self):
        return self.cash_invested

    def CurrentPosition(self):
        return self.position

    def CurrentPositionSide(self):
        return self.position_side

    def Leverage(self):
        return self.leverage

    def AvailableUnits(self):
        result = self.GetNetWorth() * self.Leverage() / self.current_price
        result = max(0,int(math.floor(result)))
        return result

    def UnrealizedPNL(self):
        price_diff = 0.0

        if self.position_side == MarketTrend.ENTER_LONG:
            price_diff = self.current_price - self.last_entered_price

        if self.position_side == MarketTrend.ENTER_SHORT:
            price_diff = self.last_entered_price - self.current_price

        return self.position * price_diff

    def ClosePosition(self, position):
        # Nothing to close - no positions open
        if (INSTRUMENT not in self.balance) or (not self.balance[INSTRUMENT]):
            return

        if self.balance[INSTRUMENT] > 0.0:
            realizedPnL = (abs(self.balance[INSTRUMENT]) * self.current_price) - (self.cash_invested)
            realizedPnL *= self.Leverage()
            self.balance[HOME_CURRENCY] += self.cash_invested / self.Leverage()
        else:
            realizedPnL = (self.cash_invested) - (abs(self.balance[INSTRUMENT]) * self.current_price)
            realizedPnL *= self.Leverage()
            self.balance[HOME_CURRENCY] -= self.cash_invested / self.Leverage()

        self.balance[HOME_CURRENCY] += realizedPnL
        self.balance[INSTRUMENT] = 0.0
        self.position = 0.0

        logging_str  = "Trade closed (" + str(datetime.datetime.fromtimestamp(self.last_update_timestamp)) + "): "
        logging_str += str(self.position_side)
        logging_str += " from: " + str(self.last_entered_price)
        logging_str += " to: " + str(self.current_price)
        logging_str += ". Realized PnL: " + str(realizedPnL)
        logging_str += " NetWorth: " + str(self.GetNetWorth())
        logging.info(logging_str)

        self.position_side = MarketTrend.NONE

        self.total_PnL += realizedPnL

        self._createPlotRecord("Close")

    def Sell(self, units):
        self.position = units
        self.position_side = MarketTrend.ENTER_SHORT
        self.balance[INSTRUMENT] -= units
        self.balance[HOME_CURRENCY] += (units * self.current_price) / self.Leverage()
        self.cash_invested = units * self.current_price
        self.last_entered_price = self.current_price

        self._createPlotRecord("Sell")

    def Buy(self, units):
        self.position = units
        self.position_side = MarketTrend.ENTER_LONG

        self.balance[HOME_CURRENCY] -= (units * self.current_price) / self.Leverage()
        self.balance[INSTRUMENT] += units
        self.cash_invested = units * self.current_price
        self.last_entered_price = self.current_price

        self._createPlotRecord("Buy")

    def GetCandles(self, number_of_last_candles_to_get = 0, size_of_candles_in_minutes = 120):
        candles = []
        for i in range(1,number_of_last_candles_to_get):
            candles.append(self.GetCandle(size_of_candles_in_minutes))
        return candles

    def GetCandle(self, candleSize):
        price, datapoint = self.getNextLine()
        openTime = datapoint["now"]
        closeTime = datetime.datetime.fromtimestamp(datapoint["now"]) + datetime.timedelta(minutes=candleSize)
        closeTime = time.mktime(closeTime.timetuple()) + closeTime.microsecond * 0.000001
        candle = Candle(openTime, closeTime)
        while not candle.SeenEnoughData():
            price, datapoint = self.getNextLine()
            candle.Update(datapoint)
        return candle

    def IsRunning(self):
        return self.file != None

    def getNextLine(self):
        if not self.file:
            return
        line = self.file.readline()
        self.pbar.update(len(line))
        if not line:
            self.StopPriceStreaming

        try:
            date, bid, ask, bidVol, askVol = line.split(",")
        except:
            self.StopPriceStreaming()
            return

        price = float(bid)
        #histdata
        #ts = time.mktime(time.strptime(days + ' ' + minutes, '%Y.%m.%d %H:%M'))
        ts = time.mktime(time.strptime(date, '%Y-%m-%d %H:%M:%S'))

        # form a ticker
        datapoint = {}
        datapoint["now"] = ts
        datapoint["value"] = price

        return price, datapoint

    def UpdateSubscribers(self):
        # get a line
        if not self.file:
            return

        try:
            price, datapoint = self.getNextLine()
        except:
            return

        self.last_update_timestamp = datapoint["now"]
        self.current_price = price

        # push to all subscribers
        for obj in self.ticker_subscribers:
            obj.Update(datapoint)
            # For plotting stops
            try:
                self._createPlotRecord("StopLoss", obj.GetStopLossPrice())
                self._createPlotRecord("TrailingStop", obj.GetTrailingStopPrice())
            except:
                pass

        self._createPlotRecord("RawPrice")
        self._createPlotRecord("NetWorth", self.GetNetWorth())


    def GetPlotData(self):
        return self.plot_data

    def _createPlotRecord(self, plot_name, value = None):
        if not value:
            value = self.current_price
        tmp = {}
        tmp["now"] = self.last_update_timestamp
        tmp["value"] = value
        self.plot_data[plot_name].append(tmp)
        del tmp
