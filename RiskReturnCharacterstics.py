from argparse import ArgumentParser
import pandas as pd
import numpy as np
import argparse
import statistics
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt


def LoadData(stocksDf, stockNames, marketData):
    for i in range(len(stocksDf)):
        stocksDf[i].columns = ["Unnamed","datestamp",'Open', 'High',"Low","Close","Volume","Adjusted"]
        stocksDf[i].name=stockNames[i]
        
        marketData[stockNames[i]]={
        'Open':list(stocksDf[i]['Open']),
        'High':list(stocksDf[i]['High']),
        'Low':list(stocksDf[i]['Low']),
        'Close':list(stocksDf[i]['Close']),
        "Volume":list(stocksDf[i]['Volume']),
        "Adjusted":list(stocksDf[i]['Adjusted']),
        "Date": list(stocksDf[i]['datestamp']),
        "MA_10":[]
    }

def MovingAverage(marketData):

    for key,value in marketData.items():
        close = marketData[key]["Close"]
        ma = [None if i in (0,1,2,3,4,5,6,7,8) else statistics.mean(close[i-9:i+1]) for i   in range(0,len(close))]
        marketData[key].update({"MA_10":ma})

def DailyReturn(marketData):
    for key,value in marketData.items():
        adjusted = marketData[key]["Adjusted"]
        dailyReturn = [0 if i == 0 else (adjusted[i]-adjusted[i-1])/adjusted[i-1] for i in range(0,len(adjusted))]
        marketData[key]['DAILY_RETURN'] = dailyReturn

def MaximumReturn(marketData):
    maxReturn = 0

    for key,value in marketData.items():
        maxDailyReturn = max(marketData[key]['DAILY_RETURN'])
        if maxDailyReturn > maxReturn:
            maxReturn = maxDailyReturn
            dailyReturnIndex = marketData[key]['DAILY_RETURN'].index(maxDailyReturn)
            date = marketData[key]['Date'][dailyReturnIndex]
    maxReturn *= 100
    maxReturn = round(maxReturn ,2)
        
    return maxReturn, date 

def MinimumReturn(marketData):
    minReturn = 0

    for key,value in marketData.items():
        minDailyReturn = min(marketData[key]['DAILY_RETURN'])
        if minDailyReturn < minReturn:
            minReturn = minDailyReturn
            dailyReturnIndex = marketData[key]['DAILY_RETURN'].index(minDailyReturn)
            date = marketData[key]['Date'][dailyReturnIndex]

    minReturn *= 100
    minReturn = round(minReturn,2)

    return minReturn, date

def MaxReturnInTheMonth(marketData):
    maxaOneMonthReturn = 0
   
    for key,value in marketData.items():

        startDate = 0
        endDate = startDate + 30 
        price = marketData[key]["Adjusted"]

        while(endDate < len(marketData[key]['DAILY_RETURN'])):
       
            maxReturnGivenMonth = (price[endDate]-price[startDate] )/price[startDate]
        
            if maxReturnGivenMonth > maxaOneMonthReturn:
                maxaOneMonthReturn = maxReturnGivenMonth
                date = marketData[key]['Date'][startDate]

            startDate = startDate + 30
            endDate = startDate + 30 
            
            
    dt = datetime.strptime(date,"%Y-%m-%d")
    date = str(dt.month)+"/" + str(dt.year)

    maxaOneMonthReturn = round(maxaOneMonthReturn * 100 ,2)
    
    return maxaOneMonthReturn, date



def main():

    parser = argparse.ArgumentParser(description = "RiskReturnCharacterstics")
    parser.add_argument("-s", "--stockNames", type = str, help = "REQUIRED : input stocks", default = "NVDA GOOGL MSFT EBAY FB TSLA AMZN")
    parser.add_argument("-f","--fileNames", type = str, help = "REQUIRED: stock csv files", default = "NVDA.csv GOOGL.csv MSFT.csv EBAY.csv FB.csv TSLA.csv AMZN.csv")

    args = parser.parse_args()


    marketData = {}
    stockNames = args.stockNames.split(" ")
    fileNames = args.fileNames.split(" ")

    #reading the csv files 
    stocksDf=[pd.read_csv(i) for i in fileNames]

    #Loading Data
    LoadData(stocksDf, stockNames, marketData)

    #Calculating Moving Average 
    MovingAverage(marketData)

    # Calculating Daily Returns
    DailyReturn(marketData)

    # Computing Maimum Return 
    maxReturn, date = MaximumReturn( marketData)

    #Telling the user his maximum return 
    print(f"The Maximum Return you can earn is : {maxReturn} % on the following day : {date} ")

    # Computing Minimum Return 
    minReturn, date = MinimumReturn( marketData)

    #Telling the user his minimum return 
    print(f"The Minimum Return you can earn is : {minReturn} % on the following day : {date} ")

    # Computing Maximum Return In a Month
    maxaOneMonthReturn, date = MaxReturnInTheMonth(marketData)
    print(f"The Maximum Return in a month you can earn is : {maxaOneMonthReturn} % on the following day : {date} ")


    # Plot 
    plt.figure(figsize=(15,10))
    for key, value in marketData.items():
        plt.plot(marketData[key]['Date'],marketData[key]['Close'])
    plt.xlabel("Date",fontsize=20)
    plt.ylabel("Daily Market price",fontsize=20)
    plt.show()



if __name__=="__main__":
    main()