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

def getDeltaDataFrame(optionType):
    print("GenerateDataFrameFor:::",optionType)
    bnSpot = calG.getSpot(conn)
    bnStrike = calG.setSellStrike(bnSpot)
    data = {
        "strikes": [bnStrike,bnStrike+100,bnStrike+200,bnStrike+300,bnStrike+400,bnStrike+500,bnStrike+600,bnStrike+700,bnStrike-100,bnStrike-200,bnStrike-300,bnStrike-400,bnStrike-500,bnStrike-600,bnStrike-700],
        "delta": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    }
    #load data into a DataFrame object:
    df = pd.DataFrame(data)
    #print(df)
    for index,row in df.iterrows():
        #print("Strike: ", row['strikes'])
        strike = row['strikes']
        position = "NFO:BANKNIFTY" + nextExpiryDate() + str(strike) + optionType
        if (optionType=="CE"):
            delta = calG.getCallDelta(conn,position,strike)
        elif (optionType=="PE"):
            delta = calG.getPutDelta(conn, position, strike)
        df.at[index, 'delta'] = abs(delta*1000)
    print(df)
    return df

def getMatchingStrike(df, input_value):
    deltaList = df['delta']
    difference = lambda deltaList: abs(deltaList - input_value)
    nearestDelta = min(deltaList, key=difference)
    matchingStrike = df.loc[df['delta'] == nearestDelta, 'strikes'].iloc[0]
    return int(matchingStrike)

def setActivePositions(positionDict):
    #This code writes active positions into JSON File on every trade order
    json_object = json.dumps(positionDict)
    with open("F:\\PycharmProject\\activePositions.json", "w") as outfile:
        outfile.write(json_object)

def getActivePositions():
    #This code reads the positions from JSON File on every 5minutes
    file = open("F:\\PycharmProject\\activePositions.json","r")
    positionList = json.load(file)
    #print(positionList)
    #print(positionList['hedgeOrder']['callSymbol'])
    return positionList

def exitHedge():
    print("===============Exit Hedge===============")
    positionList = conn.positions()
    #file = open("F:\\PycharmProject\\position2.json","r")
    #positionList = json.load(file)
    for i in positionList['day']:
        if (i['quantity'] > 0 ):
            placeSellOrder(conn, i['tradingsymbol'])

def exitStraddle():
    print("======================Exit Straddle========================")
    positionList = conn.positions()
    #file = open("F:\\PycharmProject\\position2.json","r")
    #positionList = json.load(file)
    for i in positionList['day']:
        print(i['tradingsymbol'],"::::",i['quantity'])
        if(i['quantity'] < 0 ):
            placeBuyOrder(conn, i['tradingsymbol'])

def exitAllPositions():
    print("====================Exit All Positions===========================")
    positionList = conn.positions()
    #file = open("F:\\PycharmProject\\position2.json","r")
    #positionList = json.load(file)
    for i in positionList['day']:
        print(i['tradingsymbol'],"::::",i['quantity'])
        if(i['quantity'] < 0 ):
            placeBuyOrder(conn, i['tradingsymbol'])
        elif (i['quantity'] > 0 ):
            placeSellOrder(conn, i['tradingsymbol'])

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
    placeSellOrder(conn, callPosition[4:])
    placeSellOrder(conn, putPosition[4:])
    print("Staddle Order Placed")
    positionDict = getActivePositions()
    positionDict["straddleOrder"]["callSymbol"] = callPosition[4:]
    positionDict["straddleOrder"]["putSymbol"] = putPosition[4:]
    positionDict["straddleOrder"]["callStrike"] = strikePrice
    positionDict["straddleOrder"]["putStrike"] = strikePrice
    setActivePositions(positionDict)
    print(positionDict)
    tm.telegram_sendmsg("Straddle order placed::"+str(int(strikePrice)), "0")

def exitOneLeg(conn,tradeSymbol):
    print("Exit One Leg: ",tradeSymbol)
    placeBuyOrder(conn, tradeSymbol)
    #order = conn.place_order()
    #cover sell position
    #cover hedge position

def enterNewLeg(conn,exitType,existingdelta):
    print("Enter New Leg: ",exitType,"##",existingdelta)
    bnSpot = calG.getSpot(conn)
    positionDict = getActivePositions()
    print(positionDict)
    #order = conn.place_order()
    #buy Hedge
    #Sell one leg
    if (exitType == "CE"):
        df = getDeltaDataFrame("CE")
        newStrike = getMatchingStrike(df, existingdelta)
        print("New Strike: ", newStrike)
        callPosition = "NFO:BANKNIFTY" + nextExpiryDate() + str(newStrike) + "CE"
        #Place Order for new CALL
        placeSellOrder(conn, callPosition[4:])
        #Update Dictionary
        positionDict["straddleOrder"]["callSymbol"]= callPosition[4:]
        positionDict["straddleOrder"]["callStrike"] = newStrike
        tm.telegram_sendmsg("New Leg Entered:: " + callPosition + " : " + str(int(newStrike)), "0")

    elif (exitType == "PE"):
        df = getDeltaDataFrame("PE")
        newStrike = getMatchingStrike(df, existingdelta)
        print("New Strike: ", newStrike)
        putPosition = "NFO:BANKNIFTY" + nextExpiryDate() + str(newStrike) + "PE"
        # Place Order for new PUT
        placeSellOrder(conn, putPosition[4:])
        #Update Dictionary
        positionDict["straddleOrder"]["putSymbol"] = putPosition[4:]
        positionDict["straddleOrder"]["putStrike"] = newStrike
        tm.telegram_sendmsg("New Leg Entered:: " + putPosition + " : " + str(int(newStrike)), "0")

    print(positionDict)
    setActivePositions(positionDict)

def getPNL():
    margin = conn.margins()
    realised = margin['equity']['utilised']['m2m_realised']
    unrealised = margin['equity']['utilised']['m2m_unrealised']
    total = realised + unrealised
    return total

def getPNL2():
    positionList = conn.positions()
    pnl = 0
    for i in positionList['day']:
        pnl = pnl + i['pnl']
    return pnl

def checkPNL(maxProfit,trailingSL):

    minProfit = trailSLConfig["minProfit"]
    maxProfit = trailSLConfig["maxProfit"]
    trailingSL = trailSLConfig["trailingSL"]
    #Check if profit now is max of the day
    totalPNL=getPNL2()
    print("Total PNL:",totalPNL," maxProfit: ",maxProfit,"  Trailing SL: ",trailingSL)
    if(totalPNL > maxProfit):
        maxProfit = totalPNL
    tm.telegram_sendmsg("Net Profit::: \\" + str(int(totalPNL)) + "Max Profit::: \\" + str(int(maxProfit)), "0")
    #if profit reaches a target, trail SL
    if (maxProfit > minProfit):
        trailingSL = 0

    trailSLConfig["maxProfit"] = maxProfit
    trailSLConfig["trailingSL"] = trailingSL

    if(totalPNL < trailingSL):
        #exitAllPositions()
        print("Exit All Positions")
        quit()

    if(totalPNL > 25000):
        #exitAllPositions()
        print("Exit All Positions")
        quit()

def placeBuyOrder(conn,tradeSymbol):
    order = conn.place_order(tradingsymbol=tradeSymbol, quantity=150, exchange=conn.EXCHANGE_NFO,order_type=conn.ORDER_TYPE_MARKET,
                             transaction_type=conn.TRANSACTION_TYPE_BUY,product=conn.PRODUCT_MIS,variety=conn.VARIETY_REGULAR)
    print("Buy Order Successfully Placed for::::",tradeSymbol)

def placeSellOrder(conn,tradeSymbol):
    order = conn.place_order(tradingsymbol=tradeSymbol, quantity=150, exchange=conn.EXCHANGE_NFO,order_type=conn.ORDER_TYPE_MARKET,
                             transaction_type=conn.TRANSACTION_TYPE_SELL,product=conn.PRODUCT_MIS,variety=conn.VARIETY_REGULAR)
    print("Sell Order Successfully Placed for::::",tradeSymbol)

def checkIn5Mins():
    print("========================Inside check delta each 5 mins==========================")
    startTime= datetime.now()
    timeNow = str(datetime.now().hour) + ":" + str(datetime.now().minute) + ":" + str(datetime.now().second)
    print("Time: ", timeNow)
    #get Open Positions.
    #CallPosition = "NFO:BANKNIFTY2220337600CE"
    #PutPosition = "NFO:BANKNIFTY2220337600PE"
    positionDict = getActivePositions()
    print(positionDict)
    CallPosition = "NFO:" + positionDict["straddleOrder"]["callSymbol"]
    PutPosition = "NFO:" + positionDict["straddleOrder"]["putSymbol"]
    #remove NFO: from symbol
    CallSymbol = positionDict["straddleOrder"]["callSymbol"]
    PutSymbol = positionDict["straddleOrder"]["putSymbol"]
    CallStrike = positionDict["straddleOrder"]["callStrike"]
    PutStrike = positionDict["straddleOrder"]["putStrike"]
    calG.getSpot(conn)
    #calG.setSellStrike()
    #Net Delta is commented as delta is individually calculated
    #netDelta = calG.getNetDelta(conn,CallPosition,CallStrike,PutPosition,PutStrike)
    callDelta = calG.getCallDelta(conn, CallPosition, CallStrike)
    putDelta = calG.getPutDelta(conn, PutPosition, PutStrike)
    callDeltaRound = callDelta*1000
    putDeltaRound = putDelta*1000
    print("Call Delta: ", callDeltaRound, "Put Delta: ", putDeltaRound)
    print("Net Delta:",callDeltaRound + putDeltaRound)
    totalPNL = getPNL2()
    tm.telegram_sendmsg("CallPosition:: " + str(CallStrike) + " : \\" + str(int(callDeltaRound)) + " ::::PutPosition:: " + str(PutStrike) + " : \\" + str(int(putDeltaRound)), "0")
    tm.telegram_sendmsg("Net Delta:: \\" + str(int(callDeltaRound + putDeltaRound)), "0")
    #tm.telegram_sendmsg("Net Profit::: \\" + str(int(totalPNL)), "0")
    callPosStatus = True
    putPosStatus = True
    if (abs(callDeltaRound + putDeltaRound) > 200):
        print("Delta Mismatch")
        tm.telegram_sendmsg("Delta Mismatch:: ", "0")
        if (abs(callDeltaRound) > 700):
            # exit CALL
            print("-------------Call Delta more than 700----------")
            exitOneLeg(conn, CallSymbol)
            callPosStatus = False
        elif (abs(putDeltaRound) > 700):
            # exit PUT
            print("-------------Put Delta more than 700----------")
            exitOneLeg(conn, PutSymbol)
            putPosStatus = False
        elif (abs(callDeltaRound) < 400):
            # exit CALL
            print("-------------Call Delta less than 400----------")
            exitOneLeg(conn, CallSymbol)
            callPosStatus = False
        elif (abs(putDeltaRound) < 400):
            # exit PUT
            print("-------------Put Delta less than 400----------")
            exitOneLeg(conn, PutSymbol)
            putPosStatus = False

        elif (abs(callDeltaRound) > 450 and abs(callDeltaRound) < 650):
            # exit PUT
            print("-------------Call Delta between 450 & 650----------")
            exitOneLeg(conn, PutSymbol)
            putPosStatus = False

        elif (abs(putDeltaRound) > 450 and abs(putDeltaRound) < 650):
            # exit CALL
            print("-------------Put Delta between 450 & 650----------")
            exitOneLeg(conn, CallSymbol)
            callPosStatus = False

        elif (abs(callDeltaRound) > 650 and abs(callDeltaRound) < 700):
            # Condition for 650to 700...PENDING
            print("-------------Call Delta between 650 and 700----------")
            exitOneLeg(conn, CallSymbol)
            callPosStatus = False

        elif (abs(putDeltaRound) > 650 and abs(putDeltaRound) < 700):
            # Condition for 650to 700...PENDING
            print("-------------Put Delta between 650 and 700----------")
            exitOneLeg(conn, PutSymbol)
            putPosStatus = False

    #=================EXIT operations completed==========================
    if (callPosStatus == False and putPosStatus == False):
        #enterFreshHedge(conn)
        sellStraddle(conn)
    if (callPosStatus == False and putPosStatus == True):
        # find equivalent Call Option
        enterNewLeg(conn,"CE",abs(putDeltaRound))
    if (callPosStatus == True and putPosStatus == False):
        # find equivalent Put Option
        enterNewLeg(conn,"PE",abs(callDeltaRound))

    endTime = datetime.now()
    print("Check Every 5 Minutes Completed::::",endTime-startTime)

def checkDelta():
    schedule.every(5).minutes.do(checkIn5Mins)
    #schedule.every(1).minutes.do(checkPNL)

#==========================Main Starts here==============================
ai = AccessInitiator()
#accessToken = ai.getAccessToken()
accessToken = "qH2YZXHdh2luFqC6D2VWI3e07pVxA5cb"
print(accessToken)
api_key = ai.api_key
print(api_key)

conn = KiteConnect(api_key=api_key)
conn.set_access_token(accessToken)
print("Start Time: ",datetime.now().hour,":",datetime.now().minute,":",datetime.now().second)
calG = CalculateGreeks(conn)
tm = TelegramMessenger()
#Initialize the dictionaties
#hedgeOrder = {"callSymbol":0,"callStrike":0,"callPrice":0,"putSymbol":0,"putStrike":0,"putPrice":0}
#straddleOrder = {"callSymbol":0,"callStrike":0,"callPrice":0,"putSymbol":0,"putStrike":0,"putPrice":0}
positionDict = {'hedgeOrder': {'callSymbol': 0, 'callStrike': 0, 'callPrice': 0, 'putSymbol': 0, 'putStrike': 0, 'putPrice': 0}, 'straddleOrder': {'callSymbol': 0, 'callStrike': 0, 'callPrice': 0, 'putSymbol': 0, 'putStrike': 0, 'putPrice': 0}}
trailSLConfig = {'minProfit':10000,'trailingSL':-20000,'maxProfit':0,'maxTarget':20000}

schedule.every().day.at("09:17").do(buyHedge)
schedule.every().day.at("09:29").do(sellStraddle)
schedule.every().day.at("09:30").do(checkDelta)
schedule.every().day.at("15:24:30").do(exitStraddle)
schedule.every().day.at("15:24:40").do(exitHedge)

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
