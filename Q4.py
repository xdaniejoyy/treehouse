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
        self.market_rtn = pd.DataFrame()

        columns = ['ticker', 'weight']
        if any(x not in self.portfolio.columns for x in columns):
            raise ValueError(f"Required columns: {columns}")

        self.portfolio.set_index('ticker', inplace=True)
        assert self.portfolio['weight'].sum() == 1

    def get_returns(self,
                    start_date,
                    end_date):
        """
        Get VaR, CVaR based on portfolio returns between start/end date
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
                self.market_rtn[ticker] = cl.Close

        # Calculate returns
        self.market_rtn = self.market_rtn.apply(
            lambda x: x / x.shift() - 1).fillna(0)

    def get_historical_var(self,
                           var_pct=95):
        """
        Get VaR, CVaR based on portfolio returns between start/end date
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
        Get VaR, CVaR based on distribution of portfolio returns between start/end date
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
print("1D Parametric VaR/CVaR:", q4.get_parametric_var(var_pct))

