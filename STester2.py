from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import undetected_chromedriver as uc
from datetime import datetime, timedelta, date
import calendar
from AccessInitiator import AccessInitiator
from CalculateGreeks import CalculateGreeks
import sched, schedule
import logging
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time, pyotp
import requests
import mibian
import pandas as pd
import json
import os

def sellCall(CallSymbol):
    print("========================Inside Sell Call==========================")
    #placeSellOrder(conn, CallSymbol)
    print("Single Call order placed")
    #========================Add Call order code here
    positionDict["straddleOrder"]["callSymbol"]=CallSymbol
    print(positionDict)

def sellPut(PutSymbol):
    print("========================Inside Sell Put==========================")
    #placeSellOrder(conn, PutSymbol)
    print("Single Put order placed")
    #========================Add Put order code here
    positionDict["straddleOrder"]["putSymbol"]=PutSymbol
    print(positionDict)

def closest_value(input_list, input_value):
  difference = lambda input_list: abs(input_list - input_value)
  res = min(input_list, key=difference)
  return res

def getMatchingStrike(df, input_value):
    deltaList = df['delta']
    difference = lambda deltaList: abs(deltaList - input_value)
    nearestDelta = min(deltaList, key=difference)
    matchingStrike = df.loc[df['delta'] == nearestDelta, 'strikes'].iloc[0]
    return matchingStrike

def getSpot(self,conn):
    return
    #interestRate = 4
    #symbolName = "BANKNIFTY"
    #bnCurrPrice = conn.quote("NSE:BANKNIFTY")
    bnOhlc = conn.ohlc(self.symbolName)
    self.bnSpot = bnOhlc[self.symbolName]['last_price']
    #self.bnSpot = 37578
    print("Banknifty Spot: ",self.bnSpot)
    return self.bnSpot
"""
putDelta = 629
print("Put Delta: ", putDelta )
bnStrike = 34500
data = {
  "strikes": [bnStrike,bnStrike+100,bnStrike+200,bnStrike+300,bnStrike+400,bnStrike+500,bnStrike-100,bnStrike-200,bnStrike-300,bnStrike-400,bnStrike-500],
  "delta": [345,967,450,790,150,560,610,502,470,650,410]
}

#load data into a DataFrame object:
df = pd.DataFrame(data)
print(df)
final=getMatchingStrike(df, putDelta)
print(final)
"""

def setActivePositions(positionDict):
    #This code writes active positions into JSON File on every trade order
    json_object = json.dumps(positionDict)
    with open("F:\\PycharmProject\\activePositions.json", "w") as outfile:
        outfile.write(json_object)

def getActivePositions():
    #This code reads the positions from JSON File on every 5minutes
    file = open("F:\\PycharmProject\\activePositions.json","r")
    positionList = json.load(file)
    print(positionList)
    #print(positionList['hedgeOrder']['callSymbol'])
    return positionList


hedgeOrder = {"callSymbol":0,"callStrike":0,"callPrice":0,"putSymbol":0,"putStrike":0,"putPrice":0}
straddleOrder = {"callSymbol":0,"callStrike":0,"callPrice":0,"putSymbol":0,"putStrike":0,"putPrice":0}
positionDict = {'hedgeOrder': {'callSymbol': 0, 'callStrike': 0, 'callPrice': 0, 'putSymbol': 0, 'putStrike': 0, 'putPrice': 0}, 'straddleOrder': {'callSymbol': 0, 'callStrike': 0, 'callPrice': 0, 'putSymbol': 0, 'putStrike': 0, 'putPrice': 0}}
#In the morning set file to empty
setActivePositions(positionDict)

#At 9.18 update with Hedge positions
positionDict=getActivePositions()
positionDict["hedgeOrder"]["callSymbol"] = "BANKNIFTY22JAN38700CE"
positionDict["hedgeOrder"]["putSymbol"] = "BANKNIFTY22JAN32700PE"
positionDict["hedgeOrder"]["callStrike"] = 38700
positionDict["hedgeOrder"]["putStrike"] = 32700
setActivePositions(positionDict)

#At 9.25 update with Straddle positions
positionDict=getActivePositions()
positionDict["straddleOrder"]["callSymbol"]  = "BANKNIFTY22JAN35700CE"
positionDict["straddleOrder"]["putSymbol"] = "BANKNIFTY22JAN35700PE"
positionDict["straddleOrder"]["callStrike"] = 35700
positionDict["straddleOrder"]["putStrike"] = 35700
setActivePositions(positionDict)

#9.35onwards read from file
getActivePositions()