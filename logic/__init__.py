__all__ = [
    "candle", "strategy", "heikinashi", "movingaverage", "risk", "trailingstop",
    "timestop", "takeprofit"
]


class Indicator(object):

    def update(self, datapoint):
        pass

    def seen_enough_data(self):
        return False

    def amount_of_data_still_missing(self):
        return 0


class MarketTrend(object):
    NONE = "none"
    BULL = "bull"
    BEAR = "bear"
    ENTER_LONG = "enter_long"
    ENTER_SHORT = "enter_short"
    EXIT_LONG = "exit_long"
    EXIT_SHORT = "exit_short"
    STOP_LONG = "stop_long"
    STOP_SHORT = "stop_short"
    NO_STOP = "no_stop"
    UP = BULL
    DOWN = BEAR


class TrendEstimator(object):

    def __init__(self, config):
        self.config = config
        self.trend = MarketTrend.NONE

    # The amount of data points needed to finish
    # seeding the trend estimator.
    # If the estimator does not need seeding, this should always be 0
    # If the estimator needs 10 datapoints to be seeded and has already
    # seen 5, then this function should return 5
    def amount_of_data_still_missing(self):
        return 0

    # Should return False while the instance needs to be seeded more
    # And return True when the estimator seen enough data and can function
    def seen_enough_data(self):
        return False

    # Return the current market trend state
    # If uncertain, return MarketTrend.NONE,
    # otherwise try to predict if we are in UP or DOWN trend
    def market_trend(self):
        if not self.seen_enough_data():
            return MarketTrend.NONE
        return self.trend

    # update the trend estimator with a new data point (candle, trade, ticker)
    def update(self, datapoint):
        pass


def validate_datapoint(datapoint):
    if not datapoint:
        return False
    if "now" not in datapoint:
        return False
    if "value" not in datapoint:
        return False
    return True
