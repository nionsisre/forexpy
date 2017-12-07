import datetime
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt


class Strategyplot:

    def __init__(self, debug_data, subplots_no):
        self.debug_data = debug_data
        self.figure, self.subplots = plt.subplots(subplots_no, 1, sharex=True)
        self.xfrom = None
        self.xto = None
        if subplots_no > 1:
            self.subplots[0].set_xlabel('')
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        plt.gcf().canvas.set_window_title('Backtest Results')
        plt.style.use('Solarize_Light2')

        # Get the right x scale
        time = []
        for item in debug_data["RawPrice"]:
            time.append(datetime.datetime.fromtimestamp(item["now"]))
        self.setxlimits(time[0], time[-1])

    def setxlimits(self, xfrom, xto):
        self.xfrom = xfrom
        self.xto = xto

    def plot(self, plotname, subplot, style="r-"):
        if plotname not in self.debug_data:
            return

        time = []
        value = []
        for item in self.debug_data[plotname]:
            time.append(datetime.datetime.fromtimestamp(item["now"]))
            value.append(item["value"])

        self.subplots[subplot].plot(time, value, style, lw=1.0)

        if self.xfrom != None and self.xto != None:
            self.subplots[subplot].set_xlim([self.xfrom, self.xto])

    def show(self):
        figManager = plt.get_current_fig_manager()
        figManager.window.showMaximized()
        plt.show()
