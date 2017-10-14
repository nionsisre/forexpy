#!/usr/bin/env python3
import sys
import ui
from backtest.oanda_backtest import OandaBacktest
from logic.strategy import Strategy
from settings import CANDLES_MINUTES, MAX_PERCENTAGE_ACCOUNT_AT_RISK, STOP_LOSS
from util.plot import Strategyplot


def plot_results(plot_data):
    if not plot_data:
        return
    splot = StrategyPlot(plot_data, 1)
    #splot.Plot("RawPrice", 1, "b-")
    #splot.Plot("Sell", 1, "ro")
    #splot.Plot("Buy", 1, "g^")
    #splot.Plot("Close", 1, "b*")
    #splot.Plot("StopLoss", 1, "_")
    #splot.Plot("TrailingStop", 1, "y--")
    #splot.Plot("short", 1, "r--")
    #splot.Plot("medium", 1, "g--")
    #splot.Plot("long", 1, "b--")
    #splot.Show()
    splot.Plot("NetWorth", 1, "r-")
    splot.Show()


def main(argv):
    oanda_backtest = OandaBacktest(argv[0])

    strategy = Strategy(oanda_backtest,
                        CANDLES_MINUTES,
                        email=None,
                        risk=MAX_PERCENTAGE_ACCOUNT_AT_RISK,
                        stoploss=STOP_LOSS)

    info_icon = ui.UnicodeSequence(ui.green, "ℹ", "i")
    ui.info('', ui.green, info_icon, ui.reset, 'Starting backtest on', argv[0])

    strategy.Start()

    while oanda_backtest.IsRunning():
        oanda_backtest.UpdateSubscribers()

    ui.info('', ui.green, info_icon, ui.reset, 'Plotting results...')
    plot_data = oanda_backtest.GetPlotData()
    plot_results(plot_data)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        sys.exit(0)
