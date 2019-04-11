from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import os
import pandas as pd
import datetime
import backtrader.indicators as btind
import backtrader.analyzers as btanalyzers
import ccxt

basedir = os.path.abspath(os.path.dirname(__file__))


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('printlog', False),
        ('fast', 20),
        ('slow', 45)
    )

    def log(self, txt, dt=None, doprint=False):
        # Logging function for this strategy
        if self.params.printlog or doprint:
            # 很有意思的地方，self.datas[0].datetime到底是什么
            # date(0) == date(), datetime() == datetime(0)
            # self.datas[0].datetime is a linebuffer
            # linebuffer has date, time, datetime method, leveraging num2date
            dt = dt or self.datas[0].datetime.datetime()
            print(f"{dt.strftime('%Y-%m-%d %H:%M:%S')}, {txt}")
            # print(f"{dt}, {txt}")

    def __init__(self):
        sma = btind.SimpleMovingAverage
        cross = btind.CrossOver
        self.fastma = sma(self.datas[0].close, period=self.params.fast, plotname='FastMA')
        self.slowma = sma(self.datas[0].close, period=self.params.slow, plotname='SlowMA')
        self.crossover = cross(self.fastma, self.slowma)
        # self.crossover = self.fastma - self.slowma

    def next(self):
        # 除了buy和sell，还有close，从定义上看是和buy，sell相反的操作：如果有持仓，那么就是sell，如果没有持仓，就是买
        if self.position.size:
            if self.crossover < 0:
                self.sell()
        elif self.crossover > 0:
            self.buy()

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f"OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}", doprint=True)


class TheStrategy(bt.SignalStrategy):  # 测试signal
    params = dict(rsi_per=14, rsi_upper=65.0, rsi_lower=35.0, rsi_out=50.0,
                  warmup=35)

    def notify_order(self, order):
        super(TheStrategy, self).notify_order(order)
        if order.status == order.Completed:
            print('%s: Size: %d @ Price %f' %
                  ('buy' if order.isbuy() else 'sell',
                   order.executed.size, order.executed.price))

            d = order.data
            print('Close[-1]: %f - Open[0]: %f' % (d.close[-1], d.open[0]))

    def __init__(self):
        # Original code needs artificial warmup phase - hidden sma to replic
        if self.p.warmup:
            bt.indicators.SMA(period=self.p.warmup, plot=False)

        rsi = bt.indicators.RSI(period=self.p.rsi_per,
                                upperband=self.p.rsi_upper,
                                lowerband=self.p.rsi_lower)

        crossup = bt.ind.CrossUp(rsi, self.p.rsi_lower)
        self.signal_add(bt.SIGNAL_LONG, crossup)
        self.signal_add(bt.SIGNAL_LONGEXIT, -(rsi > self.p.rsi_out))

        crossdown = bt.ind.CrossDown(rsi, self.p.rsi_upper)
        self.signal_add(bt.SIGNAL_SHORT, -crossdown)
        self.signal_add(bt.SIGNAL_SHORTEXIT, rsi < self.p.rsi_out)


def get_ohlc_data(local_data=True):
    if local_data:
        local_data_name = 'btc_usd_1h.csv'
        local_data_file = os.path.join(basedir, local_data_name)
        # dataframe = pd.read_csv(local_data_file, index_col='dt', parse_dates=True)
        dataframe = pd.read_csv(
            local_data_file, skiprows=0, header=0, parse_dates=True, index_col=0
        )
        dataframe['openinterest'] = 0
        # print(dataframe.head(10))
        # 会包括9.25，只是因为9.25的0点是24日的24点
        return bt.feeds.PandasData(
            dataname=dataframe, fromdate=datetime.datetime(2017, 10, 1), todate=datetime.datetime(2017, 11, 24)
        )
    else:
        exchange = 'bitfinex'
        limit = 300
        freq = '1h'
        freq_mapper = {'1h': 60 * 60 * 1000}
        proxy_setting = {
            'http': 'socks5://127.0.0.1:1080',
            'https': 'socks5h://127.0.0.1:1080'
        }
        worker = ccxt.bitfinex({
            'proxies': proxy_setting,
            'timeout': 30000,
        })
        worker.load_markets()
        symbol = 'BTC/USD'
        symbol_real = worker.find_symbol(symbol)
        # print(symbol_real)
        end_time = worker.milliseconds()
        since_time = end_time - limit * freq_mapper[freq]
        data = worker.fetch_ohlcv(symbol=symbol_real, timeframe=freq, limit=limit, since=since_time)

        df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        df['date'] = pd.to_datetime(df['date'], unit='ms')  # CCXT返回的是ts，需要转换成毫秒
        df['openinterest'] = 0
        df.set_index('date', inplace=True)
        df.dropna(how='all')  # 数据整形
        fromdate = datetime.datetime.fromtimestamp(since_time / 1000)
        todate = datetime.datetime.fromtimestamp(end_time / 1000)
        return bt.feeds.PandasData(dataname=df, fromdate=fromdate, todate=todate)


def run_me(start_cash, commission, fast, slow):
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy, fast=fast, slow=slow)
    # cerebro.addstrategy(TheStrategy)

    # Add the Data Feed to Cerebro
    data_feed = get_ohlc_data(local_data=False)
    cerebro.adddata(data_feed)

    cerebro.broker.setcash(start_cash)
    cerebro.broker.setcommission(commission=commission)
    # Add a FixedSize sizer according to the stake
    # cerebro.addsizer(bt.sizers.FixedSize, stake=2)  # 固定的仓位
    cerebro.addsizer(bt.sizers.PercentSizer, percents=85)  # 百分比仓位，占可用cash的百分比

    cerebro.addanalyzer(btanalyzers.Transactions, _name='mytrans')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='dw')

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    runstrats = cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # cerebro.plot(volume=False)  # 避免由于缺少volume而导致的异常（本地数据没有vol）
    cerebro.plot(style='candlestick')

    # 测试分析器
    runstrats = runstrats[0]
    trans_analysis = runstrats.analyzers.mytrans.get_analysis()
    dw_analysis = runstrats.analyzers.dw.get_analysis()
    # print(type(dw_analysis).__name__)
    for k, v in dw_analysis.items():
        if type(v).__name__ != "AutoOrderedDict":
            print(f"{k}: {v}")
        else:
            print(f"{k}:   ")
            for k1, v1 in v.items():
                print(f"   {k1}: {v1}")

    # print(trans_analysis)
    for k, v in trans_analysis.items():  # k is datetime, v is [['amount', 'price', 'sid', 'symbol', 'value']]
        print(f"{k.isoformat()}, amount {v[0][0]}, price {v[0][1]}, cost {v[0][4]}")


if __name__ == '__main__':
    run_me(10000, 0.02, 40, 60)

