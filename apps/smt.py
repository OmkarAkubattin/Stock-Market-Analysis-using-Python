import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly
import json
from datetime import date
import yfinance as yf
import time

class Stocks:
    def __init__(self,Symbol="SBIN.NS",period="1mo",intervaltime="1d",stocprice=False):
        self.getinfo = yf.Ticker(Symbol)
        if stocprice:
            self.stock = self.getinfo.history(period=period,interval=intervaltime)
            # self.stock=self.stock.round(decimals=2)
            self.stock.reset_index(drop = False, inplace = True)
            self.stock["Date"]=pd.to_datetime(self.stock["Date"],format='%d%m%Y')
            self.stock=self.stock.drop(['Dividends','Stock Splits'], axis=1)
            self.stock["Change"]=self.stock["Close"]-self.stock["Open"]
            self.stock["Change%"]=self.stock["Close"]/self.stock["Open"]
            # self.stock['Month']=self.stock["Date"].dt.month
            # self.stock['Year']=self.stock["Date"].dt.year
            # self.stock['Day']=self.stock["Date"].dt.day
        
    def watchlist(self,watchlist):
        stocksdata={}
        for x in range(len(watchlist)):
            self.__init__(watchlist[x],period="1d")
            stocksdata[self.getinfo.info["underlyingSymbol"]] = {'Close':round(self.getinfo.info["previousClose"],2),'Change':round(self.getinfo.info["previousClose"]-self.getinfo.info["open"],2),'Change%':round(self.getinfo.info["previousClose"]/self.getinfo.info["open"],2)}
        return stocksdata

    def get_fig(self,chartname="Candlestick"):
        if chartname=="Candlestick":
            fig = go.Figure(data=[go.Candlestick(x=pd.to_datetime(self.stock["Date"],format='%d%m%Y'),open=self.stock['Open'],high=self.stock['High'],low=self.stock['Low'],close=self.stock['Close'])])
        elif chartname=="Line":
            fig = go.Figure(data=[go.Line(y=self.stock["Open"],x=pd.to_datetime(self.stock["Date"],format='%d%m%Y'),name='Open')])#fill='tonexty'
            fig.add_trace(go.Line(y=self.stock["High"],x=pd.to_datetime(self.stock["Date"],format='%d%m%Y'),name='High'))
            fig.add_trace(go.Line(y=self.stock["Low"],x=pd.to_datetime(self.stock["Date"],format='%d%m%Y'),name='Low'))
            fig.add_trace(go.Line(y=self.stock["Close"],x=pd.to_datetime(self.stock["Date"],format='%d%m%Y'),name='Close'))
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
        fig.update_layout(xaxis_rangeslider_visible=False,yaxis_title="Price",xaxis_title="Date",autosize=True)#title='Overview',width=500,height=500)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)