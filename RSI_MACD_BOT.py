

import time
import datetime as DT
from binance.client import Client
from binance.enums import *
import pandas as pd
import numpy as np

def computeRSI (data, time_window):
    diff = np.diff(data)
    up_chg = 0 * diff
    down_chg = 0 * diff
    
   
    up_chg[diff > 0] = diff[ diff>0 ]
    
    
    down_chg[diff < 0] = diff[ diff < 0 ]

    up_chg = pd.DataFrame(up_chg)
    down_chg = pd.DataFrame(down_chg)
    
    up_chg_avg   = up_chg.ewm(com=time_window-1 , min_periods=time_window).mean()
    down_chg_avg = down_chg.ewm(com=time_window-1 , min_periods=time_window).mean()
    
    rs = abs(up_chg_avg/down_chg_avg)
    rsi = 100 - 100/(1+rs)
    rsi = int(rsi[0].iloc[-1])
    return rsi


def MACD():
    klines2 = client.get_klines(symbol=tradePair, interval='5m', limit='60')
    closeVal = [float(entry[4]) for entry in klines2]
    closeVal = pd.DataFrame(closeVal)
    ema12 = closeVal.ewm(span=12).mean()
    ema26 = closeVal.ewm(span=26).mean()
    macd = ema26 - ema12
    signal = macd.ewm(span=9).mean()

    macd = macd.values.tolist()
    signal = signal.values.tolist()
    
    if macd[-1] > signal[-1] and macd[-2] < signal[-2]:
        macdIndicator = 'BUY'
    elif macd[-1] < signal[-1] and macd[-2] > signal[-2]:
        macdIndicator = 'SELL'
    else:
        macdIndicator = 'HOLD'

    return macdIndicator


def stopLoss():
    today = DT.date.today()
    week_ago = today - DT.timedelta(days=6)
    week_ago = week_ago.strftime('%d %b, %Y')
    klines2 = client.get_historical_klines(tradePair, Client.KLINE_INTERVAL_1DAY, str(week_ago))
    highVal = [float(entry[2]) for entry in klines2]
    lowVal = [float(entry[3]) for entry in klines2]
    closeVal = [float(entry[4]) for entry in klines2]
    avgDownDrop = (sum(highVal)/len(highVal)-sum(lowVal)/len(lowVal))/(sum(closeVal)/len(closeVal))
    stopVal = closeVal[-2]*(1-avgDownDrop)
    return stopVal

api_key = ''
api_secret = ''

trdPair1 = 'BNB'
trdPair2 = 'USDT'
winRate = 1.02
client = Client(api_key, api_secret)

print('___DATE______TIME_____BALANCE___RSI__MACD___PRICE______STRATEGY___TARGET-PRICE__')

while True:
    try:
       
        tradePair = trdPair1 + trdPair2
        price = client.get_ticker(symbol=tradePair)
        sigNum = len(str(int(float(price['askPrice']))))
        sigNumOfCoin = '.' + str(len(str(int(float(price['askPrice']))))) + 'f'
        btcCount = client.get_asset_balance(asset = trdPair1)
        btcCount = float(btcCount['free'])*float(price['askPrice'])
        busdCount = client.get_asset_balance(asset = trdPair2)
        busdCount = float(busdCount['free'])

        
        if btcCount > busdCount:
            lastrade = trdPair1
        elif btcCount < busdCount:
            lastrade = trdPair2

        
        trades = client.get_my_trades(symbol=tradePair)
        trades = trades[len(trades)-1]
        lasprice = float(trades['price'])
        
        klines = client.get_klines(symbol=tradePair, interval='5m', limit='500')
        klines2 = client.get_historical_klines(tradePair, Client.KLINE_INTERVAL_1DAY, "1 day ago UTC")
        close = [float(entry[4]) for entry in klines]
        close_array = np.asarray(close)
        close_finished = close_array[:-1]

        
        rsi = computeRSI (close_finished, 14)
        
        
        coitime = client.get_server_time()
        coitime = time.strftime('%m/%d/%Y %H:%M:%S',
                                time.gmtime(coitime['serverTime']/1000.))

        
         
        if lastrade == trdPair1:
            balance = client.get_asset_balance(asset = trdPair1)
            coiNumber = format(float(balance['free']) - 5*10**-sigNum, sigNumOfCoin) 
            coiprice = format(float(price['askPrice']), '.4f')
            if (float(coiprice) > float(lasprice) * winRate) and (rsi > 70 or MACD() == 'SELL'):
                stat = 'sell'
                            
                order = client.order_limit_sell(
                    symbol=tradePair,
                    quantity= float(coiNumber),
                    price= coiprice)
                
                lastrade = trdPair2
                lasprice = coiprice
                prntInfo = coitime + ' ' + 'SELL:' + ' ' + coiprice + ' ' + 'Balance:' + ' ' + balance['free']
               
            elif float(coiprice) < stopLoss():
                stat = 'STOPLOSS'
                order = client.order_limit_sell(
                    symbol=tradePair,
                    quantity= float(coiNumber),
                    price= coiprice)

                lastrade = trdPair2
                lasprice = coiprice
                prntInfo = coitime + ' ' + 'StopLoss :((( :' + ' ' + coiprice + ' ' + 'Balance:' + ' ' + balance['free']
                
            else:
                stat = 'hold' + trdPair1 + '  ' + str(lasprice*winRate)


           
        elif lastrade == trdPair2:
            balance = client.get_asset_balance(asset = trdPair2)
            coiNumber = float(balance['free'])
            coiprice = format(float(price['askPrice']), '.4f')
            test = format(float(coiNumber)/float(coiprice) - 5*10**-sigNum, sigNumOfCoin)
            if (float(coiprice) * winRate < float(lasprice)) and (MACD() == 'BUY' or rsi < 30):
                stat = 'buy'
                
                order = client.order_limit_buy(
                    symbol=tradePair,
                    quantity=test,
                    price= coiprice)
                
                lastrade = trdPair1
                lasprice = coiprice
                prntInfo = coitime + ' ' + 'BUY:' + ' ' + coiprice + ' ' + 'Balance:' + ' ' + balance['free']
                
            else:
                stat = 'hold' + trdPair2 + '  ' + str(lasprice/winRate)

        
        print(coitime + ' ' + balance['free'] + '  ' + str(rsi) + '  ' + MACD()
              + '  ' + price['askPrice'] + ' ' + stat)
    except:
        print(coitime + ' ' + 'an error occured & retrying now')
    
    time.sleep(10)
