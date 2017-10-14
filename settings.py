# Account settings
ACCOUNT_ID = "101-004-6915582-001"
ACCESS_TOKEN = "9d533eda015cd715c939ea0dd168df50-f84a47446e936bc2009ecf0d0f0a2f5d"
ENVIRONMENT = "practice"  # change this to "live" for production

# Pair to trade.
# only one allowed for now - run multiple instances if you want multiple pairs
ACCOUNT_CURRENCY = "USD"
INSTRUMENT = "EUR_USD"

# Home / Base exchange rate
# Examples: instrument: "USD_JPY", home: "USD", home/base: "USD_USD"
#           instrument: "EUR_USD", home: "USD", home/base: "EUR_USD"
#           instrument: "AUD_CAD", home: "USD", home/base: "USD_AUD"
HOME_BASE_CURRENCY_PAIR = "EUR_USD"
HOME_BASE_CURRENCY_PAIR_DEFAULT_EXCHANGE_RATE = 0.88

# Size of candles in minutes
CANDLES_MINUTES = 1

# Risk settings
MAX_PERCENTAGE_ACCOUNT_AT_RISK = 2  # percent
STOP_LOSS = 100  # atr stop loss

# Email credentials
EMAIL_RECIPIENT = "youremail@gmail.com"
EMAIL_FROM = "oandabot@yourserver.com"
EMAIL_SERVER = "mail.yourserver.com"
EMAIL_PORT = 25
EMAIL_PASSWORD = "SuchSecurePasswordStoredUnecrypted"

# Special bot name for identification
# In case you have many and want to distinguish between them
# Leave default if only running one bot
BOT_NAME = "OANDAPYBOT"

# For backtesting
BACKTESTING_FILENAME = "DAT_MT_EURUSD_M1_2016.csv"
