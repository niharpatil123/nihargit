def getPnl():
    positionList = KiteConn.positions()
    # print(positionList)
    
    # pprint(positionList)
    # file = open("orders/3legActivePositions.json","r")
    # positionList = json.load(file)
    totalPnl = 0
    postionPNL = 0
    hedgePNL = 0
    realizedPNL = 0
    for i in positionList['net']:
        # print(i['tradingsymbol'], ":::", i['quantity'],":::",i['last_price'],":::",i['sell_price'],":::",i['buy_price'])
        if (i['quantity'] < 0):
            postionPNL = postionPNL +  (i['sell_value'] - i['buy_value']) + (i['quantity'] * i['last_price'] * i['multiplier']) 
            # print(sellpnl)
        elif (i['quantity'] > 0):
            hedgePNL = hedgePNL + (i['sell_value'] - i['buy_value']) + (i['quantity'] * i['last_price'] * i['multiplier']) 
            # print(buypnl)
        elif (i['quantity'] == 0):
            # realizedPNL = realizedPNL + (i['sell_price'] - i['buy_price']) * i['sell_quantity']
            realizedPNL = realizedPNL + (i['sell_value'] - i['buy_value']) + (i['quantity'] * i['last_price'] * i['multiplier']) 
            # print (realizedPNL)
            # print(round(closepnl))
    totalPnl = postionPNL + hedgePNL + realizedPNL
    print(round(totalPnl))
    # return toalPnl
