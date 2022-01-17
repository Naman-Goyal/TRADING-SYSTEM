from argparse import ArgumentParser
import argparse
import pandas as pd
import numpy as np
import statistics
import datetime as dt
import matplotlib
import matplotlib.pyplot as plt
from collections import OrderedDict


def PrProcessData(data):
    for ex in data:
        ex.index = ex['Time'].apply((lambda x: x.zfill(8)))
        ex.drop( columns=['Time'], inplace = True)


    data = pd.concat(data)

    data.sort_index(inplace = True)

    
    data.Side[data.Side == 1] = "BID"
    data.Side[data.Side == 0]   = "OFFER"

    return data


class BookBuilder:
    
    def __init__(self, exchangesDf):

        self.bid = {}
        self.offer = {}

        self.Initialize(exchangesDf)

    def Initialize(self, exchangesDf):
        exchanges = exchangesDf['Exchange'].unique()

        for ex in exchanges:
            self.bid[ex] = {0 : 0 }
            self.offer[ex] = {0 : 0 }
     

    def ProcessTick(self,order):
        if order['side'] == 'BID':
            self.bid[order['exchange']].update({order['price'] : order['quantity']})
        
        elif order['side']=="OFFER":
            self.offer[order['exchange']].update({order['price'] : order['quantity']})
           
        self.TopOfBook(order['exchange'])
        
    def TopOfBook(self, exchange):
        for key, value in self.bid.items():
            self.bid [key] = OrderedDict(sorted(value.items() , reverse = True ))

        for key, value in self.offer.items():
            self.offer [key] = OrderedDict(sorted(value.items() ))

        self.DisplayTopOfBook(exchange)

    def DisplayTopOfBook(self, exchange):

        print("BID",list(self.bid[exchange].keys())[0]) 
        print("OFFER",list(self.offer[exchange].keys())[0]) 

    
    def GetBidVolumeBetween(self, price1, price2):
        vol = 0
        for key,val in self.od1.items():
            if val['price']<=price2 and val['price'] >= price1:
                vol += val['quantity']
        return vol

    def GetOfferVolumeBetween(self, price1, price2):
        vol = 0

        for key,val in self.od2.items():
            if val['price'] <= price2 and val['price'] >= price1:
                vol += val['quantity']
        return vol
        
def main():

    parser = argparse.ArgumentParser(description = "RiskReturnCharacterstics")
    parser.add_argument("-s", "--exchangeNames", type = str, help = "REQUIRED : input exchanges", default = "ARCA EDEX NYSE")
    parser.add_argument("-f","--fileNames", type = str, help = "REQUIRED: stock csv files", default = "arca_aapl.csv edgex_aapl.csv nyse_aapl.csv")

    args = parser.parse_args()


    
    exchangeNames = args.exchangeNames.split(" ")
    fileNames = args.fileNames.split(" ")

    #reading the csv files 
    exchangesDf = [pd.read_csv(i) for i in fileNames]

    #Loading Data
    exchangesDf = PrProcessData(exchangesDf)

    # Creating Book 
    book = BookBuilder(exchangesDf)
    exchangesDfArr = exchangesDf.to_numpy()

    # Process Orders
    for i in range(0,len(exchangesDfArr),10000):
        order = {'price': exchangesDfArr[i][0], 'quantity':exchangesDfArr[i][1], 'side' :exchangesDfArr[i][2], 'exchange' :exchangesDfArr[i][3]}
        book.ProcessTick(order)

if __name__=="__main__":
    main()