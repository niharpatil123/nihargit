from kiteconnect import KiteConnect
import undetected_chromedriver as uc
import logging
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time, pyotp

class AccessInitiator:

    def __init__(self):
        #f = open("config.json", "r"); jsonconfig = f.read(); f.close()
        #brokerconfig = json.loads(jsonconfig)
        self.api_key = 'xyipj2fx4akxggck'
        self.api_secret = 'ehzimap1bmhdbmrg2jbysn6jddxmmfr4'
        self.accessToken = ""
        self.reqToken = ""
        self.userName = 'RN2607'
        self.userPassword = 'Rupali@11'
        self.securityPin = '110278'
        self.url = 'https://kite.trade/connect/login?api_key=xyipj2fx4akxggck&v=3'
        self.totpKey = 'JDNQXHY4GZIB3RVCG6P7CDYURGQZ54PM'
        #self.chromedriverpath = brokerconfig['chromedriverpath']
        self.kiteConn = ""

    def getAccessToken(self):
        #api_key = 'xyipj2fx4akxggck'
        #api_secret = 'ehzimap1bmhdbmrg2jbysn6jddxmmfr4'
        #url='https://kite.trade/connect/login?api_key=xyipj2fx4akxggck&v=3'
        #root_uri = "https://api.kite.trade"
        #login_uri = "https://kite.trade/connect/login"
        #userName = 'RN2607'
        #userPassword = 'Rupali@11'
        #securityPin = '110278'
        #totpKey = 'JDNQXHY4GZIB3RVCG6P7CDYURGQZ54PM'

        print("Get Access Token")
        driver = uc.Chrome()
        driver.get("https://kite.trade/connect/login?api_key=xyipj2fx4akxggck&v=3")
        login_id = WebDriverWait(driver,10).until(lambda x: x.find_element(By.XPATH,'//*[@id="userid"]'))
        login_id.send_keys(self.userName)

        pwd = WebDriverWait(driver,10).until(lambda x: x.find_element(By.XPATH,'//*[@id="password"]'))
        pwd.send_keys(self.userPassword)

        submit = WebDriverWait(driver,10).until(lambda x: x.find_element(By.XPATH,'//*[@id="container"]/div/div/div[2]/form/div[4]/button'))
        submit.click()

        authkey = pyotp.TOTP(self.totpKey)
        print(authkey.now())

        totp = WebDriverWait(driver,10).until(lambda x: x.find_element(By.XPATH,'//*[@id="totp"]'))
        totp.send_keys(authkey.now())

        submit2 = WebDriverWait(driver,10).until(lambda x: x.find_element(By.XPATH,'//*[@id="container"]/div/div/div/form/div[3]/button'))
        submit2.click()
        print("Submitted......")
        time.sleep(5)
        rdirUrl = driver.current_url
        print(rdirUrl)

        self.reqToken = rdirUrl.split('request_token=')[1].split('&')[0]

        print(self.reqToken)
        driver.close()
        self.kiteConn = KiteConnect(api_key = self.api_key)
        dataObj = self.kiteConn.generate_session(request_token=self.reqToken,api_secret=self.api_secret)

        print(dataObj['access_token'])

        self.accessToken = self.kiteConn.set_access_token(dataObj['access_token'])
        #kiteConn.holdings()
        #print(kiteConn.holdings())
        print("Get Token Completed Successfully")

#ai = AccessInitiator()
#ai.getAccessToken()