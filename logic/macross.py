from logic import MarketTrend, Indicator, validate_datapoint, movingaverage
from logic.candle import Candle

class MACross(Indicator):

    def __init__(self, sho, med, lon):
        super(MACross, self).__init__()
        self.state = MarketTrend.NONE
        self._short_ema = movingaverage.ExponentialMovingAverage(sho)
        self._medium_ema = movingaverage.ExponentialMovingAverage(med)
        self._long_sma = movingaverage.SimpleMovingAverage(lon)
        self._previous_cross = [False, False]
        self._current_cross = [False, False]

    def GetState(self):
        return self.state

    def seen_enough_data(self):
        return self._long_sma.seen_enough_data()

    def amount_of_data_still_missing(self):
        return self._long_sma.AmountOfDataStillMissing()

    def update(self, datapoint):
        self._short_ema.update(datapoint)
        self._medium_ema.update(datapoint)
        self._long_sma.update(datapoint)

        self._previous_cross = self._current_cross
        self._current_cross = self.check_crosses()

        if self._previous_cross[0] == False and self._current_cross[0] == True:
            self.state = MarketTrend.ENTER_LONG
        elif self._previous_cross[1] == False and self._current_cross[1] == True:
            self.state = MarketTrend.ENTER_SHORT
        else:
            self.state = MarketTrend.NONE

    def check_crosses(self):
        buycross = self._short_ema.value > self._medium_ema.value and self._short_ema.value > self._long_sma.value
        sellcross = self._short_ema.value < self._medium_ema.value and self._short_ema.value < self._long_sma.value
        return [buycross, sellcross]

