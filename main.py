import sys, schedule, time, json
from datetime import datetime
from common.functions import functions
from systems.threeLeg.threeLegSystem import threeleg
from systems.delta.deltaNeutralSystem import deltaNeutral
from common.broker.zerodha_login import login
from kiteconnect import KiteConnect
from common.login import login


class main:
    
    def __init__(self):
        self.file = sys.argv[0]
        self.user = sys.argv[1]
        self.system = sys.argv[2]
        
        self.tradeSymbol = 'BANKNIFTY'
        self.positionSize = '10'

        print(f'CMD: {self.file} {self.user} {self.system}')
        lg = login(self.user)
        f = open(f'common/orders/accessToken.json', "r")
        jsonconfig = f.read()
        f.close()
        at = json.loads(jsonconfig)
        self.accessToken = at['accessToken']['at']
        self.accessTokenDate = at['accessToken']['dt']

        if self.accessTokenDate == str(datetime.now().date()):
            print('Access Token is available. skip login!')
            self.accessToken = self.accessToken
        else: 
            self.accessToken = lg.getAccessToken()

        apiKey = lg.api_key
        self.KiteConn = KiteConnect(api_key = apiKey)
        self.KiteConn.set_access_token(self.accessToken)

        self.fn = functions(self.KiteConn, self.tradeSymbol, self.positionSize, self.system, self.user)
        
        self.sy = threeleg(self.KiteConn, self.tradeSymbol, self.positionSize, self.system, self.user)
        self.dn = deltaNeutral(self.KiteConn, self.tradeSymbol, self.positionSize, self.system, self.user)
       


    def startTrading(self):
        if self.system == '3leg':
            print ('3 leg system selected')
            self.fn.sendTelegram("Three Leg System Initiated")
            self.sy.scheduler()
            #while True:
                #schedule.run_pending()
                #time.sleep(1)
        elif self.system == 'delta':
            print ('delta system selected')
            self.fn.sendTelegram("Delta System Initiated")
            self.dn.scheduler()
            #while True:
                #schedule.run_pending()
                #time.sleep(1)

mn = main()
mn.startTrading()



