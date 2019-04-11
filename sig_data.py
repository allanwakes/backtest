from sig_config import EXCHANGES, USING_PROXY, PROXY_SETTING, BINANCE_APIKEY, BINANCE_APISECRET, CCXT_FREQ
import ccxt
import pandas as pd
import datetime
import backtrader as bt


def get_or_create_worker(exchange_name):
    worker = EXCHANGES.get(exchange_name)
    if worker is None:
        if exchange_name == 'huobi':
            worker = ccxt.huobipro({
                'proxies': PROXY_SETTING if USING_PROXY else None,
                'timeout': 30000,
            })
        elif exchange_name == 'binance':
            worker = ccxt.binance({
                'proxies': PROXY_SETTING if USING_PROXY else None,
                'apiKey': BINANCE_APIKEY,
                'secret': BINANCE_APISECRET,
                'timeout': 30000,
                'enableRateLimit': True,
            })
        elif exchange_name == 'bitfinex':
            worker = ccxt.bitfinex({
                'proxies': PROXY_SETTING if USING_PROXY else None,
                'timeout': 30000,
            })
        else:
            print(f"{exchange_name} not supported")
            raise Exception(f"{exchange_name} worker unsupported")

        worker.load_markets()

        EXCHANGES[exchange_name] = worker

    return worker


def get_crypt_datafeed(exchange='bitfinex', limit=300, freq='5m', symbol='BTC/USD'):
    if exchange not in EXCHANGES.keys():
        raise Exception(f"{exchange} parameter error")
    if freq not in CCXT_FREQ.keys():
        raise Exception(f"{freq} parameter error")

    data_worker = get_or_create_worker(exchange)
    symbol_real = data_worker.find_symbol(symbol)
    if symbol_real not in data_worker.symbols:
        raise Exception(f"{symbol_real} checking error")

    end_time = data_worker.milliseconds()
    since_time = end_time - limit * CCXT_FREQ[freq]
    data = data_worker.fetch_ohlcv(symbol=symbol_real, timeframe=freq, limit=limit, since=since_time)
    if data is None:
        raise Exception(f"{symbol_real} {freq} getting none data")

    df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'], unit='ms')  # CCXT返回的是ts，需要转换成毫秒
    df['openinterest'] = 0
    df.set_index('date', inplace=True)
    df.dropna(how='all')  # 数据整形
    fromdate = datetime.datetime.fromtimestamp(since_time / 1000)
    todate = datetime.datetime.fromtimestamp(end_time / 1000)
    return bt.feeds.PandasData(dataname=df, fromdate=fromdate, todate=todate)