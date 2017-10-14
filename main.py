#!/usr/bin/env python3
import sys
import traceback
import logging
from settings import ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENT, \
    ACCOUNT_CURRENCY, HOME_BASE_CURRENCY_PAIR, HOME_BASE_CURRENCY_PAIR_DEFAULT_EXCHANGE_RATE, \
    ENVIRONMENT, CANDLES_MINUTES, MAX_PERCENTAGE_ACCOUNT_AT_RISK, STOP_LOSS
from util.ui import CursedUI
from exchange.oanda import Oanda
from exchange.oanda import OandaExceptionCode
from logic.strategy import Strategy


logging.basicConfig(filename='oandabot.log',
                    level=logging.INFO,
                    format="%(asctime)-15s %(message)s")

oanda = Oanda(ACCESS_TOKEN,
              ACCOUNT_ID,
              INSTRUMENT,
              ACCOUNT_CURRENCY,
              HOME_BASE_CURRENCY_PAIR,
              HOME_BASE_CURRENCY_PAIR_DEFAULT_EXCHANGE_RATE,
              ENVIRONMENT)

strategy = Strategy(oanda,
                    CANDLES_MINUTES,
                    risk=MAX_PERCENTAGE_ACCOUNT_AT_RISK,
                    stoploss=STOP_LOSS)

cursed_ui = CursedUI(oanda, strategy, INSTRUMENT, ACCOUNT_CURRENCY)


def handle_exceptions(error):
    cursed_ui.Stop()
    traceback.print_exc()
    logging.critical(traceback.format_exc())
    strategy.Stop()
    ret_code = OandaExceptionCode(error)
    sys.exit(ret_code)


def main():
    strategy.Start()
    cursed_ui.Start()

    while oanda.IsRunning():
        oanda.UpdateSubscribers()
        cursed_ui.ProcessUserInput()
        if cursed_ui.IsExiting():
            break

    cursed_ui.Stop()
    strategy.Stop()
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as err:
        handle_exceptions(err)
