import datetime
import matplotlib
matplotlib.use('qt5agg') 
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class StrategyPlot:

	def __init__(self, debugData, numberSubplots):
		self.debugData = debugData
		self.numberSubplots = numberSubplots
		self.xfrom = None
		self.xto = None
		plt.gcf().canvas.set_window_title('Backtest Results')

		# Get the right x scale
		time = []
		for item in debugData["RawPrice"]:
			time.append( datetime.datetime.fromtimestamp(item["now"]) )
		self.SetXLimits(time[0], time[-1])

	def SetXLimits(self, xfrom, xto):
		self.xfrom = xfrom
		self.xto = xto

	def Plot(self, plotName, subplot, format="r-"):
		if (plotName not in self.debugData):
			return
	
		time = []
		value = []
		for item in self.debugData[plotName]:
			time.append(datetime.datetime.fromtimestamp(item["now"]))
			value.append(item["value"])

		plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
		plt.subplot(self.numberSubplots,1,subplot)
		plt.plot(time, value, format)

		if self.xfrom != None and self.xto != None:
			plt.xlim([self.xfrom, self.xto])

	def Show(self):
		plt.show()
