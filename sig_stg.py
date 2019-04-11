import backtrader as bt
import backtrader.indicators as btind


class CrossOverStrategy(bt.Strategy):
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

        self.log(f"OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}")


def run_stg():
    pass