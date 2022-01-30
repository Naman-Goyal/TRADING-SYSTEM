from argparse import ArgumentParser
import argparse
from pandas_datareader import data as pdr
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import pandas as pd
import numpy as np
import datetime
import pandas as pd
import numpy as np
import collections
from collections import OrderedDict
from numpy import NaN, NAN,nan
import statistics
from pylab import rcParams
import warnings
warnings.filterwarnings('ignore')
import matplotlib.pyplot as plt

def LoadData(data, stocks):
    for stk in stocks:
        data[stk] = yf.download( stk, start = '2016-06-13', end='2016-12-13')
    
    luvdf = yf.download( "LUV", start = '2016-06-13', end='2016-12-13')
    return luvdf

def PriceReturn(data, stocks ):
    date = { 'Date':np.array([k for k in data['AAL'].index])}

    for stk in stocks:
        date[stk] = np.array([k for k in data[stk]['Adj Close']])

    price = pd.DataFrame(date) 
    price.index = price['Date']
    price = price.drop(columns = ['Date'])


    priceReturn = price.pct_change(periods = 1)
    priceReturn = priceReturn.replace(to_replace=[NaN],value = 0)
    
    return price,priceReturn

def TradingOnSignal(luvdf, priceIndustry):
    # Initialize the short and long windows
    shortWindow = 10
    longWindow = 40

    # Initialize the `signals` DataFrame with the `signal` column
    signals = pd.DataFrame(luvdf.index)
    signals.index = signals['Date']
    signals = signals.drop(columns = ['Date'])
    signals['IndSignal'] = 0.0
    signals['LuvSignal'] = 0.0

    # Create short simple moving average over the short window for industry
    signals['IndSMA'] = np.array(priceIndustry.mean(axis=1).rolling(window = shortWindow, min_periods = 1, center = False).mean())
    signals['IndLMA'] = np.array(priceIndustry.mean(axis=1).rolling(window = longWindow, min_periods = 1, center = False).mean())


    # Create short simple moving average over the short window for Soutwest
    signals['LUV_10SMA'] = np.array(luvdf['Adj Close'].rolling(window = shortWindow, min_periods = 1, center = False).mean())
    signals['LUV_40LMA'] = np.array(luvdf['Adj Close'].rolling(window = longWindow, min_periods = 1, center = False).mean())


    # Create signals
    signals['IndSignal'] = np.where(signals['IndSMA'] > signals['IndLMA'], 1.0, 0.0)

    # Signal changes from 0 to 1 (or 1 to 0)
    signals["IndPosition"] = signals["IndSignal"].diff()

    for i in range(shortWindow,signals["LuvSignal"].shape[0]):
        if signals['LUV_10SMA'][i] > signals['LUV_40LMA'][i]:
            if  any( (signals["IndPosition"][i+j] == 1 or signals["IndPosition"][i+j] == -1) for j in range(-10,1)):
                signals['LuvSignal'][i] = 1
              
    # Generate trading orders
    signals['LuvPositions'] = signals['LuvSignal'].diff()

    # Print signals
    print(signals.head(5))

    return signals

def Portfolio(luvdf, signals):
    # Set the initial capital
    initialCapital= float(100000.0)

    # Create a DataFrame `positions`
    positions =  pd.DataFrame(luvdf.index)

    positions.index = positions['Date']
    positions = positions.drop(columns = ['Date'])

    # Buy a 100 shares
    positions['LUV'] = 100* signals['LuvPositions'] 


    # Initialize the portfolio with value owned   
    portfolio = positions.multiply(luvdf['Adj Close'], axis = 0)

    # Store the difference in shares owned 
    posDiff = positions.diff()


    # Add holdings to portfolio
    portfolio['holdings'] = (positions.multiply(luvdf['Adj Close'], axis=0)).sum(axis = 1)

    # Add cash to portfolio
    portfolio['cash'] = initialCapital - (posDiff.multiply(luvdf['Adj Close'], axis = 0)).sum(axis = 1).cumsum()  


    # Add total to portfolio
    portfolio['total'] = portfolio['cash'] + portfolio['holdings']

    # Add `returns` to portfolio
    portfolio['returns'] = portfolio['total'].pct_change()

    return portfolio

def MaxDrawDown(luvdf):
    # Define a trailing 252 trading day window
    window = 252

    # Calculate the max drawdown in the past window days for each day 
    rollingMax = luvdf['Adj Close'].rolling(window, min_periods = 1).max()
    dailyDrawdown = luvdf['Adj Close']/rollingMax - 1.0

    # Calculate the minimum (negative) daily drawdown
    maxDailyDrawdown = dailyDrawdown.rolling(window, min_periods = 1).min()

    # Plot the results
    dailyDrawdown.plot()
    maxDailyDrawdown.plot()

    plt.ylabel('drawdown', fontsize = 10 )
    plt.title('MAX DRAWDOWN', fontsize = 10)  
    # Show the plot
    plt.show()
    return maxDailyDrawdown



def main():

    parser = argparse.ArgumentParser(description = "SignalOptimizationandPortfolioReturn")
    parser.add_argument("-s", "--stockSymbols", type = str, help = "REQUIRED : input stocks", default = "AAL ALK CEA ZNH VLRS CPA DAL GOL UAL")

    args = parser.parse_args()
    stocks = args.stockSymbols.split(" ")

    data = {}

    #loading data
    luvdf = LoadData(data, stocks)

    price, priceReturn = PriceReturn(data, stocks)

    lag = pd.DataFrame({'price_LUV':np.array([k for k in luvdf['Adj Close']]),
                        'daily_return_airline_industry' : priceReturn.mean(axis=1),
                        'MovingAverage(5)':luvdf['Adj Close'].rolling(5).mean(),
                        'MovingAverage(25)':luvdf['Adj Close'].rolling(25).mean()
                        })


    signalPoints = TradingOnSignal( luvdf, price)

    #print the total trading points 
    numTradingPoints = sum(signalPoints["LuvSignal"])
    print(f"Total Signal Points : {numTradingPoints}")

    # Initialize the plot figure
    fig = plt.figure()

    # Add a subplot and label for y-axis
    ax1 = fig.add_subplot(111,  ylabel='Price in $')

    # Plot the short and long moving averages
    signalPoints[['LUV_10SMA', 'LUV_40LMA']].plot(ax=ax1)

    # Plot the buy signals
    ax1.plot(signalPoints.loc[signalPoints.LuvPositions == 1.0].index, 
            signalPoints.LUV_10SMA[signalPoints.LuvPositions == 1.0],
            '^', markersize=10, color='m',label = 'buy')
         
    # Plot the sell signals
    ax1.plot(signalPoints.loc[signalPoints.LuvPositions == -1.0].index, 
            signalPoints.LUV_10SMA[signalPoints.LuvPositions == -1.0],
            'v', markersize=10, color='k',label = 'sell')

    plt.legend()
    plt.title('CROSSOVER', fontsize = 10)   
    #Show the plot
    plt.show()

    portfolio = Portfolio(luvdf, signalPoints)

    # Isolate the returns of my strategy
    returns = portfolio['returns']

    # annualized Sharpe ratio
    sharpeRatio = np.sqrt(252) * (returns.mean() / returns.std())

    # Printing the Sharpe ratio
    print(f"sharpeRatio : {sharpeRatio}")

    # Create a figure
    fig = plt.figure()

    ax1 = fig.add_subplot(111, ylabel='Portfolio value in $')

    # Plot the equity curve in dollars
    portfolio['total'].plot(ax = ax1, lw = 2.)

    ax1.plot(portfolio.loc[signalPoints.LuvPositions == 1.0].index, 
            portfolio.total[signalPoints.LuvPositions == 1.0],
            '^', markersize = 10, color='m',label = 'buy')
    ax1.plot(portfolio.loc[signalPoints.LuvPositions == -1.0].index, 
            portfolio.total[signalPoints.LuvPositions == -1.0],
            'v', markersize = 10, color='k',label = 'sell')

    plt.legend()
    plt.title('PORTFOLIO WEALTH', fontsize = 10)  
    # Show the plot
    plt.show()

    maxDailyDrawdown = MaxDrawDown(luvdf)

    #printing max drawdown
    print(f"maximum daily drawdown is : {min(maxDailyDrawdown)}")
    

if __name__=="__main__":
    main()
