from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import os
import pandas as pd
import datetime

basedir = os.path.abspath(os.path.dirname(__file__))


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('printlog', False),
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
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log(f"Close, {self.dataclose[0]:.2f}", doprint=True)


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
            dataname=dataframe, fromdate=datetime.datetime(2017, 9, 1), todate=datetime.datetime(2017, 9, 24)
        )
    else:
        return None


def run_me(start_cash, commission):
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # Add the Data Feed to Cerebro
    data_feed = get_ohlc_data()
    cerebro.adddata(data_feed)

    cerebro.broker.setcash(start_cash)
    cerebro.broker.setcommission(commission=commission)

    # print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    # print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())


if __name__ == '__main__':
    run_me(10000, 0.02)
