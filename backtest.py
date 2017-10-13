#!/usr/bin/env python3
from backtest.oanda_backtest import OandaBacktest
from logic.strategy import Strategy
from settings import *
from util.plot import StrategyPlot
import ui
import sys
import os

def PlotResults(plotData):
    if not plotData:
        return
    splot = StrategyPlot(plotData, 1)
    splot.Plot("RawPrice",1, "b-")
    splot.Plot("Sell", 1, "ro")
    splot.Plot("Buy", 1, "g^")
    splot.Plot("Close", 1, "b*")
    splot.Plot("StopLoss", 1, "_")
    splot.Plot("TrailingStop", 1, "y--")
    splot.Plot("short", 1, "r--")
    splot.Plot("medium", 1, "g--")
    splot.Plot("long", 1, "b--")
    splot.Show()
    #splot.Plot("NetWorth", 1, "r-")
    #splot.Show()

def Main(argv):
    oanda_backtest = OandaBacktest(argv[0])

    strategy = Strategy(oanda_backtest,
                        CANDLES_MINUTES,
                        email=None,
                        risk=MAX_PERCENTAGE_ACCOUNT_AT_RISK,
                        stoploss=STOP_LOSS)

    info_icon = ui.UnicodeSequence(ui.green, "ℹ", "i")
    ui.info('', ui.green,info_icon,ui.reset,'Starting backtest on',argv[0])

    strategy.Start()

    while oanda_backtest.IsRunning():
        oanda_backtest.UpdateSubscribers()

    ui.info('', ui.green,info_icon,ui.reset,'Plotting results...')
    plotData = oanda_backtest.GetPlotData()
    PlotResults(plotData)

if __name__ == "__main__":
    try:
        Main(sys.argv[1:])
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
