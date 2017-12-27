import datetime
import time
from exchange.oanda import Oanda
from logic.candle import Candle
from logic import movingaverage
from logic import MarketTrend
from logic.stoploss import StopLoss
from logic.trailingstop import TrailingStop
from logic.takeprofit import TakeProfit
from logic.risk import RiskManager
from logic.timestop import TimeStop
from logic.macross import MACross
import logging
import traceback
import numpy
import talib
from settings import PLOT_RESULTS


class Strategy(object):

    SHORT_EMA_PERIOD = 7
    MEDIUM_EMA_PERIOD = 26
    LONG_SMA_PERIOD = 50

    def __init__(self,
                 oanda,
                 candle_size=120,
                 email=None,
                 risk=2,
                 stoploss=20,
                 trailing_period=7,
                 take_profit=20):
        self._oanda = oanda
        self._oanda.subscribe_ticker(self)
        self._current_candle = None
        self._candle_size = candle_size
        self._risk = RiskManager(oanda, risk)
        self._stop_loss = stoploss
        self._take_profit = take_profit
        self._email = email
        self._macross = MACross(
                Strategy.SHORT_EMA_PERIOD,
                Strategy.MEDIUM_EMA_PERIOD,
                Strategy.LONG_SMA_PERIOD)
        self._sl_indicator = StopLoss(trailing_period)
        self._tp_indicator = TakeProfit()
        self._timestop = TimeStop()
        self._logging_current_price = 0.0
        self.trading_enabled = False

    def Start(self):
        logging.info("Starting strategy")
        # Prefeed the strategy with historic candles
        candle_count = self._macross.amount_of_data_still_missing() + 1
        self._oanda.start_price_streaming()
        candles = self._oanda.get_candles(candle_count, self._candle_size)
        for c in candles:
            self._macross.update(c)
            self._sl_indicator.update(c)
            self._tp_indicator.update(c)
        self.trading_enabled = True

    def PauseTrading(self):
        logging.info("Pausing strategy")
        self.trading_enabled = False

    def ResumeTrading(self):
        logging.info("Resuming strategy")
        self.trading_enabled = True

    def TradingStatus(self):
        return self.trading_enabled

    def SetTradingStatus(self, tstatus):
        self.trading_enabled = tstatus

    def stop(self):
        logging.info("Stop strategy")
        self.SetTradingStatus(False)
        self._oanda.StopPriceStreaming()

    def update(self, datapoint):
        if not isinstance(datapoint, Candle):
            if not self._current_candle or self._current_candle.seen_enough_data(
            ):
                openTime = datapoint["now"]
                closeTime = datetime.datetime.fromtimestamp(
                    datapoint["now"]) + datetime.timedelta(
                        minutes=self._candle_size)
                closeTime = time.mktime(
                    closeTime.timetuple()) + closeTime.microsecond * 0.000001
                self._current_candle = Candle(openTime, closeTime)
                self._current_candle.update(datapoint)
            else:
                self._current_candle.update(datapoint)
            self._sl_indicator.update(datapoint)
            self._tp_indicator.update(datapoint)
            self._logging_current_price = datapoint["value"]
        else:
            self._current_candle = datapoint
            self._logging_current_price = datapoint.close

        # Check if it is Friday night and we should seize trading
        self._timestop.update(datapoint)
        _state = self._timestop.GetState()
        if _state == MarketTrend.STOP_LONG or _state == MarketTrend.STOP_SHORT:
            if (self._oanda.current_position() != 0):
                logging.info("Timing Stop fired, TGIF!: " + str(_state) +
                             " price: " + str(self._logging_current_price))
                self.ClosePosition('short')
                self.ClosePosition('long')
                return

        if not self._current_candle.seen_enough_data():
            return

        self._macross.update(self._current_candle)
        self._sl_indicator.update(self._current_candle)
        self._tp_indicator.update(self._current_candle)

        sl = self._sl_indicator.GetState()
        if sl == MarketTrend.STOP_LONG or sl == MarketTrend.STOP_SHORT:
            if self._oanda.current_position() != 0:
                self.ClosePosition('both')
                logging.info(
                    "STOP called @ " + str(self._logging_current_price))
                self._sl_indicator.CancelStop()
                return

        tp = self._tp_indicator.GetState()
        if tp == MarketTrend.STOP_LONG or tp == MarketTrend.STOP_SHORT:
            if self._oanda.current_position() != 0:
                self.ClosePosition('both')
                logging.info(
                    "TAKE PROFIT called @ " + str(self._logging_current_price))
                self._tp_indicator.CancelTakeProfit()
                return

        ma = self._macross.GetState()
        if ma == MarketTrend.ENTER_LONG:
            if self._oanda.current_position() != 0 and self._oanda.current_side(
            ) == MarketTrend.ENTER_LONG:
                return
            else:
                self.ClosePosition('short')
                self._tp_indicator.SetTakeProfit(
                    self._logging_current_price - self._take_profit,
                    MarketTrend.ENTER_LONG)
                self._sl_indicator.SetStop(
                    self._logging_current_price - self._stop_loss,
                    MarketTrend.ENTER_LONG)
                self.Buy()
                return
        elif ma == MarketTrend.ENTER_SHORT:
            if self._oanda.current_position() != 0 and self._oanda.current_side(
            ) == MarketTrend.ENTER_SHORT:
                return
            else:
                self.ClosePosition('long')
                self._tp_indicator.SetTakeProfit(
                    self._logging_current_price + self._take_profit,
                    MarketTrend.ENTER_SHORT)
                self._sl_indicator.SetStop(
                    self._logging_current_price - self._stop_loss,
                    MarketTrend.ENTER_SHORT)
                self.Sell()
                return

    def Buy(self):
        logging.info("Strategy Buy() called. Going long @ " +
                     str(self._logging_current_price))

        if not self.trading_enabled:
            logging.info("Strategy trading disabled, doing nothing")
            return

        # Enter the long position on the instrument
        units = self._risk.GetLongPositionSize()
        if units == 0:
            logging.info("Cant trade zero units, doing nothing")
            return

        try:
            self._oanda.buy(units)
        except Exception as e:
            self._catchTradeException(e, "enter long")

    def Sell(self):
        logging.info("Strategy Sell() called. Going short @ " +
                     str(self._logging_current_price))
        if not self.trading_enabled:
            logging.info("Trading disabled, doing nothing")
            return

        # Enter the short position on the instrument
        units = self._risk.GetShortPositionSize()
        logging.info(
            "Got the number of units to trade from RiskManager: " + str(units))
        if units == 0:
            logging.info("Cant trade 0 units, doing nothing")
            return

        try:
            self._oanda.sell(units)
        except Exception as e:
            self._catchTradeException(e, "enter short")

    def ClosePosition(self, position):
        logging.info("Closing %s position, and all stops" % position)
        self._sl_indicator.CancelStop()
        if not self.trading_enabled:
            logging.info("Trading disabled, doing nothing")
            return

        try:
            self._oanda.close_position(position)
        except Exception as e:
            self._catchTradeException(e, "close")

    def GetStopLossPrice(self):
        return 0.0

    def GetTakeProfitPrice(self):
        return self._tp_indicator.GetPrice(self._oanda.current_side())

    def GetTrailingStopPrice(self):
        return self._sl_indicator.GetPrice()

    def _catchTradeException(self, e, position):
        logging.critical("Failed to " + position + " position")
        logging.critical(traceback.format_exc())
        if self._email:
            txt = "\n\nError while trying to " + position + " position\n"
            txt += "It was caught, I should still be running\n\n"
            txt += traceback.format_exc() + "\n" + str(e)
            self._email.Send(txt)
