import time

from logic import Indicator, validate_datapoint


class Candle(Indicator):

    openp = 0.0
    close = 0.0
    high = 0.0
    low = 0.0
    open_time = time.time()
    close_time = open_time

    def __init__(self, open_time, close_time):
        self.open_time = open_time
        self.close_time = close_time
        self._is_closed = False

    # Returns true if candle stick accumulated enough data to represent the
    # time span between Opening and Closing timestamps
    def seen_enough_data(self):
        return self._is_closed

    def amount_of_data_still_missing(self):
        if self.seen_enough_data():
            return 0

        return 1

    def update(self, data):
        if self.close_time < self.open_time:
            self._reset_price(0.0)
            self._is_closed = False
            return

        if not validate_datapoint(data):
            return

        _current_timestamp = data["now"]
        _price = data["value"]

        if _current_timestamp >= self.close_time:
            self._is_closed = True

        if (_current_timestamp <= self.close_time
                and _current_timestamp >= self.open_time):
            self._update_data(_price)

    def _reset_price(self, price):
        self.high = price
        self.low = price
        self.openp = price
        self.close = price

    # update the running timestamps of the data
    def _update_data(self, price):
        # If this is the first datapoint, initialize the values
        if self.high == 0.0 and self.low == 0.0 and self.openp == 0.0 \
           and self.close == 0.0:
            self._reset_price(price)
            self._is_closed = False
            return

        # update the values in case the current datapoint is a current High/low
        self.close = price
        self.high = max(price, self.high)
        self.low = min(price, self.low)

    def set_closed(self, state):
        self._is_closed = state

    def __str__(self):
        return "openp = "+str(self.openp)\
            +" close = "+str(self.close)\
            +" high = "+str(self.high)\
            +" low = "+str(self.low)\
            +" open_time = "+str(self.open_time)\
            +" close_time = "+str(self.close_time)