from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
import pandas as pd
import datetime
import backtrader.analyzers as btanalyzers


# 新建均线交叉的交易策略,快线是10周期，慢线是30周期
class SmaCross(bt.SignalStrategy):
    params = (('pfast', 10), ('pslow', 30),)

    def __init__(self):
        sma1, sma2 = bt.ind.SMA(period=self.p.pfast), bt.ind.SMA(period=self.p.pslow)
        self.signal_add(bt.SIGNAL_LONG, bt.ind.CrossOver(sma1, sma2))


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # Add a strategy
    # cerebro.addstrategy(TestStrategy)
    cerebro.addstrategy(SmaCross)

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
    cerebro.addsizer(bt.sizers.FixedSize, stake=1000)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.001)

    cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='transdemo')

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    thestrats = cerebro.run()
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # thestrat = thestrats[0]
    # print('Results: ', thestrat.analyzers.transdemo.get_analysis())

    # 显示测试运行后的图表
    cerebro.plot()
