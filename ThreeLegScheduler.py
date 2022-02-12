from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import undetected_chromedriver as uc
from datetime import datetime, timedelta, date
from AccessInitiator import AccessInitiator
from CalculateGreeks import CalculateGreeks
from TelegramMessenger import TelegramMessenger
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

def nextExpiryDate():
    d = datetime.now()
    #print("Inside next expiry date")
    while d.weekday() != 3:
        d = d + timedelta(days=1)
    # print("Next Expiry Date: ",d)
    dayStr = str(d.strftime("%y")) + str(d.month) + str(d.day).zfill(2)
    #print("Next Expiry Date String: ", dayStr)
    # monthdays = calendar.monthrange(d.year, d.month)[1]
    # print(monthdays)
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

def daysToExpiry():
    d = datetime.now()
    i = 0
    #print("Inside number of days")
    while d.weekday() != 3:
        d = d + timedelta(days=1)
        i = i+1
    # to manage last day of expiry. TO avoid divide by zero
    if (i == 0):
        i = 0.00001
    print("Days to Expiry: ",i)
    return i

def closest_value(input_list, input_value):
  difference = lambda input_list: abs(input_list - input_value)
  res = min(input_list, key=difference)
  return res

def setActivePositions(positionDict):
    #This code writes active positions into JSON File on every trade order
    json_object = json.dumps(positionDict)
    with open("F:\\PycharmProject\\activePositions3Leg.json", "w") as outfile:
        outfile.write(json_object)

def getActivePositions():
    #This code reads the positions from JSON File on every 5minutes
    file = open("F:\\PycharmProject\\activePositions3Leg.json","r")
    positionList = json.load(file)
    #print(positionList)
    #print(positionList['hedgeOrder']['callSymbol'])
    return positionList

def get3LegConfig():
    #This code reads the positions from JSON File on every 5minutes
    file = open("F:\\PycharmProject\\ThreeLegConfig.json","r")
    slConfigDic = json.load(file)
    #print(positionList)
    #print(positionList['hedgeOrder']['callSymbol'])
    return slConfigDic



def buyHedge():
    print("=========================Inside Hedge Buy=============================")
    calG.getSpot(conn)
    calG.setHedgeStrike()
    callHedge = calG.bnHStrike + 3000
    putHedge = calG.bnHStrike - 3000
    callPosition = "NFO:BANKNIFTY" + nextExpiryDate() + str(callHedge) + "CE"
    putPosition = "NFO:BANKNIFTY" + nextExpiryDate() + str(putHedge) + "PE"
    #=============================put order code here
    placeBuyOrder(conn, callPosition[4:])
    placeBuyOrder(conn, putPosition[4:])
    print("Hedge Order Placed","CallHedge: ",callHedge,"PutHedge: ",putHedge)
    positionDict["hedgeOrder"]["callSymbol"] = callPosition[4:]
    positionDict["hedgeOrder"]["putSymbol"] = putPosition[4:]
    positionDict["hedgeOrder"]["callStrike"] = callHedge
    positionDict["hedgeOrder"]["putStrike"] = putHedge
    print(positionDict)
    tm.telegram_sendmsg("Hedge order placed::", "0")
    tm.telegram_sendmsg("Call Hedge:: " + str(int(callHedge)) + " :::: " + "Put Hedge:: " + str(int(putHedge)), "0")
    setActivePositions(positionDict)

def sellStraddle():
    print("========================Inside Sell Straddle==========================")
    callEntryPrice = 0
    putEntryPrice = 0
    #calG.getSpot(conn)
    #calG.setSellStrike()
    bnSpot = calG.getSpot(conn)
    strikePrice = calG.setSellStrike(bnSpot)
    #strikePrice = calG.bnStrike
    #Next 2 lines commented temporarily
    callPosition = "NFO:BANKNIFTY" + nextExpiryDate() + str(strikePrice) + "CE"
    putPosition = "NFO:BANKNIFTY" + nextExpiryDate() + str(strikePrice) + "PE"
    #callPosition = "NFO:BANKNIFTY2220338200CE"
    #putPosition = "NFO:BANKNIFTY2220338200PE"
    #strikePrice = 38200
    #========================Add order code here
    callOrderId = placeSellOrder(conn, callPosition[4:])
    putOrderId = placeSellOrder(conn, putPosition[4:])
    print("Staddle Order Placed")
    orderList = conn.orders()
    print(orderList)
    for i in orderList:
        if(callOrderId == i['order_id']):
            callEntryPrice = i['average_price']
        elif(putOrderId == i['order_id']):
            putEntryPrice = i['average_price']
        print(i['order_id'],i['tradingsymbol'],i['transaction_type'],i['guid'],i['average_price'])

    positionDict = getActivePositions()
    positionDict["straddleOrder"]["callSymbol"] = callPosition[4:]
    positionDict["straddleOrder"]["putSymbol"] = putPosition[4:]
    positionDict["straddleOrder"]["callStrike"] = strikePrice
    positionDict["straddleOrder"]["putStrike"] = strikePrice
    positionDict["straddleOrder"]["callOrderId"] = callOrderId
    positionDict["straddleOrder"]["putOrderId"] = putOrderId
    positionDict["straddleOrder"]["callEntryPrice"] = callEntryPrice
    positionDict["straddleOrder"]["putEntryPrice"] = putEntryPrice
    setActivePositions(positionDict)
    print(positionDict)
    tm.telegram_sendmsg("Straddle order placed::"+str(int(strikePrice)), "0")

def setSLOrders(leg):
    print("===============Set SL Orders===============")
    callTriggerPrice = 0
    callSlPrice = 0
    putTriggerPrice = 0
    putSlPrice = 0
    #positionList = conn.positions()
    positionDict = getActivePositions()
    print(positionDict)

    CallPosition = "NFO:" + positionDict["straddleOrder"]["callSymbol"]
    PutPosition = "NFO:" + positionDict["straddleOrder"]["putSymbol"]
    #remove NFO: from symbol
    CallSymbol = positionDict["straddleOrder"]["callSymbol"]
    PutSymbol = positionDict["straddleOrder"]["putSymbol"]
    CallStrike = positionDict["straddleOrder"]["callStrike"]
    PutStrike = positionDict["straddleOrder"]["putStrike"]
    CallEntry = positionDict["straddleOrder"]["callEntryPrice"]
    PutEntry = positionDict["straddleOrder"]["putEntryPrice"]
    CallEntryPrice = round(0.05 * round(CallEntry/0.05),2)
    PutEntryPrice = round(0.05 * round(PutEntry/0.05),2)

    if (leg == "leg1"):
        factor = slConfigDic["pct"]["leg1pct"][weekday]
        print("Percentage factor:",str(factor))
        CallTP = CallEntryPrice*(1+factor/100)
        callTriggerPrice = round(0.05 * round(CallTP/0.05),2)
        callSlPrice = callTriggerPrice + 2
        PutTP = PutEntryPrice*(1+factor/100)
        putTriggerPrice = round(0.05 * round(PutTP/0.05),2)
        putSlPrice = putTriggerPrice + 2
        placeSLOrder(conn, CallSymbol, callTriggerPrice, callSlPrice)
        placeSLOrder(conn, PutSymbol, putTriggerPrice, putSlPrice)
    elif (leg == "leg2"):
        factor = slConfigDic["pct"]["leg2pct"][weekday]
        print("Percentage factor:",str(factor))
        CallTP = CallEntryPrice * (1 + factor / 100)
        callTriggerPrice = round(0.05 * round(CallTP / 0.05), 2)
        callSlPrice = callTriggerPrice + 2
        PutTP = PutEntryPrice * (1 + factor / 100)
        putTriggerPrice = round(0.05 * round(PutTP / 0.05), 2)
        putSlPrice = putTriggerPrice + 2
        placeSLOrder(conn, CallSymbol, callTriggerPrice, callSlPrice)
        placeSLOrder(conn, PutSymbol, putTriggerPrice, putSlPrice)
    elif (leg == "leg3"):
        factor = slConfigDic["pct"]["leg3pct"][weekday]
        print("Percentage factor:",str(factor))
        CallTP = CallEntryPrice * (1 + factor / 100)
        callTriggerPrice = round(0.05 * round(CallTP / 0.05), 2)
        callSlPrice = callTriggerPrice + 2
        PutTP = PutEntryPrice * (1 + factor / 100)
        putTriggerPrice = round(0.05 * round(PutTP / 0.05), 2)
        putSlPrice = putTriggerPrice + 2
        placeSLOrder(conn, CallSymbol, callTriggerPrice, callSlPrice)
        placeSLOrder(conn, PutSymbol, putTriggerPrice, putSlPrice)

def exitHedge():
    print("===============Exit Hedge===============")
    positionList = conn.positions()
    #file = open("F:\\PycharmProject\\position2.json","r")
    #positionList = json.load(file)
    for i in positionList["day"]:
        if (i['quantity'] > 0 ):
            placeSellOrder(conn, i["tradingsymbol"])

def exitStraddle():
    print("======================Exit Straddle========================")
    positionList = conn.positions()
    #file = open("F:\\PycharmProject\\position2.json","r")
    #positionList = json.load(file)
    for i in positionList["day"]:
        print(i["tradingsymbol"],"::::",i["quantity"])
        if(i["quantity"] < 0 ):
            placeBuyOrder(conn, i["tradingsymbol"])

def exitAllPositions():
    print("====================Exit All Positions===========================")
    positionList = conn.positions()
    #file = open("F:\\PycharmProject\\position2.json","r")
    #positionList = json.load(file)
    for i in positionList["day"]:
        print(i["tradingsymbol"],"::::",i["quantity"])
        if(i["quantity"] < 0 ):
            placeBuyOrder(conn, i["tradingsymbol"])
        elif (i['quantity'] > 0 ):
            placeSellOrder(conn, i["tradingsymbol"])

def exitOneLeg(conn,tradeSymbol):
    print("Exit One Leg: ",tradeSymbol)
    placeBuyOrder(conn, tradeSymbol)
    #order = conn.place_order()
    #cover sell position
    #cover hedge position

def placeBuyOrder(conn,tradeSymbol):
    order = conn.place_order(tradingsymbol=tradeSymbol, quantity=100, exchange=conn.EXCHANGE_NFO,order_type=conn.ORDER_TYPE_MARKET,
                             transaction_type=conn.TRANSACTION_TYPE_BUY,product=conn.PRODUCT_MIS,variety=conn.VARIETY_REGULAR)
    print("Buy Order Successfully Placed for::::",tradeSymbol)


def placeSellOrder(conn,tradeSymbol):
    #order = 1
    order = conn.place_order(tradingsymbol=tradeSymbol, quantity=100, exchange=conn.EXCHANGE_NFO,order_type=conn.ORDER_TYPE_MARKET,
                             transaction_type=conn.TRANSACTION_TYPE_SELL,product=conn.PRODUCT_MIS,variety=conn.VARIETY_REGULAR)
    print("Sell Order Successfully Placed for::::",tradeSymbol)
    return order

def placeSLOrder(conn,tradeSymbol,triggerPrice,slPrice):
    order = conn.place_order(tradingsymbol=tradeSymbol, quantity=100, exchange=conn.EXCHANGE_NFO,order_type=conn.ORDER_TYPE_SL,
                             transaction_type=conn.TRANSACTION_TYPE_BUY,product=conn.PRODUCT_MIS,variety=conn.VARIETY_REGULAR,
                             trigger_price=triggerPrice,price=slPrice)
    print("SL Order Successfully Placed for::::",tradeSymbol)

def checkPNL():
    margin = conn.margins()
    realized = margin['equity']['utilised']['m2m_realised']
    unrealized = margin['equity']['utilised']['m2m_unrealised']
    total = realized + unrealized
    tm.telegram_sendmsg("Net Profit::: \\" + str(int(total)), "0")

def checkStatus():
    schedule.every(5).minutes.do(checkPNL())

#================================Main Starts here=========================================
print("Start Time: ",datetime.now().hour,":",datetime.now().minute,":",datetime.now().second)
ai = AccessInitiator()
#accessToken = ai.getAccessToken()
accessToken = "qH2YZXHdh2luFqC6D2VWI3e07pVxA5cb"
print(accessToken)
api_key = ai.api_key
print(api_key)
conn = KiteConnect(api_key=api_key)
conn.set_access_token(accessToken)
calG = CalculateGreeks(conn)
weekday = datetime.today().strftime('%A')
#weekday = "Friday"
print(weekday)
slConfigDic = get3LegConfig()
#print(slConfigDic["time"]["leg1"]["starttime"])
#print(slConfigDic["pct"]["leg1pct"][weekday])
#leg = "leg1"

tm = TelegramMessenger()
#Initialize the dictionaties
#hedgeOrder = {"callSymbol":0,"callStrike":0,"callPrice":0,"putSymbol":0,"putStrike":0,"putPrice":0}
#straddleOrder = {"callSymbol":0,"callStrike":0,"callPrice":0,"putSymbol":0,"putStrike":0,"putPrice":0}
positionDict = {'hedgeOrder': {'callSymbol': 0, 'callStrike': 0, 'callPrice': 0, 'putSymbol': 0, 'putStrike': 0, 'putPrice': 0}, 'straddleOrder': {'callSymbol': 0, 'callStrike': 0, 'callPrice': 0, 'putSymbol': 0, 'putStrike': 0, 'putPrice': 0}}

#schedule.every().day.at("00:13").do(buyHedge)
schedule.every().day.at(slConfigDic["time"]["leg1"]["starttime"]).do(sellStraddle)
schedule.every().day.at(slConfigDic["time"]["leg1"]["sltime"]).do(setSLOrders,leg="leg1")
schedule.every().day.at(slConfigDic["time"]["leg1"]["exittime"]).do(exitStraddle)
schedule.every().day.at(slConfigDic["time"]["leg2"]["starttime"]).do(sellStraddle)
schedule.every().day.at(slConfigDic["time"]["leg2"]["sltime"]).do(setSLOrders,leg="leg2")
schedule.every().day.at(slConfigDic["time"]["leg2"]["exittime"]).do(exitStraddle)
schedule.every().day.at(slConfigDic["time"]["leg3"]["starttime"]).do(sellStraddle)
schedule.every().day.at(slConfigDic["time"]["leg3"]["sltime"]).do(setSLOrders,leg="leg3")
schedule.every().day.at(slConfigDic["time"]["leg3"]["exittime"]).do(exitStraddle)
#schedule.every().day.at("03:24").do(exitHedge)
schedule.every().day.at("09:30").do(checkStatus)

#now = datetime.now()
#startTime = now.replace(hour=19, minute=7, second=0)
#endTime = now.replace(hour=23, minute=59,second=59)
#if(datetime.now() > startTime and datetime.now() < endTime):

while True:
    #while (datetime.now() > startTime and datetime.now() < endTime):
    schedule.run_pending()
    time.sleep(1)




