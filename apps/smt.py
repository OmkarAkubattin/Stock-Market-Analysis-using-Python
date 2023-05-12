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
    def __init__(self,Symbol="SBIN.NS",period="1mo",intervaltime="1d",stocprice=False):
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
            self.stock['Month']=self.stock["Date"].dt.month
            self.stock['Year']=self.stock["Date"].dt.year
            self.stock['Day']=self.stock["Date"].dt.day

        
    def watchlist(self,watchlist):
        stocksdata={}
        for x in range(len(watchlist)):
            self.__init__(watchlist[x],period="1d")
            stocksdata[self.getinfo.info["underlyingSymbol"]] = {'Close':round(self.getinfo.info["previousClose"],2),'Change':round(self.getinfo.info["previousClose"]-self.getinfo.info["open"],2),'Change%':round(self.getinfo.info["previousClose"]/self.getinfo.info["open"],2)}
        return stocksdata

    def get_fig(self,chartname="Candlestick",day=30):
        if chartname=="Candlestick":
            fig = go.Figure(data=[go.Candlestick(x=pd.to_datetime(self.stock["Date"][self.stock["Date"].size-day:],format='%d%m%Y'),open=self.stock["Open"][self.stock["Open"].size-day:],high=self.stock["High"][self.stock["High"].size-day:],low=self.stock["Low"][self.stock["Low"].size-day:],close=self.stock["Close"][self.stock["Close"].size-day:])])
        elif chartname=="Line":
            fig = go.Figure(data=[go.Line(y=self.stock["Open"][self.stock["Open"].size-day:],x=pd.to_datetime(self.stock["Date"][self.stock["Date"].size-day:],format='%d%m%Y'),name='Close',fill='tonexty')])#fill='tonexty'
            # fig.add_trace(go.Line(y=self.stock["High"],x=pd.to_datetime(self.stock["Date"],format='%d%m%Y'),name='High'))
            # fig.add_trace(go.Line(y=self.stock["Low"],x=pd.to_datetime(self.stock["Date"],format='%d%m%Y'),name='Low'))
            # fig.add_trace(go.Line(y=self.stock["Close"],x=pd.to_datetime(self.stock["Date"],format='%d%m%Y'),name='Close',fill='tonexty'))
        fig.update_layout(xaxis_rangeslider_visible=False,yaxis_title="Price",xaxis_title="Date",autosize=True,margin=dict(l=20, r=20, t=20, b=20),)#title='Overview',width=500,height=500)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    def Moving_avg(self,day=30):
        self.stock['MA50'] = self.stock['Open'].rolling(50).mean()
        self.stock['MA100'] = self.stock['Open'].rolling(100).mean()
        self.stock['MA200'] = self.stock['Open'].rolling(200).mean()
        fig = go.Figure(data=[go.Line(y=self.stock["MA50"][self.stock["MA50"].size-day:],x=pd.to_datetime(self.stock["Date"][self.stock["Date"].size-day:],format='%d%m%Y'),name='MA50')])#fill='tonexty'
        fig.add_trace(go.Candlestick(x=pd.to_datetime(self.stock["Date"][self.stock["Date"].size-day:],format='%d%m%Y'),open=self.stock["Open"][self.stock["Open"].size-day:],high=self.stock["High"][self.stock["High"].size-day:],low=self.stock["Low"][self.stock["Low"].size-day:],close=self.stock["Close"][self.stock["Close"].size-day:],name=self.getinfo.info["underlyingSymbol"]))
        fig.add_trace(go.Line(y=self.stock["MA200"][self.stock["MA200"].size-day:],x=pd.to_datetime(self.stock["Date"][self.stock["Date"].size-day:],format='%d%m%Y'),name='MA200'))
        fig.add_trace(go.Line(y=self.stock["MA100"][self.stock["MA100"].size-day:],x=pd.to_datetime(self.stock["Date"][self.stock["Date"].size-day:],format='%d%m%Y'),name='MA100'))
        fig.update_layout(xaxis_rangeslider_visible=False,yaxis_title="Price",xaxis_title="Date",autosize=True,margin=dict(l=20, r=20, t=20, b=20),)#title='Overview',width=500,height=500)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def Profit_Loss_Roi(self,stockname,result,roi,boolroi=False):
        if(boolroi):
            fig = go.Figure(data=[go.Bar(y=roi,x=stockname)])#fill='tonexty'
        else:
            fig = go.Figure(data=[go.Bar(y=result,x=stockname)])#fill='tonexty'
        fig.update_layout(xaxis_rangeslider_visible=False,yaxis_title="Price",xaxis_title="Date",autosize=True,margin=dict(l=20, r=20, t=20, b=20),)#title='Overview',width=500,height=500)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

