from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import undetected_chromedriver as uc
from datetime import datetime, timedelta, date
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

def nextExpiryDate():
    d = datetime.now()
    print("Inside next expiry date")
    while d.weekday() != 3:
        d = d + timedelta(days=1)
    # print("Next Expiry Date: ",d)
    dayStr = str(d.strftime("%y")) + str(d.month) + str(d.day)
    print("Next Expiry Date String: ", dayStr)
    # monthdays = calendar.monthrange(d.year, d.month)[1]
    # print(monthdays)
    # Check one more week
    nd = d + timedelta(days=1)
    while nd.weekday() != 3:
        nd = nd + timedelta(days=1)
    print("Further Next Expiry Date: ", nd)

    if (nd.month != d.month):
        print("Coming is Last Thursday of Month")
        dayStr = str(d.strftime("%y")) + (d.strftime("%b")).upper()
    print("Further Next Expiry Date: ", dayStr)
    return dayStr

def daysToExpiry():
    d = datetime.now()
    i = 0
    print("Inside number of days")
    while d.weekday() != 3:
        d = d + timedelta(days=1)
        i = i+1
    print("Days to Expiry: ",i)
    return i

def buyHedge():
    print("=========================Inside Hedge Buy=============================")
    calG.getSpot(conn)
    calG.setHedgeStrike()
    callHedge = calG.bnHStrike + 2500
    putHedge = calG.bnHStrike - 2500
    callSymbol = "NFO:BANKNIFTY" + nextExpiryDate() + str(callHedge) + "CE"
    putSymbol = "NFO:BANKNIFTY" + nextExpiryDate() + str(putHedge) + "PE"
    print("Hedge Order Placed","CallHedge: ",callHedge,"PutHedge: ",putHedge)
    #put order code here

def sellStraddle():
    print("========================Inside Sell Straddle==========================")
    calG.getSpot(conn)
    calG.setSellStrike()
    callSymbol = "NFO:BANKNIFTY" + nextExpiryDate() + str(calG.bnStrike) + "CE"
    putSymbol = "NFO:BANKNIFTY" + nextExpiryDate() + str(calG.bnStrike) + "PE"
    print("Staddle Order Placed")
    #put order code here

def checkIn5Mins():
    print("========================Inside check delta each 5 mins==========================")
    print("Time: ",datetime.now().hour,datetime.now().minute)
    #get Open Positions.
    CallPosition = "BANKNIFTY22JAN37600CE"
    PutPosition = "BANKNIFTY22JAN337600PE"
    calG.getSpot(conn)
    calG.setSellStrike()
    calG.getNetDelta(conn,CallPosition,PutPosition)

def checkDelta():
    schedule.every(1).minutes.do(checkIn5Mins)


ai = AccessInitiator()
#accessToken = ai.getAccessToken()
accessToken = "MG78McIEfUf6UF80GW5RMifXLYlFarQb"
print(accessToken)
api_key = ai.api_key
print(api_key)
conn = KiteConnect(api_key=api_key)
conn.set_access_token(accessToken)
print("Start Time: ",datetime.now().hour,datetime.now().minute)
calG = CalculateGreeks(conn)

schedule.every().day.at("14:35").do(buyHedge)
schedule.every().day.at("14:35").do(sellStraddle)
schedule.every().day.at("14:36").do(checkDelta)

#now = datetime.now()
#startTime = now.replace(hour=19, minute=7, second=0)
#endTime = now.replace(hour=23, minute=59,second=59)
#if(datetime.now() > startTime and datetime.now() < endTime):

while True:
    #while (datetime.now() > startTime and datetime.now() < endTime):
    schedule.run_pending()
    time.sleep(1)
#s = sched.scheduler(time.time,time.sleep)
#s.enter(60,1,checkIn5Mins,("0"))
#s.run()
#get next expiry date
#nextExpiryDate()
#get number of days to expiry
#daysToExpiry()
