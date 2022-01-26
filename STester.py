from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import undetected_chromedriver as uc
from datetime import datetime, timedelta, date
import calendar
from AccessInitiator import AccessInitiator
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

def nextExpiryDate():
    d = datetime.now()
    #print("Inside next expiry date")
    while d.weekday() != 3:
        d = d + timedelta(days=1)
    #print("Next Expiry Date: ",d)
    dayStr = str(d.strftime("%y")) + str(d.month) + str(d.day)
    #print("Next Expiry Date String: ", dayStr)
    #monthdays = calendar.monthrange(d.year, d.month)[1]
    #print(monthdays)

    #Check one more week
    nd = d + timedelta(days=1)
    while nd.weekday() != 3:
        nd = nd + timedelta(days=1)
    print("Further Next Expiry Date: ",nd)

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

def setSellStrike(self):
    #Decide the strike price
    bnStrike = round(self.bnSpot/100)*100
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

accessToken = "MG78McIEfUf6UF80GW5RMifXLYlFarQb"
print(accessToken)
api_key = 'xyipj2fx4akxggck'
print(api_key)
conn = KiteConnect(api_key=api_key)
conn.set_access_token(accessToken)
interestRate = 4
#nextExpiryDate()
#Get Positions to find the delta
positionList = conn.positions()
print(positionList['day'][0])
print(positionList['day'][0]['tradingsymbol'])
print(positionList['day'][0]['quantity'])
print(positionList['day'][0]['product'])
print(positionList['day'][0]['sell_quantity'])
print(positionList['day'][0]['sell_price'])
CallPosition = "NFO:BANKNIFTY22JAN37300CE"
PutPosition = "NFO:BANKNIFTY22JAN37300PE"
CallSymbol = "BANKNIFTY22JAN37300CE"
PutSymbol = "BANKNIFTY22JAN37300PE"
bnSpot = getSpot(conn)
netDelta = getNetDelta(conn,CallPosition,37300,PutPosition,37300)
callDelta = getCallDelta(conn,CallPosition,37300)
putDelta = getPutDelta(conn,PutPosition,37300)
print("Call Delta: ",callDelta*1000,"Put Delta: ",putDelta*1000)
callPosStatus = True
putPosStatus = True
if ((callDelta+putDelta)*1000 > 200):
    print("Delta Mismatch")
    if(abs(callDelta)>700):
        #exit CALL
        print("-------------Call Delta more than 700----------")
        exitOneLeg(conn,CallSymbol)
        callPosStatus = False
    elif(abs(putDelta)>700):
        #exit PUT
        print("-------------Put Delta more than 700----------")
        exitOneLeg(conn,PutSymbol)
        putPosStatus = False
    elif (abs(callDelta) < 400):
        # exit CALL
        print("-------------Call Delta less than 400----------")
        exitOneLeg(conn,CallSymbol)
        callPosStatus = False
    elif (abs(putDelta) < 400):
        # exit PUT
        print("-------------Put Delta less than 400----------")
        exitOneLeg(conn,PutSymbol)
        putPosStatus = False

    elif (abs(callDelta) > 450 and abs(callDelta) < 650):
        # exit PUT
        print("-------------Call Delta between 450 & 650----------")
        exitOneLeg(conn,PutSymbol)
        putPosStatus = False

    elif (abs(putDelta) > 450 and abs(putDelta) < 650):
        # exit CALL
        print("-------------Put Delta between 450 & 650----------")
        exitOneLeg(conn,CallSymbol)
        callPosStatus = False

    elif(abs(callDelta) > 650 and abs(callDelta) < 700 ):
        #Condition for 650to 700...PENDING
        print("-------------Call Delta between 650 and 700----------")
        exitOneLeg(conn,CallSymbol)

    elif (abs(putDelta) > 650 and abs(putDelta) < 700):
        #Condition for 650to 700...PENDING
        print("-------------Put Delta between 650 and 700----------")
        exitOneLeg(conn,PutSymbol)

#placeSellOrder(conn,CallSymbol)
#EXIT operations completed
if(callPosStatus==False and putPosStatus==False):
    enterFreshHedge(conn)
    enterFreshStraddle(conn)
if(callPosStatus==False and putPosStatus==True):
    #find equivalent Call Option
    enterNewLeg(conn,CallSymbol)
if(callPosStatus==True and putPosStatus==False):
    #find equivalent Put Option
    enterNewLeg(conn,PutSymbol)
