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

def nextExpiryDate():
    d = datetime.now()
    #print("Inside next expiry date")
    while d.weekday() != 3:
        d = d + timedelta(days=1)
    #print("Next Expiry Date: ",d)
    dayStr = str(d.strftime("%y")) + str(d.month) + str(d.day).zfill(2)
    #print("Next Expiry Date String: ", dayStr)
    #monthdays = calendar.monthrange(d.year, d.month)[1]
    #print(monthdays)

    #Check one more week
    nd = d + timedelta(days=1)
    while nd.weekday() != 3:
        nd = nd + timedelta(days=1)
    #print("Further Next Expiry Date: ",nd)

    if(nd.month != d.month):
        #print("Coming is Last Thursday")
        dayStr = str(d.strftime("%y")) + (d.strftime("%b")).upper()
    #print("Further Next Expiry Date: ", dayStr)
    return dayStr

def daysToExpiry():
    d = datetime.now()
    i = 0
    #print("Inside number of days")
    while d.weekday() != 3:
        d = d + timedelta(days=1)
        i = i+1
    #print("Days to Expiry: ",i)
    return i

def getSpot(conn):
    #interestRate = 4
    symbolName = "NSE:NIFTY BANK"
    #bnCurrPrice = conn.quote("NSE:BANKNIFTY")
    bnOhlc = conn.ohlc(symbolName)
    bnSpot = bnOhlc[symbolName]['last_price']
    print("Banknifty Spot: ",bnSpot)
    return bnSpot

def setSellStrike(bnSpot):
    #Decide the strike price
    bnStrike = round(bnSpot/100)*100
    print("Banknifty Strike: ",bnStrike)
    return bnStrike

def getNetDelta(conn,CallPosition,callStrike,PutPosition,putStrike):
    #Generate Straddle Symbol Names
    #self.callSymbol = "NFO:BANKNIFTY" + self.nextExpiryDate() + str(self.bnStrike) + "CE"
    #self.putSymbol = "NFO:BANKNIFTY" + self.nextExpiryDate() + str(self.bnStrike) + "PE"
    callSymbol = CallPosition
    putSymbol = PutPosition
    #print("Banknifty Call Instrument: ",self.callSymbol)
    #print("Banknifty Put Instrument: ",self.putSymbol)
    positionList = []
    positionList.append(callSymbol)
    positionList.append(putSymbol)
    print(positionList)
    currPrices = conn.quote(positionList)
    #print(currPrices)
    callOhlc = conn.ohlc(callSymbol)
    callLtp = callOhlc[callSymbol]['last_price']
    #print("Call LTP: ",callLtp)
    putOhlc = conn.ohlc(putSymbol)
    putLtp = putOhlc[putSymbol]['last_price']
    print("Call LTP: ",callLtp,"Put LTP: ",putLtp)
    #Calculate the greeks
    #claculate the Call volatility first
    voltyC = mibian.BS([bnSpot,callStrike,interestRate,daysToExpiry()],callPrice=callLtp)
    #print(voltyC.impliedVolatility)
    newVoltyC = float("{:.2f}".format(voltyC.impliedVolatility))
    #print("CallVolatility: ",newVoltyC)
    #Calculate the put volatility
    voltyP = mibian.BS([bnSpot,putStrike,interestRate,daysToExpiry()],putPrice=putLtp)
    #print(voltyP.impliedVolatility)
    newVoltyP = float("{:.2f}".format(voltyP.impliedVolatility))
    #print("PutVolatility: ",newVoltyP)
    #Calculate the Delta
    c = mibian.BS([bnSpot,callStrike,interestRate,daysToExpiry()],volatility=newVoltyC)
    print("Call Delta: ",c.callDelta)
    #print("Call Theta: ",c.callTheta)
    p = mibian.BS([bnSpot,putStrike,interestRate,daysToExpiry()],volatility=newVoltyP)
    print("Put Delta: ",p.putDelta)
    #print("Put Theta: ",p.putTheta)
    netDelta = c.callDelta + p.putDelta
    print("Net Delta: ",netDelta)
    return netDelta

def getCallDelta(conn,CallPosition,callStrike):
    #Generate Straddle Symbol Names
    #self.callSymbol = "NFO:BANKNIFTY" + self.nextExpiryDate() + str(self.bnStrike) + "CE"
    #self.putSymbol = "NFO:BANKNIFTY" + self.nextExpiryDate() + str(self.bnStrike) + "PE"
    callSymbol = CallPosition
    #print("Banknifty Call Instrument: ",self.callSymbol)
    #print("Banknifty Put Instrument: ",self.putSymbol)
    positionList = []
    positionList.append(callSymbol)
    print(positionList)
    currPrices = conn.quote(positionList)
    #print(currPrices)
    callOhlc = conn.ohlc(callSymbol)
    callLtp = callOhlc[callSymbol]['last_price']
    #print("Call LTP: ",callLtp)
    print("Call LTP: ",callLtp)
    #Calculate the greeks
    #claculate the Call volatility first
    voltyC = mibian.BS([bnSpot,callStrike,interestRate,daysToExpiry()],callPrice=callLtp)
    #print(voltyC.impliedVolatility)
    newVoltyC = float("{:.2f}".format(voltyC.impliedVolatility))
    #print("CallVolatility: ",newVoltyC)
    #Calculate the put volatility
    #Calculate the Delta
    c = mibian.BS([bnSpot,callStrike,interestRate,daysToExpiry()],volatility=newVoltyC)
    print("Call Delta: ",c.callDelta)
    #print("Call Theta: ",c.callTheta)
    return c.callDelta

def getPutDelta(conn,PutPosition,putStrike):
    #Generate Straddle Symbol Names
    #self.callSymbol = "NFO:BANKNIFTY" + self.nextExpiryDate() + str(self.bnStrike) + "CE"
    #self.putSymbol = "NFO:BANKNIFTY" + self.nextExpiryDate() + str(self.bnStrike) + "PE"
    putSymbol = PutPosition
    #print("Banknifty Call Instrument: ",self.callSymbol)
    #print("Banknifty Put Instrument: ",self.putSymbol)
    positionList = []
    positionList.append(putSymbol)
    print(positionList)
    currPrices = conn.quote(positionList)
    #print(currPrices)
    #print("Call LTP: ",callLtp)
    putOhlc = conn.ohlc(putSymbol)
    putLtp = putOhlc[putSymbol]['last_price']
    print("Put LTP: ",putLtp)
    #Calculate the greeks
    #claculate the Call volatility first
    #Calculate the put volatility
    voltyP = mibian.BS([bnSpot,putStrike,interestRate,daysToExpiry()],putPrice=putLtp)
    #print(voltyP.impliedVolatility)
    newVoltyP = float("{:.2f}".format(voltyP.impliedVolatility))
    #print("PutVolatility: ",newVoltyP)
    #Calculate the Delta
    p = mibian.BS([bnSpot,putStrike,interestRate,daysToExpiry()],volatility=newVoltyP)
    print("Put Delta: ",p.putDelta)
    #print("Put Theta: ",p.putTheta)
    return p.putDelta

def placeBuyOrder(conn,tradeSymbol):
    order = conn.place_order(tradingsymbol=tradeSymbol, quantity=25, exchange=conn.EXCHANGE_NFO,order_type=conn.ORDER_TYPE_MARKET,
                             transaction_type=conn.TRANSACTION_TYPE_BUY,product=conn.PRODUCT_MIS,variety=conn.VARIETY_REGULAR)

def placeSellOrder(conn,tradeSymbol):
    order = conn.place_order(tradingsymbol=tradeSymbol, quantity=25, exchange=conn.EXCHANGE_NFO,order_type=conn.ORDER_TYPE_MARKET,
                             transaction_type=conn.TRANSACTION_TYPE_SELL,product=conn.PRODUCT_MIS,variety=conn.VARIETY_REGULAR)

def exitOneLeg(conn,tradeSymbol):
    print("Exit One Leg")
    #order = conn.place_order()
    #cover sell position
    #cover hedge position

def enterNewLeg(conn,tradeSymbol):
    print("Enter New Leg")
    #order = conn.place_order()
    #buy Hedge
    #Sell one leg

def exitAllPositions(conn):
    #order = conn.place_order()
    print("Exit All Positions")

def enterFreshHedge(conn):
    print("Enter Fresh Hedge")
    bnSpot = getSpot(conn)
    bnStrike = setSellStrike()
    callHedge = bnStrike + 2500
    putHedge = bnStrike - 2500
    callSymbol = "NFO:BANKNIFTY" + nextExpiryDate() + str(callHedge) + "CE"
    putSymbol = "NFO:BANKNIFTY" + nextExpiryDate() + str(putHedge) + "PE"
    placeBuyOrder(conn,callSymbol)
    placeBuyOrder(conn, putSymbol)

def enterFreshStraddle(conn):
    print("Enter fresh straddle")
    bnSpot = getSpot(conn)
    bnStrike = setSellStrike()
    callSymbol = "NFO:BANKNIFTY" + nextExpiryDate() + str(bnStrike) + "CE"
    putSymbol = "NFO:BANKNIFTY" + nextExpiryDate() + str(bnStrike) + "PE"
    placeSellOrder(conn,callSymbol)
    placeSellOrder(conn, putSymbol)

def getActivePositions():
    #positionList = conn.positions()
    #with open("F:\\PycharmProject\\position.json","r") as f:
    #    data = f.read
    #    print(data)
    file = open("F:\\PycharmProject\\position.json","r")
    positionList = json.load(file)
    for i in positionList['day']:
        #print(i)
        if(i['tradingsymbol'].endswith("CE") and i['quantity'] < 0 ):
            straddleOrder["callSymbol"] = i['tradingsymbol']
            straddleOrder["callPrice"] = i['last_price']
        elif (i['tradingsymbol'].endswith("PE") and i['quantity'] < 0 ):
            straddleOrder["putSymbol"] = i['tradingsymbol']
            straddleOrder["putPrice"] = i['last_price']
        elif (i['tradingsymbol'].endswith("CE") and i['quantity'] > 0 ):
            hedgeOrder["callSymbol"] = i['tradingsymbol']
            hedgeOrder["callPrice"] = i['last_price']
        elif (i['tradingsymbol'].endswith("PE") and i['quantity'] > 0 ):
            hedgeOrder["putSymbol"] = i['tradingsymbol']
            hedgeOrder["putPrice"] = i['last_price']
    print(straddleOrder)
    print(hedgeOrder)

def getStrikeFromSymbol(tradeSymbol):
    print("Enter fresh straddle")
    return int(tradeSymbol[:-2][-5:])

def getMatchingDelta():
    print("Find Matching Delta & Strike Price")

def closest_value(input_list, input_value):
    difference = lambda input_list: abs(input_list - input_value)
    res = min(input_list, key=difference)
    return res

def getDeltaDataFrameCE(bnSpot,optionType):
    bnStrike = setSellStrike(bnSpot)
    data = {
        "strikes": [bnStrike,bnStrike+100,bnStrike+200,bnStrike+300,bnStrike+400,bnStrike+500,bnStrike-100,bnStrike-200,bnStrike-300,bnStrike-400,bnStrike-500],
        "delta": [0,0,0,0,0,0,0,0,0,0,0]
    }
    #load data into a DataFrame object:
    df = pd.DataFrame(data)
    print(df)
    for index,row in df.iterrows():
        print("Strike: ", row['strikes'])
        callStrike = row['strikes']
        CallPosition = "NFO:BANKNIFTY" + nextExpiryDate() + str(callStrike) + optionType
        callDelta = getCallDelta(conn,CallPosition,callStrike)
        df.at[index, 'delta'] = abs(callDelta*1000)
    print(df)
    return df

def getDeltaDataFramePE(bnSpot,optionType):
    bnStrike = setSellStrike(bnSpot)
    data = {
        "strikes": [bnStrike,bnStrike+100,bnStrike+200,bnStrike+300,bnStrike+400,bnStrike+500,bnStrike-100,bnStrike-200,bnStrike-300,bnStrike-400,bnStrike-500],
        "delta": [0,0,0,0,0,0,0,0,0,0,0]
    }
    #load data into a DataFrame object:
    df = pd.DataFrame(data)
    print(df)
    for index,row in df.iterrows():
        print("Strike: ", row['strikes'])
        putStrike = row['strikes']
        PutPosition = "NFO:BANKNIFTY" + nextExpiryDate() + str(putStrike) + optionType
        putDelta = getPutDelta(conn,PutPosition,putStrike)
        df.at[index, 'delta'] = abs(putDelta*1000)
    print(df)
    return df

def getMatchingStrike(df, input_value):
    deltaList = df['delta']
    difference = lambda deltaList: abs(deltaList - input_value)
    nearestDelta = min(deltaList, key=difference)
    matchingStrike = df.loc[df['delta'] == nearestDelta, 'strikes'].iloc[0]
    return matchingStrike

def checkEvery5mins():
    CallPosition = "NFO:BANKNIFTY22JAN37300CE"
    PutPosition = "NFO:BANKNIFTY22JAN37300PE"
    CallSymbol = "BANKNIFTY22JAN37300CE"
    PutSymbol = "BANKNIFTY22JAN37300PE"
    bnSpot = getSpot(conn)
    netDelta = getNetDelta(conn, CallPosition, 37300, PutPosition, 37300)
    callDelta = getCallDelta(conn, CallPosition, 37300)
    putDelta = getPutDelta(conn, PutPosition, 37300)
    print("Call Delta: ", callDelta * 1000, "Put Delta: ", putDelta * 1000)
    callPosStatus = True
    putPosStatus = True
    if ((callDelta + putDelta) * 1000 > 200):
        print("Delta Mismatch")
        if (abs(callDelta) > 700):
            # exit CALL
            print("-------------Call Delta more than 700----------")
            exitOneLeg(conn, CallSymbol)
            callPosStatus = False
        elif (abs(putDelta) > 700):
            # exit PUT
            print("-------------Put Delta more than 700----------")
            exitOneLeg(conn, PutSymbol)
            putPosStatus = False
        elif (abs(callDelta) < 400):
            # exit CALL
            print("-------------Call Delta less than 400----------")
            exitOneLeg(conn, CallSymbol)
            callPosStatus = False
        elif (abs(putDelta) < 400):
            # exit PUT
            print("-------------Put Delta less than 400----------")
            exitOneLeg(conn, PutSymbol)
            putPosStatus = False

        elif (abs(callDelta) > 450 and abs(callDelta) < 650):
            # exit PUT
            print("-------------Call Delta between 450 & 650----------")
            exitOneLeg(conn, PutSymbol)
            putPosStatus = False

        elif (abs(putDelta) > 450 and abs(putDelta) < 650):
            # exit CALL
            print("-------------Put Delta between 450 & 650----------")
            exitOneLeg(conn, CallSymbol)
            callPosStatus = False

        elif (abs(callDelta) > 650 and abs(callDelta) < 700):
            # Condition for 650to 700...PENDING
            print("-------------Call Delta between 650 and 700----------")
            exitOneLeg(conn, CallSymbol)

        elif (abs(putDelta) > 650 and abs(putDelta) < 700):
            # Condition for 650to 700...PENDING
            print("-------------Put Delta between 650 and 700----------")
            exitOneLeg(conn, PutSymbol)

    # placeSellOrder(conn,CallSymbol)
    # EXIT operations completed
    if (callPosStatus == False and putPosStatus == False):
        enterFreshHedge(conn)
        enterFreshStraddle(conn)
    if (callPosStatus == False and putPosStatus == True):
        # find equivalent Call Option
        enterNewLeg(conn, CallSymbol)
    if (callPosStatus == True and putPosStatus == False):
        # find equivalent Put Option
        enterNewLeg(conn, PutSymbol)

#========Main Code Starts Here
accessToken = "ppIj55RjlhXlX0mKKc31B4kFfZOSUlvG"
print(accessToken)
api_key = 'xyipj2fx4akxggck'
print(api_key)
conn = KiteConnect(api_key=api_key)
conn.set_access_token(accessToken)
interestRate = 4
#nextExpiryDate()
#Get Positions to find the delta
#positionList = conn.positions()
hedgeOrder = {"callSymbol":0,"callStrike":0,"callPrice":0,"putSymbol":0,"putStrike":0,"putPrice":0}
straddleOrder = {"callSymbol":0,"callStrike":0,"callPrice":0,"putSymbol":0,"putStrike":0,"putPrice":0}
bnSpot = getSpot(conn)

#getActivePositions()
#checkEvery5mins()
#getMatchingDelta()
#voltyP = mibian.BS([bnSpot, 37300, interestRate,1], putPrice=184)
# print(voltyP.impliedVolatility)
#newVoltyP = float("{:.2f}".format(voltyP.impliedVolatility))
# Calculate the Delta
#p = mibian.BS([bnSpot,37300, interestRate,1], volatility=newVoltyP)
#print("Put Delta Calculation: ",p.putDelta)

CallPosition = "NFO:BANKNIFTY2220338200CE"
CallSymbol = "BANKNIFTY2220338200CE"
PutPosition = "NFO:BANKNIFTY2220338200PE"
PutSymbol = "BANKNIFTY2220338200PE"
bnSpot = getSpot(conn)
print("Before........")
putDelta = getPutDelta(conn, PutPosition, 38200)
callDelta = getCallDelta(conn, CallPosition, 38200)
print("After........")
print("Call Delta: ", callDelta * 1000,"Put Delta: ", putDelta * 1000)
#Next 2 lines get nearest 10prices of spot, calculate the delta of each and match delta
df = getDeltaDataFrameCE(bnSpot,"CE")
newStrike = getMatchingStrike(df, abs(putDelta) * 1000)
print("New Strike: ", newStrike)

#bnStrike = setSellStrike(bnSpot)
#data = {
#  "strikes": [bnStrike,bnStrike+100,bnStrike+200,bnStrike+300,bnStrike+400,bnStrike+500,bnStrike-100,bnStrike-200,bnStrike-300,bnStrike-400,bnStrike-500],
#  "delta": [0,0,0,0,0,0,0,0,0,0,0]
#}

#load data into a DataFrame object:
#df = pd.DataFrame(data)
#for index,row in df.iterrows():
#    print("Strike: ", row['strikes'])
#    callStrike = row['strikes']
#    CallPosition = "NFO:BANKNIFTY" + nextExpiryDate() + str(callStrike) + "CE"
#    callDelta = getCallDelta(conn,CallPosition,callStrike)
#    df.at[index, 'delta'] = callDelta*1000
#print(df)
