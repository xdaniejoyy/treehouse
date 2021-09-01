from dateutil.parser import parse
from pandas_datareader import data as pdr
from scipy.stats import *
import numpy as np
import pandas as pd
import yfinance as yf


class Portfolio(object):
    """Portfolio takes in a DataFrame of tickers and weights.
    Columns: ticker, weight.

    :param portfolio: DataFrame, portfolio composition.
    """

    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.prices = pd.DataFrame()
        self.market_rtn = pd.DataFrame()

        columns = ['ticker', 'weight']
        if any(x not in self.portfolio.columns for x in columns):
            raise ValueError(f"Required columns: {columns}")

        self.portfolio.set_index('ticker', inplace=True)
        assert self.portfolio['weight'].sum() == 1

    def get_prices(self,
                    start_date,
                    end_date):
        """
        Get portfolio prices between start/end date
        :param start_date: date
        :param end_date: date
        :return:
        """
        # Format and check params
        start_date = parse(start_date).date()
        end_date = parse(end_date).date()
        assert end_date > start_date

        # Get daily returns from Yahoo! Finance
        yf.pdr_override()
        for ticker in self.portfolio.index.tolist():

            print(f"Getting close prices for {ticker}.")
            cl = pdr.get_data_yahoo(ticker, start=start_date, end=end_date)

            if len(cl) == 0:
                print("No data found, check ticker again.")
            else:
                self.prices[ticker] = cl.Close

    def get_returns(self,
                    start_date,
                    end_date):
        """
        Get portfolio returns between start/end date
        :param start_date: date
        :param end_date: date
        :return:
        """
        self.get_prices(start_date, end_date)

        # Calculate returns
        self.market_rtn = self.prices.apply(
            lambda x: x / x.shift() - 1).fillna(0)

    def get_historical_var(self,
                           var_pct=95):
        """
        Get VaR, CVaR based on actual returns
        :param var_pct: float, % VaR, CVaR to calculate
        :return: list containing VaR, CVaR
        """

        assert 0 <= var_pct <= 100

        values = self.market_rtn.dot(self.portfolio['weight'])
        var = np.quantile(values, 1 - var_pct/100)
        cvar = values[values < var].mean()

        return [f"{round(var * 100, 2)}%", f"{round(cvar * 100, 2)}%"]

    def get_parametric_var(self,
                           var_pct=95):
        """
        Get VaR, CVaR based on distribution of actual returns
        :param var_pct: float, % VaR, CVaR to calculate
        :return: list containing VaR, CVaR
        """
        # Format and check params
        assert 0 <= var_pct <= 100

        values = self.market_rtn.dot(self.portfolio['weight'])
        portf_mean = np.mean(values)
        portf_std = np.sqrt(self.portfolio['weight'].dot(
            self.market_rtn.cov()).dot(self.portfolio['weight']))
        var = norm.ppf(1 - var_pct/100, portf_mean, portf_std)
        cvar = (1 / (var_pct/100)) * \
               norm.pdf(norm.ppf(1 - var_pct/100)) * portf_std - portf_mean
        return [f"{round(var * 100, 2)}%", f"{round(cvar * 100, 2)}%"]

    def rebal(self,
              delta=0.05,
              lookback_days=4):
        """
        Risk-adjusted momentum portfolio. We o/w stocks with positive momentum,
        and low volatility.

        Assumptions:
        1. Earliest returns available are 1 Jan 2016- no data is available prior
        to make rebal decisions.
        2. Portfolio starts off equal-weighting all 7 assets.
        3. Each rebal, we re-weight the assets based on how they perform
        (+/- delta)

        :param delta: float, how much to increase/decrease
        :param lookback_days, int, lookback for momentum
        :return: DataFrame, weights at the end of each month
        """
        start_date = '2016-01-01'
        end_date = '2016-12-31'

        assert lookback_days > 0

        if len(self.prices) == 0:
            self.get_prices(start_date, end_date)

        # Initialize result
        dates = self.market_rtn.reset_index().groupby(
            pd.Grouper(key='Date', freq='M')).max().index
        result = pd.DataFrame(index=dates, columns=self.market_rtn.columns)
        signals = pd.DataFrame(index=dates, columns=self.market_rtn.columns)
        result.iloc[0, :] = 1.0 / result.shape[1]

        for d1, d2 in zip(dates[:-1], dates[1:]):
            subset = self.prices.loc[d1:d2].copy(deep=True).pct_change()
            signal = (subset.tail(lookback_days).sum()) / self.prices.loc[:d2].std()
            signal_rank = signal.rank()
            signals.loc[d2, :] = signal

            # Get weights
            wgt_chg = signal_rank.apply(lambda x: -delta if x <= 2 else (delta if x >= 6 else 0))
            new_wgt = result.loc[d1] + wgt_chg

            result.loc[d2, :] = new_wgt / sum(new_wgt)

        return result, signals


df = pd.DataFrame([['AAPL', 0.15],
                   ['IBM', 0.2],
                   ['GOOG', 0.2],
                   ['BP', 0.15],
                   ['XOM', 0.10],
                   ['COST', 0.15],
                   ['GS', 0.05]],
                  columns=['ticker', 'weight'])

start_date = '2016-01-01'
end_date = '2016-12-31'
var_pct = 95

q4 = Portfolio(df)
q4.get_returns(start_date, end_date)
print("1D Historical VaR/CVaR:", q4.get_historical_var(var_pct))
print("1D Parametric VaR/CVaR:", q4.get_parametric_var(var_pct))


# Risk-Adjusted Momentum Backtest with:
# lookback_days = 3, 5, 10
# delta = 0.05, 0.1, 0.2
# Most optimal is a medium signal (5D lookback, 0.2 delta).

strategy_returns = pd.DataFrame()
for lookback_days in [3, 5, 10]:
    for delta in [0.05, 0.1, 0.2]:
        identifier = f"delta={delta},{lookback_days}D"

        rebal_weights, smas = q4.rebal(delta=delta,
                                       lookback_days=lookback_days)

        # Get monthly returns plot

        wgts = pd.DataFrame(index=q4.market_rtn.index).merge(
            rebal_weights, how='outer', left_index=True, right_index=True).ffill()
        strategy_returns[identifier] = (q4.market_rtn * wgts).sum(axis=1)

# Sharpe Ratios
print("Sharpe Ratios (for Y=2016)")
print(strategy_returns.sum() / (strategy_returns.std() * np.sqrt(260)))

## Plot of permutations
strategy_returns.apply(lambda x: np.cumprod(1 + x)).plot()