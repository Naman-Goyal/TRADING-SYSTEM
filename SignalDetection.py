import datetime
import pandas as pd
import io
import matplotlib
import requests
from argparse import ArgumentParser
import argparse
from pandas_datareader import data as pdr
import yfinance as yf
import numpy as np
from numpy import NaN, NAN,nan
import matplotlib.pyplot as plt
from pandas.plotting import scatter_matrix
from pandas.plotting import register_matplotlib_converters
from matplotlib.pyplot import *
import statsmodels.api as sm
import statsmodels.formula.api as smf


apikey = "VKN1S4903YECQ0X2"

def getDailyStockPrices(symbol):
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&outputsize=full&symbol='+symbol+'&apikey='+apikey+'&datatype=csv'
    s = requests.get(url).content
    symbol_df = pd.read_csv(io.StringIO(s.decode('utf-8')))
    symbol_df = symbol_df.sort_values('timestamp', ascending=True)
    converted_timestamp = pd.to_datetime(symbol_df['timestamp'], infer_datetime_format=True)
    symbol_df.index = converted_timestamp
    symbol_df = symbol_df.drop(columns = ['timestamp'])
    return symbol_df

# get minute stock prices
def getMinuteStockPrices(symbol):
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&interval=1min&outputsize=full&symbol='+symbol+'&apikey='+apikey+'&datatype=csv'
    s = requests.get(url).content
    symbol_df = pd.read_csv(io.StringIO(s.decode('utf-8')))
    symbol_df = symbol_df.sort_values('timestamp', ascending=True)
    converted_timestamp = pd.to_datetime(symbol_df['timestamp'], infer_datetime_format=True)
    symbol_df.index = converted_timestamp
    symbol_df = symbol_df.drop(columns = ['timestamp'])
    return symbol_df

# get minute stock prices
def getLatestStockPrice(symbol):
    url = 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=' + symbol + '&apikey=' + apikey + '&datatype=csv'
    s = requests.get(url).content
    symbol_df = pd.read_csv(io.StringIO(s.decode('utf-8')))
    return symbol_df['price'].values[0]

def LoadData(data, stocks):
    for stk in stocks:
        data[stk] = yf.download(stk, start = '2014-06-02', end='2016-06-14')
        
    luvdf = pd.read_csv('LUV.csv')
    luvdf['Date'] = pd.to_datetime(luvdf['Date'])
    luvdf.index = luvdf['Date']
    luvdf = luvdf.drop(columns = ['Date'])
    luvdf = luvdf.iloc[21:]
    data['LUV'] = luvdf

def PriceData(data, stocks ):
    date = { 'Date':np.array([k for k in data['LUV'].index])}

    for stk in stocks:
        date[stk] = np.array([k for k in data[stk]['Adj Close']])
        
    date["LUV"] = np.array([k for k in data["LUV"]['Adj Close']])
    price = pd.DataFrame(date) 
    price.index = price['Date']
    price = price.drop(columns = ['Date'])

    return price

def VolumeData(data, stocks):
    date = { 'Date':np.array([k for k in data['LUV'].index])}
    
    for stk in stocks:
        date[stk] = np.array([k for k in data[stk]['Volume']])

    date["LUV"] = np.array([k for k in data["LUV"]['Volume']])
    volume = pd.DataFrame(date) 
    volume.index = volume['Date']
    volume = volume.drop(columns = ['Date'])

    return volume

def main():

    parser = argparse.ArgumentParser(description = "RiskReturnCharacterstics")
    parser.add_argument("-s", "--stockSymbols", type = str, help = "REQUIRED : input stocks", default = "AAL ALK CEA ZNH VLRS CPA DAL GOL UAL WTI")

    args = parser.parse_args()
    stocks = args.stockSymbols.split(" ")

    data = {}

    # Loading the data 
    LoadData(data,stocks)

    #pricing data 
    price = PriceData(data, stocks)

    #volumedata
    volume =VolumeData(data, stocks)

    # computing returns 
    priceReturn = price.pct_change(periods = 1)
    priceReturn = priceReturn.replace(to_replace = [NaN],value = 0)

    # plotting returns vs the volume
    plt.figure(figsize = (20,8))
    plt.scatter(x = volume['AAL'], y = priceReturn['AAL'])
    plt.xlabel('Volume AAL', fontsize = 30)
    plt.ylabel('Price Return AAL', fontsize = 30)
    plt.legend(fontsize = 30)


    # Plot raw data
    plt.figure(figsize = (20,8))
    plt.scatter(y = priceReturn['LUV'], x = volume['LUV'])
    plt.xlabel('Volume LUV', fontsize=30)
    plt.ylabel('Price Return LUV', fontsize=30)
    plt.legend(fontsize = 30)

    # checking for correlations
    for stk in stocks:
        print(volume[stk].corr(priceReturn[stk]))

    pd.plotting.scatter_matrix(priceReturn, diagonal='kde', figsize=(10, 10));  

    # computing MovingAverage 
    for key,value in data.items():
        data[key]['MovingAverage'] = data[key]['Close'].rolling(5).mean()
    

    noluv = pd.DataFrame({'Mean of daily return':priceReturn[priceReturn.columns.difference(['LUV','WTI'])].mean(axis = 1)},index = [i for i in data['AAL'].index])
    onlyluv = pd.DataFrame({'Daily_Return_LUV':[i for i in priceReturn['LUV']]},index= [i for i in data['AAL'].index])
    tt = pd.DataFrame({'NO_LUV': noluv['Mean of daily return'],'ONLY_LUV':onlyluv['Daily_Return_LUV']},index=[i for i in data['AAL'].index])
    tt.plot()

    matplotlib.rcParams['figure.figsize'] = (24, 10)
    tt.rolling(10).mean().plot()

    matplotlib.rcParams['figure.figsize'] = (15, 5)
    for stk in stocks:    
        plt.plot([priceReturn[stk].mean()],[priceReturn[stk].std()],'*')
        plt.text(priceReturn[stk].mean(),priceReturn[stk].std(),stk)
    
    plt.xlabel('RETURN', fontsize = 30)
    plt.ylabel('RISK', fontsize = 30) 

    noWTI = pd.DataFrame({'Mean_of_daily_return':priceReturn[priceReturn.columns.difference(['WTI'])].mean(axis=1)},index=[i for i in data['AAL'].index])
    plt.figure(figsize = (20,10))
    plt.scatter(x = data['WTI']['Adj Close'] , y = noWTI)
    plt.xlabel('price of Adjusted_Close of WTI', fontsize = 20)
    plt.ylabel('AVG OF daily return of whole airline industry', fontsize = 20) 

    plt.figure(figsize = (20,10))
    plt.scatter(x = priceReturn['WTI'], y = noWTI)
    plt.xlabel('Daily Return/Price Return Adjusted Close of WTI', fontsize = 20)
    plt.ylabel('AVG OF daily return of whole airline industry', fontsize = 20)

    df = pd.concat([data['WTI']['Adj Close'],noWTI],axis = 1)
    df.rename(columns = {'Adj Close':'adj_close'}, inplace = True) 
    lm = smf.ols(formula='Mean_of_daily_return ~ adj_close',data=df).fit()
    print(lm.summary())
    print(lm.params[0])
    plt.plot(df.adj_close,df.adj_close*lm.params[0] + lm.params[1])



if __name__=="__main__":
    main()