import datetime
import time
from exchange.oanda import Oanda
from logic.candle import Candle
from logic import movingaverage
from logic import MarketTrend
from logic.stoploss import StopLoss
from logic.trailingstop import TrailingStop
from logic.risk import RiskManager
from logic.timestop import TimeStop
import logging
import traceback
import numpy
import talib

class Strategy(object):

    SHORT_EMA_PERIOD = 12
    MEDIUM_EMA_PERIOD = 26
    LONG_SMA_PERIOD = 55

    def __init__(self, oanda, candle_size = 120, email = None, risk = 2, stoploss = 20):
        self._oanda = oanda
        self._oanda.SubscribeTicker(self)
        self._current_candle = None
        self._candle_size = candle_size
        self._risk = RiskManager(oanda, risk)
        self._stop_loss = stoploss
        self._email = email
        self._short_ema = movingaverage.ExponentialMovingAverage(Strategy.SHORT_EMA_PERIOD)
        self._medium_ema = movingaverage.ExponentialMovingAverage(Strategy.MEDIUM_EMA_PERIOD)
        self._long_sma = movingaverage.SimpleMovingAverage(Strategy.LONG_SMA_PERIOD)
        self._sl_indicator = TrailingStop()
        self._timestop = TimeStop()
        self._logging_current_price = 0.0
        self.trading_enabled = False

    def Start(self):
        logging.info("Starting strategy")
        # Prefeed the strategy with historic candles
        candle_count = self._long_sma.AmountOfDataStillMissing() + 1
        self._oanda.StartPriceStreaming()
        Candles = self._oanda.GetCandles(candle_count, self._candle_size)
        for c in Candles:
            self._short_ema.Update(c)
            self._medium_ema.Update(c)
            self._long_sma.Update(c)
            self._sl_indicator.Update(c)
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

    def Stop(self):
        logging.info("Stop strategy")
        self.SetTradingStatus(False)
        self._oanda.StopPriceStreaming()

    def Update(self, datapoint):
        if not isinstance(datapoint, Candle):
            if not self._current_candle or self._current_candle.SeenEnoughData():
                openTime = datapoint["now"]
                closeTime = datetime.datetime.fromtimestamp(datapoint["now"]) + datetime.timedelta(minutes=self._candle_size)
                closeTime = time.mktime(closeTime.timetuple()) + closeTime.microsecond * 0.000001
                self._current_candle = Candle(openTime, closeTime)
            else:
                self._current_candle.Update(datapoint)
            self._sl_indicator.Update(datapoint)
            self._logging_current_price = datapoint["value"]
        else:
            self._current_candle = datapoint
            self._logging_current_price = datapoint.Close

        # Check if it is Friday night and we should seize trading
        self._timestop.Update(datapoint)
        _state = self._timestop.GetState()
        if _state == MarketTrend.STOP_LONG or _state == MarketTrend.STOP_SHORT:
            if (self._oanda.CurrentPosition() != 0):
                logging.info("Timing Stop fired, TGIF!: "+str(_state) + " price: "+ str(self._logging_current_price))
                self.ClosePosition('short')
                self.ClosePosition('long')
                return

        if not self._current_candle.SeenEnoughData():
            return

        self._short_ema.Update(self._current_candle)
        self._medium_ema.Update(self._current_candle)
        self._long_sma.Update(self._current_candle)

        self._oanda._createPlotRecord("short", self._short_ema.value)
        self._oanda._createPlotRecord("medium", self._medium_ema.value)
        self._oanda._createPlotRecord("long", self._long_sma.value)

        sl = self._sl_indicator.GetState()
        if sl == MarketTrend.STOP_LONG or sl == MarketTrend.STOP_SHORT:
            if self._oanda.CurrentPosition() != 0:
                self.ClosePosition('both')
                logging.info("STOP called @ " + str(self._logging_current_price))
                self._sl_indicator.CancelStop()
                return

        if self._short_ema.value > self._medium_ema.value and self._short_ema.value > self._long_sma.value:
            if self._oanda.CurrentPosition() != 0 and self._oanda.CurrentPositionSide() == MarketTrend.ENTER_LONG:
                return
            else:
                self.ClosePosition('short')
                self._sl_indicator.SetStop(MarketTrend.ENTER_LONG)
                self.Buy()

        if (self._short_ema.value < self._medium_ema.value and self._short_ema.value > self._long_sma.value):
            if self._oanda.CurrentPosition() != 0 and self._oanda.CurrentPositionSide() == MarketTrend.ENTER_SHORT:
                return
            else:
                self.ClosePosition('long')
                self._sl_indicator.SetStop(MarketTrend.ENTER_SHORT)
                self.Sell()

    def Buy(self):
        logging.info("Strategy Buy() called. Going long @ " + str(self._logging_current_price))

        if not self.trading_enabled:
            logging.info("Strategy trading disabled, doing nothing")
            return

        # Enter the long position on the instrument
        units = self._risk.GetLongPositionSize()
        if units == 0:
            logging.info("Cant trade zero units, doing nothing")
            return

        try:
            self._oanda.Buy(units)
        except Exception as e:
            self._catchTradeException(e,"enter long")

    def Sell(self):
        logging.info("Strategy Sell() called. Going short @ " + str(self._logging_current_price))
        if not self.trading_enabled:
            logging.info("Trading disabled, doing nothing")
            return

        # Enter the short position on the instrument
        units = self._risk.GetShortPositionSize()
        logging.info("Got the number of units to trade from RiskManager: "+str(units))
        if units == 0:
            logging.info("Cant trade 0 units, doing nothing")
            return

        try:
            self._oanda.Sell(units)
        except Exception as e:
            self._catchTradeException(e,"enter short")

    def ClosePosition(self, position):
        logging.info("Closing %s position, and all stops" % position)
        self._sl_indicator.CancelStop()
        if not self.trading_enabled:
            logging.info("Trading disabled, doing nothing")
            return

        try:
            self._oanda.ClosePosition(position)
        except Exception as e:
            self._catchTradeException(e,"close")

    def GetStopLossPrice(self):
        return 0.0

    def GetTrailingStopPrice(self):
        return 0.0

    def _catchTradeException(self, e, position):
            logging.critical("Failed to "+position+" position")
            logging.critical(traceback.format_exc())
            if self._email:
                txt = "\n\nError while trying to "+position+" position\n"
                txt += "It was caught, I should still be running\n\n"
                txt += traceback.format_exc()+"\n"+str(e)
                self._email.Send(txt)
