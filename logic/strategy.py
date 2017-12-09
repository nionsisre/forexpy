from datetime import timedelta
from logic.candle import Candle
from logic import movingaverage
from logic import MarketTrend
from logic.trailingstop import TrailingStop
from logic.takeprofit import TakeProfit
from logic.risk import RiskManager
from logic.timestop import TimeStop
import traceback


class Strategy(object):

    SHORT_EMA_PERIOD = 10
    MEDIUM_EMA_PERIOD = 50
    LONG_SMA_PERIOD = 100

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
        self._short_ema = movingaverage.ExponentialMovingAverage(
            Strategy.SHORT_EMA_PERIOD)
        self._medium_ema = movingaverage.ExponentialMovingAverage(
            Strategy.MEDIUM_EMA_PERIOD)
        self._long_sma = movingaverage.SimpleMovingAverage(
            Strategy.LONG_SMA_PERIOD)
        self._previous_cross = [False, False]
        self._current_cross = [False, False]
        self._sl_indicator = TrailingStop(trailing_period)
        self._tp_indicator = TakeProfit()
        self._timestop = TimeStop()
        self._logging_current_price = 0.0
        self.trading_enabled = False

    def Start(self):
        # Prefeed the strategy with historic candles
        candle_count = self._long_sma.AmountOfDataStillMissing() + 1
        self._oanda.start_price_streaming()
        candles = self._oanda.get_candles(candle_count, self._candle_size)
        for c in candles:
            self._short_ema.update(c)
            self._medium_ema.update(c)
            self._long_sma.update(c)
            self._sl_indicator.update(c)
            self._tp_indicator.update(c)
        self.trading_enabled = True

    def PauseTrading(self):
        self.trading_enabled = False

    def ResumeTrading(self):
        self.trading_enabled = True

    def TradingStatus(self):
        return self.trading_enabled

    def SetTradingStatus(self, tstatus):
        self.trading_enabled = tstatus

    def stop(self):
        self.SetTradingStatus(False)
        self._oanda.StopPriceStreaming()

    def update(self, datapoint):
        if not isinstance(datapoint, Candle):
            if not self._current_candle or self._current_candle.seen_enough_data(
            ):
                openTime = datapoint["now"]
                closeTime = datapoint["now"] + timedelta(
                    minutes=self._candle_size)
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
                self.ClosePosition('short')
                self.ClosePosition('long')
                return

        if not self._current_candle.seen_enough_data():
            return

        self._short_ema.update(self._current_candle)

        if self._short_ema.value < 1:
            print(self._current_candle)
        self._medium_ema.update(self._current_candle)
        self._long_sma.update(self._current_candle)
        self._sl_indicator.update(self._current_candle)
        self._tp_indicator.update(self._current_candle)

        self._oanda._create_plot_record("short", self._short_ema.value)
        self._oanda._create_plot_record("medium", self._medium_ema.value)
        self._oanda._create_plot_record("long", self._long_sma.value)

        self._previous_cross = self._current_cross
        self._current_cross = self.check_crosses()

        sl = self._sl_indicator.GetState()
        if sl == MarketTrend.STOP_LONG or sl == MarketTrend.STOP_SHORT:
            if self._oanda.current_position() != 0:
                self.ClosePosition('both')
                self._sl_indicator.CancelStop()
                return

        tp = self._tp_indicator.GetState()
        if tp == MarketTrend.STOP_LONG or tp == MarketTrend.STOP_SHORT:
            if self._oanda.current_position() != 0:
                self.ClosePosition('both')
                self._tp_indicator.CancelTakeProfit()
                return

        if self._previous_cross[0] == False and self._current_cross[0] == True:
            if self._oanda.current_position(
            ) != 0 and self._oanda.current_side() == MarketTrend.ENTER_LONG:
                return
            else:
                self.ClosePosition('short')
                self._tp_indicator.SetTakeProfit(
                    self._logging_current_price - self._take_profit,
                    MarketTrend.ENTER_LONG)
                self._sl_indicator.SetStop(MarketTrend.ENTER_LONG)
                self.Buy()

        if self._previous_cross[1] == False and self._current_cross[1] == True:
            if self._oanda.current_position(
            ) != 0 and self._oanda.current_side() == MarketTrend.ENTER_SHORT:
                return
            else:
                self.ClosePosition('long')
                self._tp_indicator.SetTakeProfit(
                    self._logging_current_price + self._take_profit,
                    MarketTrend.ENTER_LONG)
                self._sl_indicator.SetStop(MarketTrend.ENTER_SHORT)
                self.Sell()

    def check_crosses(self):
        buycross = self._short_ema.value > self._medium_ema.value and self._short_ema.value > self._long_sma.value
        sellcross = self._short_ema.value < self._medium_ema.value and self._short_ema.value < self._long_sma.value
        return [buycross, sellcross]

    def Buy(self):
        if not self.trading_enabled:
            return

        # Enter the long position on the instrument
        units = self._risk.GetLongPositionSize()
        if units == 0:
            return

        try:
            self._oanda.buy(units)
        except Exception as e:
            self._catchTradeException(e, "enter long")

    def Sell(self):
        if not self.trading_enabled:
            return

        # Enter the short position on the instrument
        units = self._risk.GetShortPositionSize()
        if units == 0:
            return

        try:
            self._oanda.sell(units)
        except Exception as e:
            self._catchTradeException(e, "enter short")

    def ClosePosition(self, position):
        self._sl_indicator.CancelStop()
        if not self.trading_enabled:
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
        if self._email:
            txt = "\n\nError while trying to " + position + " position\n"
            txt += "It was caught, I should still be running\n\n"
            txt += traceback.format_exc() + "\n" + str(e)
            self._email.Send(txt)
