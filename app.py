from flask import Flask, render_template, redirect, request, session
from flask_session import Session
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
# from flask_mysqldb import MySQL
import hashlib
import yfinance as yf
import json
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly
import json
from datetime import datetime


graphJSON=''
fig=''
with open("config.json", "r") as c:
    params = json.load(c)["params"]
local_server = True

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']

db = SQLAlchemy(app)
class stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(30), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    lastprice = db.Column(db.String(20), nullable=False)
    industry = db.Column(db.String(30), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    exchange = db.Column(db.String(20), nullable=False)

class stock_data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    open = db.Column(db.Integer, nullable=False)
    high = db.Column(db.Integer, nullable=False)
    low = db.Column(db.Integer, nullable=False)
    close = db.Column(db.Integer, nullable=False)
    adj_close = db.Column(db.Integer, nullable=False)
    # fk_stock = db.Column(db.Integer, foreign_key=True)

class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    firstname = db.Column(db.String(30), nullable=False)
    lastname = db.Column(db.String(30), nullable=False)
    phone_no = db.Column(db.Integer, nullable=True)
    # user_role = db.Column(db.Integer, nullable=False)

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)
mail = Mail(app)

@app.route('/setup')
def setup():
    url="https://finance.yahoo.com/lookup/equity?s=india&t=A&b=0&c=601"
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}
    r = requests.get(url, headers=headers)
    content = r.content
    soup = BeautifulSoup(content,"lxml")
    Symbol = soup.find_all('td', attrs={'class':'data-col0'})
    Name = soup.find_all('td', attrs={'class':'data-col1'})
    Lastprice = soup.find_all('td', attrs={'class':'data-col2'})
    Industry = soup.find_all('td', attrs={'class':'data-col3'})
    Type = soup.find_all('td', attrs={'class':'data-col4'})
    Exchange = soup.find_all('td', attrs={'class':'data-col5'})
    i=0
    while(i<=len(Symbol)):
        stockinfo = stock(symbol=Symbol[i].text,
                            name=Name[i].text,
                            lastprice=Lastprice[i].text,
                            industry=Industry[i].text,
                            type=Type[i].text,
                            exchange=Exchange[i].text)
        db.session.add(stockinfo)
        db.session.commit()
        i=i+1
        if(i==len(Symbol)):
            return redirect("/")
    

@app.route('/', methods = ['GET','POST'])
def dashbord():
    if not session.get("emailid"):
            return redirect("/login")
    Symbol1="SBIN.NS"
    stockN1="SBIN.NS"
    getinfo1 = yf.Ticker(Symbol1)
    stock1=getinfo1.history(period="1mo")#interval="1d"
    if(request.method=='GET' and "SymbolName" in request.args):
        # return request.args
        stockN1=request.args.get("SymbolName")
        getinfo1 = yf.Ticker(request.args.get("SymbolName"))
        stock1=getinfo1.history(start=request.args.get("StartDate"),end=request.args.get("EndDate"),interval=request.args.get("Interval"))#interval="1d"
    stock1.reset_index(drop = False, inplace = True)
    stock1["Date"]=pd.to_datetime(stock1["Date"],format='%d%m%Y')
    # stock1=stock1.drop(['Dividends','Stock Splits'], axis=1)
    stock1['Month']=stock1["Date"].dt.month
    stock1['Year']=stock1["Date"].dt.year
    stock1['Day']=stock1["Date"].dt.day
    Candlestickfig = go.Figure(data=[go.Candlestick(x=pd.to_datetime(stock1["Date"],format='%d%m%Y'),open=stock1['Open'],high=stock1['High'],low=stock1['Low'],close=stock1['Close'])])
    Candlestickfig.update_layout(xaxis_rangeslider_visible=False,yaxis_title=stockN1,xaxis_title="Date",autosize=True)#title='Overview',width=500,height=500)
    CandlestickgraphJSON = json.dumps(Candlestickfig, cls=plotly.utils.PlotlyJSONEncoder)
    Linefig = go.Figure(data=[go.Line(y=stock1["Open"],x=pd.to_datetime(stock1["Date"],format='%d%m%Y'),name='Open')])#fill='tonexty'
    Linefig.add_trace(go.Line(y=stock1["High"],x=pd.to_datetime(stock1["Date"],format='%d%m%Y'),name='High'))
    Linefig.add_trace(go.Line(y=stock1["Low"],x=pd.to_datetime(stock1["Date"],format='%d%m%Y'),name='Low'))
    Linefig.add_trace(go.Line(y=stock1["Close"],x=pd.to_datetime(stock1["Date"],format='%d%m%Y'),name='Close'))
    Linefig.update_layout(xaxis_rangeslider_visible=False,yaxis_title=stockN1,xaxis_title="Date",autosize=True)#title='Overview',width=500,height=500)
    LinegraphJSON = json.dumps(Linefig, cls=plotly.utils.PlotlyJSONEncoder)
    return getinfo1.info
    return render_template("index.html" , params=params, CandlestickgraphJSON=CandlestickgraphJSON, LinegraphJSON=LinegraphJSON)

@app.route('/register' , methods = ['GET','POST'])
def register():
    if(session["emailid"] != None):
        return redirect("/")
    if(request.method=='POST'):
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        emailid = request.form.get("emailid")
        pwd = request.form.get("password")
        cpwd = request.form.get("cpassword")
        hashpwd = hashlib.md5(pwd.encode())
        if(pwd==cpwd):
            userinfo = user(username=emailid,
                        password=hashpwd.hexdigest(),
                        firstname=firstname,
                        lastname=lastname)
            db.session.add(userinfo)
            db.session.commit()
            return redirect("/login")
    return render_template("register.html" , params=params)

@app.route('/login' , methods = ['GET','POST'])
def login():
    if(request.method=='POST'):
        emailid = request.form.get("emailid")
        pwd = request.form.get("password")
        hashpwd = hashlib.md5(pwd.encode())
        dbdata=user.query.filter_by(username=emailid,password=hashpwd.hexdigest()).one_or_404(description=f"No user named '{emailid}'.")
        if(dbdata.username==emailid or dbdata.password==hashpwd.hexdigest()):
            session["emailid"] = emailid
            return redirect("/")
    return render_template("login.html" , params=params)

@app.route('/logout')
def logout():
    session["emailid"] = None
    return redirect("/")


@app.route('/404')
def error():
    return render_template("404.html", params=params)

@app.route('/blank')
def blank():
    return render_template("blank.html", params=params)

@app.route('/buttons')
def buttons():
    return render_template("buttons.html", params=params)

@app.route('/cards')
def cards():
    return render_template("cards.html", params=params)

@app.route('/charts')
def charts():
    return render_template("charts.html", params=params)

@app.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if(session["emailid"] != None):
        return redirect("/")
    if(request.form.get("emailid")!=None):
        mail.send_message('New message from Omkar',
        sender = request.form.get("emailid"),
        recipients = [params['gmail-user']],
        body = "message",
        )
    return render_template("forgot-password.html", params=params)

@app.route('/tables')
def tables():
    dbdata=stock.query.all()
    return render_template("tables.html", params=params ,dbdata=dbdata)

@app.route('/utilities-animation')
def utilities_animation():
    return render_template("utilities-animation.html", params=params)

@app.route('/utilities-border')
def utilities_border():
    return render_template("utilities-border.html", params=params)

@app.route('/utilities-other')
def utilities_other():
    return render_template("utilities-other.html", params=params)

@app.route('/utilities-color')
def utilities_color():
    return render_template("utilities-color.html", params=params)

@app.route('/stock/<string:stock_slug>', methods=['GET'])
def stock_route(stock_slug):
    Symbol1=stock_slug
    stockN1=stock_slug
    getinfo1 = yf.Ticker(Symbol1)
    stock1=getinfo1.history(period="1mo")#interval="1d"
    if(request.method=='GET' and "Period_No" in request.args):
        stock1=getinfo1.history(start=request.args.get("StartDate"),end=request.args.get("EndDate"),interval=request.args.get("Interval"))#interval="1d"
    stock1.reset_index(drop = False, inplace = True)
    stock1["Date"]=pd.to_datetime(stock1["Date"],format='%d%m%Y')
    # stock1=stock1.drop(['Dividends','Stock Splits'], axis=1)
    stock1['Month']=stock1["Date"].dt.month
    stock1['Year']=stock1["Date"].dt.year
    stock1['Day']=stock1["Date"].dt.day
    Candlestickfig = go.Figure(data=[go.Candlestick(x=pd.to_datetime(stock1["Date"],format='%d%m%Y'),open=stock1['Open'],high=stock1['High'],low=stock1['Low'],close=stock1['Close'])])
    Candlestickfig.update_layout(xaxis_rangeslider_visible=False,yaxis_title=stockN1,xaxis_title="Date",autosize=True)#title='Overview',width=500,height=500)
    CandlestickgraphJSON = json.dumps(Candlestickfig, cls=plotly.utils.PlotlyJSONEncoder)
    Linefig = go.Figure(data=[go.Line(y=stock1["Open"],x=pd.to_datetime(stock1["Date"],format='%d%m%Y'),name='Open')])#fill='tonexty'
    Linefig.add_trace(go.Line(y=stock1["High"],x=pd.to_datetime(stock1["Date"],format='%d%m%Y'),name='High'))
    Linefig.add_trace(go.Line(y=stock1["Low"],x=pd.to_datetime(stock1["Date"],format='%d%m%Y'),name='Low'))
    Linefig.add_trace(go.Line(y=stock1["Close"],x=pd.to_datetime(stock1["Date"],format='%d%m%Y'),name='Close'))
    Linefig.update_layout(xaxis_rangeslider_visible=False,yaxis_title=stockN1,xaxis_title="Date",autosize=True)#title='Overview',width=500,height=500)
    LinegraphJSON = json.dumps(Linefig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template("stockind.html", params=params ,CandlestickgraphJSON=CandlestickgraphJSON, LinegraphJSON=LinegraphJSON, getinfo1=getinfo1.info)

if __name__ == '__main__':
    app.run(debug=True, port=8800)