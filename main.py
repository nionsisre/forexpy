#!/usr/bin/env python3
import sys
import traceback
import logging
from settings import ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENT, \
    ACCOUNT_CURRENCY, HOME_BASE_CURRENCY_PAIR, \
    HOME_BASE_CURRENCY_PAIR_DEFAULT_EXCHANGE_RATE, \
    ENVIRONMENT, CANDLES_MINUTES, MAX_PERCENTAGE_ACCOUNT_AT_RISK, STOP_LOSS
from util.ui import CursedUI
from exchange.oanda import Oanda
from exchange.oanda import OandaExceptionCode
from logic.strategy import Strategy

logging.basicConfig(
    filename='OANDAbot.log',
    level=logging.INFO,
    format="%(asctime)-15s %(message)s")

OANDA = Oanda(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENT, ACCOUNT_CURRENCY,
              HOME_BASE_CURRENCY_PAIR,
              HOME_BASE_CURRENCY_PAIR_DEFAULT_EXCHANGE_RATE, ENVIRONMENT)

STRATEGY = Strategy(
    OANDA,
    CANDLES_MINUTES,
    risk=MAX_PERCENTAGE_ACCOUNT_AT_RISK,
    stoploss=STOP_LOSS)

CURSED_UI = CursedUI(OANDA, STRATEGY, INSTRUMENT, ACCOUNT_CURRENCY)


def handle_exceptions(error):
    CURSED_UI.stop()
    traceback.print_exc()
    logging.critical(traceback.format_exc())
    STRATEGY.stop()
    ret_code = OandaExceptionCode(error)
    sys.exit(ret_code)


def main():
    STRATEGY.start()
    CURSED_UI.start()

    while OANDA.is_running():
        OANDA.update_subscribers()
        CURSED_UI.process_user_input()
        if CURSED_UI.is_exiting():
            break

    CURSED_UI.stop()
    STRATEGY.stop()
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as err:
        handle_exceptions(err)
