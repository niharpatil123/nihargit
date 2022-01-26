from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import undetected_chromedriver as uc
from datetime import datetime, timedelta
import calendar
from AccessInitiator import AccessInitiator
import logging
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time, pyotp
import requests
import mibian

class CalculateGreeks:

    def __init__(self,conn):
        self.interestRate = 4
        self.baseSymbol = 'BANKNIFTY'
        self.symbolName= 'NSE:NIFTY BANK'
        self.callSymbol = ''
        self.putSymbol = ''
        self.bnSpot = ''
        self.bnStrike = ''
        self.bnHStrike = ''
        self.conn = conn

    def nextExpiryDate(self):
        d = datetime.now()
        #print("Inside next expiry date")
        while d.weekday() != 3:
            d = d + timedelta(days=1)
        #print("Next Expiry Date: ",d)
        dayStr = str(d.strftime("%y")) + str(d.month) + str(d.day)
        #print("Next Expiry Date String: ", dayStr)
        #monthdays = calendar.monthrange(d.year, d.month)[1]
        #print(monthdays)
        # Check one more week
        nd = d + timedelta(days=1)
        while nd.weekday() != 3:
            nd = nd + timedelta(days=1)
        #print("Further Next Expiry Date: ", nd)

        if (nd.month != d.month):
            #print("Coming is Last Thursday of Month")
            dayStr = str(d.strftime("%y")) + (d.strftime("%b")).upper()
        #print("Further Next Expiry Date: ", dayStr)
        return dayStr

    def daysToExpiry(self):
        d = datetime.now()
        i = 0
        #print("Inside number of days")
        while d.weekday() != 3:
            d = d + timedelta(days=1)
            i = i+1
        #print("Days to Expiry: ",i)
        return i

    #Get Nifty Spot price
    def setHedgeStrike(self):
        #Decide the strike price
        self.bnHStrike = round(self.bnSpot/500)*500
        print("Banknifty Strike: ",self.bnHStrike)

    def genStraddleBase(self):
        h = 0

    def getHedgePositions(self):
        h = 0

    def exitAllPositions(self):
        h = 0

    def getSpot(self,conn):
        #interestRate = 4
        #symbolName = "BANKNIFTY"
        #bnCurrPrice = conn.quote("NSE:BANKNIFTY")
        bnOhlc = conn.ohlc(self.symbolName)
        self.bnSpot = bnOhlc[self.symbolName]['last_price']
        self.bnSpot = 37578
        print("Banknifty Spot: ",self.bnSpot)

    def setSellStrike(self):
        #Decide the strike price
        self.bnStrike = round(self.bnSpot/100)*100
        print("Banknifty Strike: ",self.bnStrike)
        #hardcoding Strike for time being
        #bnStrike = 38400

    def getNetDelta(self, conn,CallPosition,PutPosition):
        #Generate Straddle Symbol Names
        self.callSymbol = "NFO:BANKNIFTY" + self.nextExpiryDate() + str(self.bnStrike) + "CE"
        self.putSymbol = "NFO:BANKNIFTY" + self.nextExpiryDate() + str(self.bnStrike) + "PE"
        #self.callSymbol = "NFO:BANKNIFTY" + '22JAN' + str(self.bnStrike) + "CE"
        #self.putSymbol = "NFO:BANKNIFTY" + '22JAN' + str(self.bnStrike) + "PE"
        #print("Banknifty Call Instrument: ",self.callSymbol)
        #print("Banknifty Put Instrument: ",self.putSymbol)
        positionList = []
        positionList.append(self.callSymbol)
        positionList.append(self.putSymbol)
        print(positionList)
        currPrices = conn.quote(positionList)
        #print(currPrices)
        callOhlc = conn.ohlc(self.callSymbol)
        callLtp = callOhlc[self.callSymbol]['last_price']
        #print("Call LTP: ",callLtp)
        putOhlc = conn.ohlc(self.putSymbol)
        putLtp = putOhlc[self.putSymbol]['last_price']
        print("Call LTP: ",callLtp,"Put LTP: ",putLtp)
        #Calculate the greeks
        #claculate the Call volatility first
        voltyC = mibian.BS([self.bnSpot,self.bnStrike,self.interestRate,self.daysToExpiry()],callPrice=callLtp)
        #print(voltyC.impliedVolatility)
        newVoltyC = float("{:.2f}".format(voltyC.impliedVolatility))
        #print("CallVolatility: ",newVoltyC)
        #Calculate the put volatility
        voltyP = mibian.BS([self.bnSpot,self.bnStrike,self.interestRate,self.daysToExpiry()],putPrice=putLtp)
        #print(voltyP.impliedVolatility)
        newVoltyP = float("{:.2f}".format(voltyP.impliedVolatility))
        #print("PutVolatility: ",newVoltyP)
        #Calculate the Delta
        c = mibian.BS([self.bnSpot,self.bnStrike,self.interestRate,self.daysToExpiry()],volatility=newVoltyC)
        print("Call Delta: ",c.callDelta)
        #print("Call Theta: ",c.callTheta)
        p = mibian.BS([self.bnSpot,self.bnStrike,self.interestRate,self.daysToExpiry()],volatility=newVoltyP)
        print("Put Delta: ",p.putDelta)
        #print("Put Theta: ",p.putTheta)
        netDelta = c.callDelta + p.putDelta
        print("Net Delta: ",netDelta)

logging.basicConfig(level=logging.DEBUG)
# print("Calculate Implied Volatity")
# symbol = "14350850"
# symboltxt = "BANKNIFTY20APRFUT"
# sameer key
# api_key = '7s6e8cjvyjw4bgvo'
# api_secret = 'b8yem58dwlgih4s1u2ryd7ynkj39hxck'
    #api_key = 'xyipj2fx4akxggck'
    #api_secret = 'ehzimap1bmhdbmrg2jbysn6jddxmmfr4'
    #conn = KiteConnect(api_key=api_key)
#reqToken = "ZzSjlLmxDk41APnBVE0B3VyWwEN92Bqh"
#genSession = conn.generate_session(request_token=reqToken, api_secret=api_secret)
#accToken = genSession['access_token']
    #accToken = 'xEIegYhtWS8xB6tgsnoe7dXzX4IlMYK0'
    #print(accToken)
    #conn.set_access_token(accToken)

    #myInstance = CalculateGreeks()
    #myInstance.getSpot(conn)
    #myInstance.setSellStrike()
    #myInstance.getNetDelta(conn)
    # ai = AccessInitiator()
    # print(ai.accessToken)
    # accToken = ai.getAccessToken()
    # print(accToken)
    # accToken = 'xEIegYhtWS8xB6tgsnoe7dXzX4IlMYK0'
    # conn.set_access_token(accToken)
    # conn.positions()
    # print(conn.holdings())

#Login to Zerodha & get access token
#if time is 918
    #get the spot banknifty price
    #get nearest strike price by rounding to 500
    #fire options buy

#if time is 920
    # get the spot banknifty price
    # get nearest strike price by rounding to 100
    #fire straddle

#if time > 9.24.59
    #run loop every five minutes
    #calculate delta of leg1,Leg2
    #if add delta > 0.2
        #build logic to exit delta
        #build logic to enter delta
