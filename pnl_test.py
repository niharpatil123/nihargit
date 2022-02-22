def checkPNL(self):
        positionList = self.KiteConn.positions()
        totalPnl = 0
        postionPNL = 0
        hedgePNL = 0
        realizedPNL = 0
        for i in positionList['net']:
            tradeSymbol = 'NFO:' + i['tradingsymbol']
            ohlc = self.KiteConn.ohlc(tradeSymbol)
            lastPrice = ohlc[tradeSymbol]['last_price']
            print(lastPrice)
            if (i['quantity'] < 0):
                postionPNL = postionPNL +  (i['sell_value'] - i['buy_value']) + (i['quantity'] * lastPrice * i['multiplier']) 
            elif (i['quantity'] > 0):
                hedgePNL = hedgePNL + (i['sell_value'] - i['buy_value']) + (i['quantity'] * lastPrice * i['multiplier']) 
            elif (i['quantity'] == 0):
                realizedPNL = realizedPNL + (i['sell_value'] - i['buy_value']) + (i['quantity'] * lastPrice * i['multiplier']) 
                # print (realizedPNL)
        totalPnl = round(postionPNL + hedgePNL + realizedPNL)
        print(totalPnl)
        self.sendTelegram("Net Profit: \\" + str(int(totalPnl)))
        # return totalPnl
