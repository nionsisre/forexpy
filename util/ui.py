import curses
from logic import validate_datapoint


class CursedUI(object):

    def __init__(self, oanda, strategy, instrument, account_currency):
        self._oanda = oanda
        self._strategy = strategy
        self._account_currency = account_currency
        self._instrument = instrument
        self.stdscr = None
        self._net_worth = ""
        self._unrealized_pnl = ""
        self._balance = ""
        self._cash_invested = ""
        self._current_position = ""
        self._current_position_side = ""
        self._available_units = ""
        self._leverage = ""
        self._current_price = ""
        self._heartbeat_time = ""
        self._stoploss_price = ""
        self._trailingstop_price = ""
        self._is_exiting = False

    def start(self):
        self._oanda.SubscribeHeartbeat(self)
        self._oanda.subscribe_ticker(self)
        self._oanda.Subscribeupdates(self)

        self.stdscr = curses.initscr()
        curses.noecho()
        self.stdscr.keypad(1)
        self.stdscr.nodelay(1)

        self.update(None)
        self.render()

    def stop(self):
        if not self.stdscr:
            return

        # deinit curses
        self.stdscr.nodelay(0)
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

    def update(self, datapoint):

        if not datapoint:
            # Pull balances and positions
            self._net_worth = str(self._oanda.GetNetWorth())
            self._balance = str(self._oanda.GetBalance())
            self._i = str(self._oanda.CashInvested())
            self._current_position = str(self._oanda.current_position())
            self._s = str(self._oanda.current_position_side())
            self._u = str(self._oanda.available_units())
            self._leverage = str(self._oanda.Leverage())
            self._unrealized_pnl = str(self._oanda.UnrealizedPNL())

        if validate_datapoint(datapoint):
            self._current_price = str(datapoint["value"])

        if self._is_heartbeat_update(datapoint):
            self._t = str(datapoint["time"])

        self._stoploss_price = str(self._strategy.GetstopLossPrice())
        self._trailingstop_price = str(self._strategy.GetTrailingstopPrice())
        self._unrealized_pnl = str(self._oanda.UnrealizedPNL())

        self.render()

    def process_user_input(self):
        char = self.stdscr.getch()

        # b - buy current instrument
        if char == ord('b'):
            self.stdscr.addstr(18, 22, "(now: buying)", curses.A_STANDOUT)
            self.stdscr.refresh()
            tstatus = self._strategy.TradingStatus()
            self._strategy.ResumeTrading()
            self._strategy.Buy()
            self._strategy.SetTradingStatus(tstatus)

        # s - sell current instrument
        if char == ord('s'):
            self.stdscr.addstr(18, 22, "(now: selling)", curses.A_STANDOUT)
            self.stdscr.refresh()
            tstatus = self._strategy.TradingStatus()
            self._strategy.ResumeTrading()
            self._strategy.Sell()
            self._strategy.SetTradingStatus(tstatus)

        # c - close open position
        if char == ord('c'):
            self.stdscr.addstr(18, 22, "(now: closing positions)",
                               curses.A_STANDOUT)
            self.stdscr.refresh()
            tstatus = self._strategy.TradingStatus()
            self._strategy.ResumeTrading()
            self._strategy.ClosePosition('both')
            self._strategy.SetTradingStatus(tstatus)

        # p - pause strategy
        if char == ord('p'):
            self.stdscr.addstr(18, 22, "(now: pausing strategy)",
                               curses.A_STANDOUT)
            self.stdscr.refresh()
            self._strategy.PauseTrading()

        # r - resume strategy
        if char == ord('r'):
            self.stdscr.addstr(18, 22, "(now: resuming strategy)",
                               curses.A_STANDOUT)
            self.stdscr.refresh()
            self._strategy.ResumeTrading()

        # q - quit
        if char == ord('q'):
            self.stdscr.addstr(18, 22, "(now: quitting)", curses.A_STANDOUT)
            self.stdscr.refresh()
            self._is_exiting = True

    def is_exiting(self):
        return self._is_exiting

    def _is_heartbeat_update(self, datapoint):
        if not datapoint:
            return False
        if "time" not in datapoint:
            return False
        return True

    def render(self):
        self.stdscr.erase()
        self.stdscr.addstr(0, 0, "OANDA bot", curses.A_UNDERLINE)

        # Current account status
        self.stdscr.addstr(2, 0,
                           "Account currency:   " + self._account_currency)
        self.stdscr.addstr(3, 0, "Trading instrument: " + self._instrument)

        # Ticker and heartbeat
        self.stdscr.addstr(5, 0, "Heartbeat: " + self._t)
        self.stdscr.addstr(6, 0, "Ticker:    " + str(self._current_price))

        # Account status
        self.stdscr.addstr(
            8, 0, "Position:        " + self._current_position + " " + self._s)
        self.stdscr.addstr(9, 0, "Balance:         " + self._balance)
        self.stdscr.addstr(10, 0, "Available units: " + self._u)
        self.stdscr.addstr(
            11, 0,
            "Cash invested:   " + self._i + " leverage: " + self._leverage)
        self.stdscr.addstr(12, 0, "Net Worth:       " + self._net_worth +
                           " unrealized PnL: " + self._unrealized_pnl)

        # Strategy status
        self.stdscr.addstr(14, 0,
                           "stop Loss price:     " + str(self._stoploss_price))
        self.stdscr.addstr(
            15, 0, "Trailing stop price: " + str(self._trailingstop_price))
        if self._strategy.TradingStatus():
            status = "running"
        else:
            status = "paused"
        self.stdscr.addstr(16, 0, "Strategy status:     " + status)

        self.stdscr.addstr(18, 0, "Available actions:", curses.A_UNDERLINE)
        if self._strategy.TradingStatus():
            command = "(P)ause - pause strategy. Disable trading, but keep tickers coming"
        else:
            command = "(R)esume - resume strategy. Reenable trading"

        self.stdscr.addstr(19, 0, command)
        self.stdscr.addstr(20, 0, "(B)uy - take long position on instrument")
        self.stdscr.addstr(21, 0, "(S)ell - take short position on instrument")
        self.stdscr.addstr(22, 0, "(C)lose - close position on instrument")
        self.stdscr.addstr(23, 0, "(Q)uit - exit")

        self.stdscr.refresh()
