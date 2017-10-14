import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('qt5agg')



class Strategyplot:

    def __init__(self, debug_data, subplots):
        self.debug_data = debug_data
        self.subplots = subplots
        self.xfrom = None
        self.xto = None
        plt.gcf().canvas.set_window_title('Backtest Results')

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

        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        plt.subplot(self.subplots, 1, subplot)
        plt.plot(time, value, style)

        if self.xfrom != None and self.xto != None:
            plt.xlim([self.xfrom, self.xto])

    def show(self):
        plt.show()
