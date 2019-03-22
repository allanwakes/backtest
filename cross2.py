from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
import pandas as pd
import datetime
import backtrader.indicators as btind
import backtrader.analyzers as btanalyzers


class CrossOver(bt.Strategy):

    alias = ('SMA_CrossOver',)

    params = (
        ('fast', 10),
        ('slow', 25),
        ('order_pct', 0.95),
        ('market', 'A:DongFeng')
    )

    def __init__(self):
        sma = btind.SimpleMovingAverage
        cross = btind.CrossOver
        self.fastma = sma(self.data.close, period=self.p.fast, plotname='FastMA')
        self.slowma = sma(self.data.close, period=self.p.slow, plotname='SlowMA')
        self.crossover = cross(self.fastma, self.slowma)

    def start(self):
        self.size = None

    def log(self, txt, dt=None):
        # Logging function for this strategy
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s, %d' % (dt.isoformat(), txt, self.p.slow))

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %(trade.pnl, trade.pnlcomm))

    def next(self):
        if self.position.size:
            # we have an open position or made it to the end of backtest
            last_candle = (self.data.close.buflen() == len(self.data.close) + 1)
            if (self.crossover < 0) or last_candle:
                msg = "*** MKT: {} SELL: {:.2f}"
                self.log(msg.format(self.p.market, self.size))
                self.close()

        elif self.crossover > 0:
            amount_to_invest = (self.p.order_pct * self.broker.cash)
            self.size = amount_to_invest / self.data.close
            msg = "*** MKT: {} BUY: {:.2f}"
            self.log(msg.format(self.p.market, self.size))
            self.buy(size=self.size)


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    km = {'fast': 5, 'slow': 10, 'order_pct': 0.9}

    cerebro.addstrategy(CrossOver, **km)

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
        dataname=dataframe, fromdate=datetime.datetime(2015, 1, 15), todate=datetime.datetime(2016, 12, 25)
    )

    # add the datafeed to cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(10000.0)

    # Add a FixedSize sizer according to the stake
    # 这里是Fixed Size，上面策略里面是按照百分比进行仓位管理
    # cerebro.addsizer(bt.sizers.FixedSize, stake=1000)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.001)

    cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='tademo')
    cerebro.addanalyzer(btanalyzers.Transactions, _name='transdemo')

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    thestrats = cerebro.run()
    print('Ending Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # inspired by http://actuarialdatascience.com/backtrader_performance_report.html
    # https://github.com/Oxylo/btreport/blob/master/report.py
    thestrat = thestrats[0]
    trade_analysis = thestrat.analyzers.tademo.get_analysis()
    trans_analysis = thestrat.analyzers.transdemo.get_analysis()
    for k, v in trans_analysis.items():
        print(k, v[0])
    trade_msg = "number of trades: {}\n%winning: {:.2f}%\n%losing: {:.2f}%\ntotal return: {:.2f}%"
    print(trade_msg.format(
        trade_analysis.total.total,
        100 * trade_analysis.won.total / trade_analysis.total.closed,
        100 * trade_analysis.lost.total / trade_analysis.total.closed,
        100 * trade_analysis.pnl.net.total / cerebro.broker.startingcash
    ))

    cerebro.plot(style='candlestick')
