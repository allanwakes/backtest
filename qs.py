from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
import pandas as pd
import datetime


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
        ('printlog', False),
    )

    def log(self, txt, dt=None, doprint=False):
        # Logging function for this strategy
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod)

        # Indicators for the plotting show
        # 这些指标会影响策略执行的bar的起始，因为有些数据不是马上就可以就位的
        # bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        # bt.indicators.WeightedMovingAverage(self.datas[0], period=25, subplot=True)
        # bt.indicators.StochasticSlow(self.datas[0])
        # bt.indicators.MACDHisto(self.datas[0])
        # rsi = bt.indicators.RSI(self.datas[0])
        # bt.indicators.SmoothedMovingAverage(rsi, period=10)
        # bt.indicators.ATR(self.datas[0], plot=False)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Size: %d, Price: %.5f, Cost: %.5f, Comm %.5f' %
                    (
                        order.executed.size,
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm
                    ))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Size: %d, Price: %.5f, Cost: %.5f, Comm %.5f' %
                         (
                             order.executed.size,
                             order.executed.price,
                             order.executed.value,
                             order.executed.comm
                         ))

            self.bar_executed = len(self)  # 记录这个order成交时候的位置（第几个bar），后面的next可以使用这个坐标来评测距离

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] > self.sma[0]:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()
        else:
            # Already in the market ... we might sell
            if self.dataclose[0] < self.sma[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

    # 在每轮回测之后被调用（相当于main中的print Final Portfolio Value），如果是一个range，那么就是多次print
    def stop(self):
        self.log('(MA Period %2d) Ending Value %.2f' %
                 (self.params.maperiod, self.broker.getvalue()), doprint=True)


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # Add a strategy
    # cerebro.addstrategy(TestStrategy)
    strats = cerebro.optstrategy(
        TestStrategy,
        maperiod=range(10, 31))

    # create datafeed
    dataframe = pd.read_csv(
        'dfqc.csv',
        skiprows=0,
        header=0,
        parse_dates=True,
        index_col=0
    )
    dataframe['openinterest'] = 0
    # print(dataframe)
    data = bt.feeds.PandasData(
        dataname=dataframe, fromdate=datetime.datetime(2014, 1, 15), todate=datetime.datetime(2016, 12, 25)
    )

    # add the datafeed to cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(1000.0)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.0)

    # print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    # print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # 可以换成在stop中打印

    # Plot the result
    # cerebro.plot()
