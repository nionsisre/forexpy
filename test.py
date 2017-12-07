#!/usr/bin/env python3
"""Usage:
  test.py FILE
  test.py -h --help
"""
import sys
import os.path
from docopt import docopt
from backtest.oanda_backtest import OandaBacktest
from logic.strategy import Strategy
from settings import CANDLES_MINUTES, MAX_PERCENTAGE_ACCOUNT_AT_RISK, STOP_LOSS,\
     TRAILING_PERIOD, TAKE_PROFIT
from util.plot import Strategyplot


def plot_results(plot_data):
    if not plot_data:
        return
    splot = Strategyplot(plot_data, 2)
    splot.plot("RawPrice", 0, "m-")
    #splot.plot("Sell", 0, "ro")
    #splot.plot("Buy", 0, "g^")
    #splot.plot("Close", 0, "b*")
    #splot.plot("StopLoss", 0, "_")
    #splot.plot("TrailingStop", 0, "g-")
    #splot.plot("TakeProfit", 0, "g-")
    splot.plot("short", 0, "r--")
    splot.plot("medium", 0, "g--")
    splot.plot("long", 0, "b--")
    #splot.plot("NetWorth", 1, "r-")
    splot.show()


def main(argv):
    arguments = docopt(__doc__, argv, help=True, version=None, options_first=False)

    if os.path.isfile(arguments['FILE']) is not True:
        print('File not found')
        return

    oanda_backtest = OandaBacktest(arguments['FILE'])

    strategy = Strategy(oanda_backtest,
                        CANDLES_MINUTES,
                        email=None,
                        risk=MAX_PERCENTAGE_ACCOUNT_AT_RISK,
                        stoploss=STOP_LOSS,
                        trailing_period=TRAILING_PERIOD,
                        take_profit=TAKE_PROFIT)

    print('Starting backtest on', argv[0])

    strategy.Start()

    while oanda_backtest.is_running():
        oanda_backtest.update_subscribers()

    print('plotting results...')
    plot_data = oanda_backtest.get_plot_data()
    plot_results(plot_data)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        sys.exit(0)
