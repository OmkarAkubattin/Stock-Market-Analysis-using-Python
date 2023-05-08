import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly
import json
from datetime import date
import yfinance as yf
import time
from scipy.stats import ttest_ind

class Stocks:
    def __init__(self,Symbol="SBIN.NS",period="1mo",intervaltime="1d",stocprice=False,moving_avg=False):
        self.getinfo = yf.Ticker(Symbol)
        n_forward = 5
        if stocprice:
            self.stock = self.getinfo.history(period=period,interval=intervaltime)
            # self.stock=self.stock.round(decimals=2)
            self.stock.reset_index(drop = False, inplace = True)
            self.stock["Date"]=pd.to_datetime(self.stock["Date"],format='%d%m%Y')
            # self.stock=self.stock.drop(['Dividends','Stock Splits'], axis=1)
            self.stock["Change"]=self.stock["Close"]-self.stock["Open"]
            self.stock["Change%"]=self.stock["Close"]/self.stock["Open"]
            # self.stock['Month']=self.stock["Date"].dt.month
            # self.stock['Year']=self.stock["Date"].dt.year
            # self.stock['Day']=self.stock["Date"].dt.day
        if moving_avg:
            self.stock['Forward Close'] = self.stock['Close'].shift(-n_forward) # Close 5 days ago
            self.stock['Forward Return'] = (self.stock['Forward Close'] - self.stock['Close'])/self.stock['Close']
            result = []
            train_size = 0.6
            for sma_length in range(20, 500):
                self.stock['SMA'] = self.stock['Close'].rolling(sma_length).mean() 
                self.stock['input'] = [int(x) for x in self.stock['Close'] > self.stock['SMA']]
                
                df = self.stock.dropna()
                training = df.head(int(train_size * df.shape[0]))
                test = df.tail(int((1 - train_size) * df.shape[0]))
                
                tr_returns = training[training['input'] == 1]['Forward Return']
                test_returns = test[test['input'] == 1]['Forward Return']

                mean_forward_return_training = tr_returns.mean()
                mean_forward_return_test = test_returns.mean()

                pvalue = ttest_ind(tr_returns,test_returns,equal_var=False)[1]
                
                result.append({
                    'sma_length':sma_length,
                    'training_forward_return': mean_forward_return_training,
                    'test_forward_return': mean_forward_return_test,
                    'p-value':pvalue
                })

            # sort result object by training_forward_return
            result.sort(key = lambda x : -x['training_forward_return'])
            best_sma = result[0]['sma_length']
            self.stock['SMA'] = self.stock['Close'].rolling(best_sma).mean()

        
    def watchlist(self,watchlist):
        stocksdata={}
        for x in range(len(watchlist)):
            self.__init__(watchlist[x],period="1d")
            stocksdata[self.getinfo.info["underlyingSymbol"]] = {'Close':round(self.getinfo.info["previousClose"],2),'Change':round(self.getinfo.info["previousClose"]-self.getinfo.info["open"],2),'Change%':round(self.getinfo.info["previousClose"]/self.getinfo.info["open"],2)}
        return stocksdata

    def get_fig(self,chartname="Candlestick",context="Normal",day=30):
        if (chartname=="Candlestick" and (context=="Normal" or context=="Moving_avg") ):
            fig = go.Figure(data=[go.Candlestick(x=pd.to_datetime(self.stock["Date"][self.stock["Date"].size-day:],format='%d%m%Y'),open=self.stock["Open"][self.stock["Open"].size-day:],high=self.stock["High"][self.stock["High"].size-day:],low=self.stock["Low"][self.stock["Low"].size-day:],close=self.stock["Close"][self.stock["Close"].size-day:])])
        elif chartname=="Line" and context=="Normal":
            fig = go.Figure(data=[go.Line(y=self.stock["Open"][self.stock["Open"].size-day:],x=pd.to_datetime(self.stock["Date"][self.stock["Date"].size-day:],format='%d%m%Y'),name='Close',fill='tonexty')])#fill='tonexty'
            # fig.add_trace(go.Line(y=self.stock["High"],x=pd.to_datetime(self.stock["Date"],format='%d%m%Y'),name='High'))
            # fig.add_trace(go.Line(y=self.stock["Low"],x=pd.to_datetime(self.stock["Date"],format='%d%m%Y'),name='Low'))
            # fig.add_trace(go.Line(y=self.stock["Close"],x=pd.to_datetime(self.stock["Date"],format='%d%m%Y'),name='Close',fill='tonexty'))
        elif chartname=="Line" and context=="Moving_avg":
            fig = go.Figure(data=[go.Line(y=self.stock["SMA"][self.stock["SMA"].size-day:],x=pd.to_datetime(self.stock["Date"][self.stock["Date"].size-day:],format='%d%m%Y'),name='Close')])#fill='tonexty'
            fig.add_trace(go.Candlestick(x=pd.to_datetime(self.stock["Date"][self.stock["Date"].size-day:],format='%d%m%Y'),open=self.stock["Open"][self.stock["Open"].size-day:],high=self.stock["High"][self.stock["High"].size-day:],low=self.stock["Low"][self.stock["Low"].size-day:],close=self.stock["Close"][self.stock["Close"].size-day:]))

        elif chartname=="Donut":
            pass
        elif chartname=="Bar":
            pass
        elif chartname=="Histogram":
            pass
        elif chartname=="Ohlc":
            pass
        elif chartname=="Pie":
            pass
        fig.update_layout(xaxis_rangeslider_visible=False,yaxis_title="Price",xaxis_title="Date",autosize=True,margin=dict(l=20, r=20, t=20, b=20),)#title='Overview',width=500,height=500)
        # self.chartname = json.loads(jsondata)["data"][0]["type"].capitalize()
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    def char_get(self,chartname,data):
        if chartname=="Candlestick":
            pass
        elif chartname=="Line":
            pass
        elif chartname=="Donut":
            pass
        elif chartname=="Bar":
            pass
        elif chartname=="Histogram":
            pass
        elif chartname=="Ohlc":
            pass
        elif chartname=="Pie":
            fig = go.Figure(data=[go.Pie(labels=data["labels"], values=data["value"], hole=.3)])
        fig.update_layout(xaxis_rangeslider_visible=False,autosize=True,margin=dict(l=20, r=20, t=20, b=20),)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
