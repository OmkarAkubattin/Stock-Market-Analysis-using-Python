from flask import Flask, render_template, redirect, request, session
# from flask_session import Session
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
import hashlib
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
from apps.smt import Stocks
import json
from turbo_flask import Turbo
from GoogleNews import GoogleNews
import pandas as pd
from datetime import date
import time


with open("config.json", "r") as c:
    params = json.load(c)["params"]
local_server = True
obforcontext = Stocks(Symbol="NESTLEIND.NS",period="max",stocprice=True)
googlenews=GoogleNews(start=date.fromtimestamp(time.time()-604800).strftime('%m/%d/%Y'),end=date.fromtimestamp(time.time()).strftime('%m/%d/%Y'))
googlenews.search('Stock Market')
result=googlenews.result()

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = 'any random string'
# Session(app)
if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']

db = SQLAlchemy(app)
turbo = Turbo(app)
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
    open = db.Column(db.Float, nullable=False)
    high = db.Column(db.Float, nullable=False)
    low = db.Column(db.Float, nullable=False)
    close = db.Column(db.Float, nullable=False)
    volume = db.Column(db.Float, nullable=False)
    change = db.Column(db.Float, nullable=False)
    changeper = db.Column(db.Float, nullable=False)
    fk_stock = db.Column(db.Integer, nullable=False)

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
    url="https://finance.yahoo.com/lookup/all?s=india&t=A&b=0&c=3184"
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
    if(request.method =="GET" and "changeSymbol" in request.args):
        obforcontext = Stocks(Symbol=request.args.get("changeSymbol"),period="max",stocprice=True)
        return render_template("index.html" , params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)
    else:
        obforcontext = Stocks(Symbol=params["watchlist"][0],period="max",stocprice=True)
        return render_template("index.html" , params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('register' , methods = ['GET','POST'])
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
    return render_template("register.html" , params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('login' , methods = ['GET','POST'])
def login():
    if(request.method=='POST'):
        emailid = request.form.get("emailid")
        pwd = request.form.get("password")
        hashpwd = hashlib.md5(pwd.encode())
        dbdata=user.query.filter_by(username=emailid,password=hashpwd.hexdigest()).one_or_404(description=f"No user named '{emailid}'.")
        if(dbdata.username==emailid or dbdata.password==hashpwd.hexdigest()):
            session["emailid"] = emailid
            return redirect("/")
    return render_template("login.html" , params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('logout')
def logout():
    session["emailid"] = None
    return redirect("/")

@app.route('404')
def error():
    return render_template("404.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('Symbol', methods = ['GET',"POST"])
def Symbol():
    if(request.method == "GET" and request.args.get("stockSymbol")!=None):
        data =request.args.get("stockSymbol").split("_")
        obforcontext = Stocks(Symbol=data[0],period=data[1],stocprice=True)
    return render_template("Symbol.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('forgot-password', methods=['GET','POST'])
def forgot_password():
    if(session["emailid"] != None):
        return redirect("/")
    if(request.form.get("emailid")!=None):
        mail.send_message('New message from Omkar',
        sender = request.form.get("emailid"),
        recipients = [params['gmail-user']],
        body = "message",
        )
    return render_template("forgot-password.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('tables')
def tables():
    dbdata = stock.query.all()
    return render_template("tables.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext ,dbdata=dbdata)

@app.route('/admin/sip')
def sip():
    return render_template("sip.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('moving_average')
def moving_average():
    return render_template("moving_average.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('/roi')
def roi():
    return render_template("roi.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('/profit_loss_ratio')
def profit_loss_ratio():
    return render_template("profit_loss_ratio.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('/stock_comparison')
def stock_comparison():
    return render_template("stock_comparison.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('stock/<string:stock_slug>', methods=['GET'])
def stock_route(stock_slug):
    return render_template("stockind.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('/admin/', methods = ['GET','POST'])
def dashbord():
    if not session.get("emailid"):
            return redirect("/login")
    return render_template("admin/index.html" , params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('/admin/register' , methods = ['GET','POST'])
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
    return render_template("admin/register.html" , params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('/admin/login' , methods = ['GET','POST'])
def login():
    if(request.method=='POST'):
        emailid = request.form.get("emailid")
        pwd = request.form.get("password")
        hashpwd = hashlib.md5(pwd.encode())
        dbdata=user.query.filter_by(username=emailid,password=hashpwd.hexdigest()).one_or_404(description=f"No user named '{emailid}'.")
        if(dbdata.username==emailid or dbdata.password==hashpwd.hexdigest()):
            session["emailid"] = emailid
            return redirect("/")
    return render_template("admin/login.html" , params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('/admin/logout')
def logout():
    session["emailid"] = None
    return redirect("/")

@app.route('/admin/forgot-password', methods=['GET','POST'])
def forgot_password():
    if(session["emailid"] != None):
        return redirect("/")
    if(request.form.get("emailid")!=None):
        mail.send_message('New message from Omkar',
        sender = request.form.get("emailid"),
        recipients = [params['gmail-user']],
        body = "message",
        )
    return render_template("admin/forgot-password.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('/admin/tables')
def tables():
    dbdata = stock.query.all()
    return render_template("admin/tables.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext ,dbdata=dbdata)

if __name__ == '__main__':
    app.run(debug=True, port=8800)
    