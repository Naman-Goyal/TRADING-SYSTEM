
from argparse import ArgumentParser
import argparse
from pandas_datareader import data as pdr
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import collections
from collections import OrderedDict
from numpy import NaN, NAN,nan
import statistics
from SignalOptimizationPortfolioReturn import LoadData
from SignalOptimizationPortfolioReturn import PriceReturn
from BookBuilder import BookBuilder

class TradingSystem:
    
    def __init__(self,ob):
        self.todaysDate = datetime.datetime.now().date()
        self.index = pd.date_range(self.todaysDate, periods = 1)
        self.columns = ['AdjClose_luv','AdjClose_ind']
        self.df = pd.DataFrame(index = self.index, columns = self.columns)
        self.df = self.df.drop(self.df.index[0])
        
        self.signals = pd.DataFrame(index=self.df.index,columns = ['ind_signal','luv_signal',"positions","ind_position"])        
        self.ob1 = ob
        
    
    def ProcessTick(self, adujustedPrice, industryPrice,volume):
        self.todaysDate += datetime.timedelta(days = 1)
        row = pd.Series({'AdjClose_luv':adujustedPrice,"AdjClose_ind":industryPrice},name = self.todaysDate)
        self.df = self.df.append(row)
        
        row2 = pd.Series({'ind_signal':0.0,'luv_signal':0.0,"positions":0.0},name = self.todaysDate)
        self.signals = self.signals.append(row2)
        
       
        self.CheckSignal()

        if np.array(self.signals["positions"])[-1] == 1:
             self.GenerateBuyOrder(adujustedPrice, volume)
        elif np.array(self.signals["positions"])[-1] == -1:
            self.GenerateSellOrder(adujustedPrice, volume)
        
        
    def CheckSignal(self):
        self.signals['ind_sma'] =np.array(self.df["AdjClose_ind"].rolling(window = 2).mean())
        self.signals['ind_lma'] = np.array(self.df["AdjClose_ind"].rolling(window = 14).mean())

        # Create short simple moving average over the short window
        self.signals['luv_sma'] = np.array(self.df['AdjClose_luv'].rolling(window = 2).mean())
        self.signals['luv_lma'] = np.array(self.df['AdjClose_luv'].rolling(window = 14).mean())
        
        if self.signals.shape[0] > 1:
            self.signals['ind_signal'] = np.where(self.signals['ind_sma'] > self.signals['ind_lma'], 1.0, 0.0) 
            self.signals["ind_position"] = self.signals["ind_signal"].diff()  
            for i in range(2,self.signals["luv_signal"].shape[0]):
                if self.signals['luv_sma'][i] > self.signals['luv_lma'][i]:
                     if  any( (self.signals["ind_position"][i+j] == 1 or self.signals["ind_position"][i+j] == -1) for j in range(-10,1)):
                        self.signals['luv_signal'][i] = 1
            self.signals['positions'] = self.signals['luv_signal'].diff() 
            
    def GenerateBuyOrder(self,adjustedPrice,volume):
        order = {'price':adjustedPrice, 'quantity': volume, 'exchange' :"NYSE", 'side' :"BID"}
        self.ob1.ProcessTick(order)
        print(f"BUY Stock : {adjustedPrice}$ ON {self.todaysDate}.")

    def GenerateSellOrder(self,adjustedPrice,volume):
        order = {'price':adjustedPrice, 'quantity':volume, 'exchange' :"NYSE", 'side' :"OFFER"}
        self.ob1.ProcessTick(order)
        print(f"SELL Stock : {adjustedPrice}$ ON {self.todaysDate}.")  
        
        
        
def main():
    
    parser = argparse.ArgumentParser(description = "SignalOptimizationandPortfolioReturn")
    parser.add_argument("-s", "--stockSymbols", type = str, help = "REQUIRED : input stocks", default = "AAL ALK CEA ZNH VLRS CPA DAL GOL UAL")
    parser.add_argument("-e", "--exchangeNames", type = str, help = "REQUIRED : input exchanges", default = "ARCA EDEX NYSE")

    args = parser.parse_args()
    stocks = args.stockSymbols.split(" ")

    data = {}

    #loading data
    luvdf = LoadData(data, stocks)

    price,priceReturn = PriceReturn(data, stocks)

    #EXCUTTION
    exchangeNames = args.exchangeNames.split(" ")
    book = BookBuilder(exchangeNames)
    ts = TradingSystem(book)
    southwestPrice = luvdf['Adj Close'].values
    industryPrice = price.mean(axis = 1)
    southwestVolume = luvdf['Volume'].values

    for i in range(len(southwestPrice)):
        ts.ProcessTick(southwestPrice[i],industryPrice[i],southwestVolume[i])
        
    for e in exchangeNames:
        book.DisplayTopOfBook(e)
  

if __name__=="__main__":
    main()
