from logic import Indicator
from logic.candle import Candle


class HeikinAshi(Indicator):

    def __init__(self):
        self.open = 0.0
        self.close = 0.0
        self.high = 0.0
        self.low = 0.0
        self._data = []

    def seen_enough_data(self):
        return (len(self._data) > 1)

    def DataPointsCount(self):
        return len(self._data)

    def AmountOfDataStillMissing(self):
        return max(2 - len(self._data), 0)

    def update(self, datapoint):
        if (not isinstance(datapoint, Candle)):
            return

        self._data.append(datapoint)

        if (self.DataPointsCount() < 2):
            self.close = datapoint.close
            self.open = datapoint.open
            self.high = datapoint.high
            self.low = datapoint.low
            return

        if (self.DataPointsCount() > 2):
            self._data.pop(0)

        # Here: exactly two datapoints in self._data
        prev_open = self._data[-2].open
        prev_close = self._data[-2].Close
        curr_open = self._data[-1].open
        curr_close = self._data[-1].Close
        curr_high = self._data[-1].high
        curr_low = self._data[-1].low

        self.open = (prev_open + prev_close) / 2.0
        self.close = (curr_open + curr_close + curr_high + curr_low) / 4.0
        self.high = max([curr_high, curr_open, curr_close])
        self.low = min([curr_low, curr_open, curr_close])
