from flask import Flask, render_template, redirect, request, session, jsonify
# from flask_session import Session
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
import hashlib
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
from apps.smt import Stocks
import json
from GoogleNews import GoogleNews
import pandas as pd
from datetime import date
import time
import json


with open("config.json", "r") as c:
    params = json.load(c)["params"]
local_server = True
obforcontext = Stocks(Symbol="NESTLEIND.NS",period="max",stocprice=True)
googlenews=GoogleNews(start=date.fromtimestamp(time.time()-60*24*30*12).strftime('%m/%d/%Y'),end=date.fromtimestamp(time.time()).strftime('%m/%d/%Y'))
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
    user_role = db.Column(db.Integer, nullable=False)

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
    if not session.get("emailid") :
         return redirect("/login")
    elif session.get("user_role") == 0:
        if(request.method =="GET" and "changeSymbol" in request.args):
            obforcontext = Stocks(Symbol=request.args.get("changeSymbol"),period="max",stocprice=True)
            return render_template("index.html" , params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)
        else:
            obforcontext = Stocks(Symbol=params["watchlist"][0],period="max",stocprice=True)
            return render_template("index.html" , params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)
    else:
        return redirect("/admin")


@app.route('/register' , methods = ['GET','POST'])
def register():
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
                        lastname=lastname,
                        user_role=0)
            db.session.add(userinfo)
            db.session.commit()
            return redirect("/login")
    return render_template("register.html" , params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('/login' , methods = ['GET','POST'])
def login():
    if(request.method=='POST'):
        emailid = request.form.get("emailid")
        pwd = request.form.get("password")
        hashpwd = hashlib.md5(pwd.encode())
        dbdata=user.query.filter_by(username=emailid,password=hashpwd.hexdigest()).first()#.one_or_404(description=f"No user named '{emailid}'.")
        if(dbdata.username==emailid or dbdata.password==hashpwd.hexdigest()):
            session["emailid"] = emailid
            session["user_role"] = dbdata.user_role
            params["firstname"] = dbdata.firstname
            params["lastname"] = dbdata.lastname
            if dbdata.user_role == 1:
                return redirect("/admin")
            else:
                return redirect("/")
    return render_template("login.html" , params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('/logout')
def logout():
    session["emailid"] = None
    return redirect("/")

@app.route('/404')
def error():
    return render_template("404.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

@app.route('/Stock', methods = ['GET',"POST"])
def Stock():
    if not session.get("emailid") :
         return redirect("/login")
    elif session.get("user_role") == 0:
        if(request.method == "GET" and request.args.get("stockSymbol")!=None):
            data =request.args.get("stockSymbol").split("_")
            obforcontext = Stocks(Symbol=data[0],period=data[1],stocprice=True)
        return render_template("Symbol.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)
    else:
        return redirect("/admin")

@app.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if not session.get("emailid") :
         return redirect("/login")
    elif session.get("user_role") == 0:
        if(request.form.get("emailid")!=None):
            mail.send_message('New message from Omkar',
            sender = request.form.get("emailid"),
            recipients = [params['gmail-user']],
            body = "message",
            )
        return render_template("forgot-password.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)
    else:
        return redirect("/admin")

@app.route('/Symbol')
def Symbol():
    if not session.get("emailid") :
         return redirect("/login")
    elif session.get("user_role") == 0:
        dbdata = stock.query.all()
        return render_template("Symbol.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext ,dbdata=dbdata)
    else:
        return redirect("/admin")


@app.route('/sip')
def sip():
    if not session.get("emailid") :
         return redirect("/login")
    elif session.get("user_role") == 0:
        return render_template("sip.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)
    else:
        return redirect("/admin")

@app.route('/moving_average', methods=['GET'])
def moving_average():
    if not session.get("emailid") :
         return redirect("/login")
    elif session.get("user_role") == 0:
        if request.method == "GET" and (request.args.get("symbol")!=None):
            obforcontext = Stocks(Symbol=request.form.get("symbol"),period="max",stocprice=True)
        else:
            obforcontext = Stocks(Symbol="NESTLEIND.NS",period="max",stocprice=True)
        return render_template("moving_average.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)
    else:
        return redirect("/admin")

@app.route('/roi', methods=['GET'])
def roi():
    if not session.get("emailid") :
         return redirect("/login")
    elif session.get("user_role") == 0:
        if (request.method == "GET" and (request.args.get("symbol1")!=None and request.args.get("symbol2")!=None)):
            obforcontext = Stocks(Symbol=request.args.get("symbol1"),period="max",stocprice=True)
            obforcontext2= Stocks(Symbol=request.args.get("symbol2"),period="max",stocprice=True)
        else:
            obforcontext = Stocks(Symbol="NESTLEIND.NS",period="max",stocprice=True)
            obforcontext2=Stocks(Symbol="TATAMOTORS.NS",period="max",stocprice=True)
        stockname1=str(obforcontext.getinfo.info["underlyingSymbol"])
        sum=0
        s=0
        for i in range(len(obforcontext.stock)):
            if obforcontext.stock.loc[i,'Day']==30:
                sum+=obforcontext.stock.loc[i,'Open']
                s+=1
        tm_end=obforcontext.stock.loc[obforcontext.stock["Open"].size-1,'Open']
        result1=round((tm_end*s)-sum,2)
        roi1=round((result1/sum)*100,2)
        stockname2=str(obforcontext2.getinfo.info["underlyingSymbol"])
        sum=0
        s=0
        for i in range(len(obforcontext2.stock)):
            if obforcontext2.stock.loc[i,'Day']==30:
                sum+=obforcontext2.stock.loc[i,'Open']
                s+=1
        tm_end=obforcontext2.stock.loc[obforcontext2.stock["Open"].size-1,'Open']
        result2=round((tm_end*s)-sum,2)
        roi2=round((result2/sum)*100,2)
        return render_template("roi.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext,stockname=[stockname1,stockname2],result=[result1,result2],roi=[roi1,roi2])
    else:
        return redirect("/admin")

@app.route('/profit_loss_ratio')
def profit_loss_ratio():
    if not session.get("emailid") :
         return redirect("/login")
    elif session.get("user_role") == 0:
        if(request.method == "GET" and (request.args.get("symbol1")!=None and request.args.get("symbol2")!=None)):
            obforcontext = Stocks(Symbol=request.args.get("symbol1"),period="max",stocprice=True)
            obforcontext2= Stocks(Symbol=request.args.get("symbol2"),period="max",stocprice=True)
        else:
            obforcontext = Stocks(Symbol="NESTLEIND.NS",period="max",stocprice=True)
            obforcontext2=Stocks(Symbol="TATAMOTORS.NS",period="max",stocprice=True)
        stockname1=str(obforcontext.getinfo.info["underlyingSymbol"])
        sum=0
        s=0
        for i in range(len(obforcontext.stock)):
            if obforcontext.stock.loc[i,'Day']==30:
                sum+=obforcontext.stock.loc[i,'Open']
                s+=1
        tm_end=obforcontext.stock.loc[obforcontext.stock["Open"].size-1,'Open']
        result1=round((tm_end*s)-sum,2)
        roi1=round((result1/sum)*100,2)
        stockname2=str(obforcontext2.getinfo.info["underlyingSymbol"])
        sum=0
        s=0
        for i in range(len(obforcontext2.stock)):
            if obforcontext2.stock.loc[i,'Day']==30:
                sum+=obforcontext2.stock.loc[i,'Open']
                s+=1
        tm_end=obforcontext2.stock.loc[obforcontext2.stock["Open"].size-1,'Open']
        result2=round((tm_end*s)-sum,2)
        roi2=round((result2/sum)*100,2)
        return render_template("profit_loss_ratio.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext,stockname=[stockname1,stockname2],result=[result1,result2],roi=[roi1,roi2])
    else:
        return redirect("/admin")

@app.route('/stock_comparison')
def stock_comparison():
    if not session.get("emailid") :
         return redirect("/login")
    elif session.get("user_role") == 0:
        if (request.method == "GET" and (request.args.get("symbol1")!=None and request.args.get("symbol2")!=None)):
            obforcontext = Stocks(Symbol=request.args.get("symbol1"),period="max",stocprice=True)
            obforcontext2= Stocks(Symbol=request.args.get("symbol2"),period="max",stocprice=True)
        else:
            obforcontext = Stocks(Symbol="NESTLEIND.NS",period="max",stocprice=True)
            obforcontext2=Stocks(Symbol="TATAMOTORS.NS",period="max",stocprice=True)
        stockname1=str(obforcontext.getinfo.info["underlyingSymbol"])
        sum=0
        s=0
        for i in range(len(obforcontext.stock)):
            if obforcontext.stock.loc[i,'Day']==30:
                sum+=obforcontext.stock.loc[i,'Open']
                s+=1
        tm_end=obforcontext.stock.loc[obforcontext.stock["Open"].size-1,'Open']
        result1=round((tm_end*s)-sum,2)
        roi1=round((result1/sum)*100,2)
        stockname2=str(obforcontext2.getinfo.info["underlyingSymbol"])
        sum=0
        s=0
        for i in range(len(obforcontext2.stock)):
            if obforcontext2.stock.loc[i,'Day']==30:
                sum+=obforcontext2.stock.loc[i,'Open']
                s+=1
        tm_end=obforcontext2.stock.loc[obforcontext2.stock["Open"].size-1,'Open']
        result2=round((tm_end*s)-sum,2)
        roi2=round((result2/sum)*100,2)
        return render_template("stock_comparison.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext,stockname=[stockname1,stockname2],result=[result1,result2],roi=[roi1,roi2])
    else:
        return redirect("/admin")

@app.route('/stock/<string:stock_slug>', methods=['GET'])
def stock_route(stock_slug):
    return render_template("stockind.html", params=params, news=result,newslen=int(len(result)/4 ), watchlistdata=Stocks().watchlist(watchlist=params["watchlist"]), ob=obforcontext)

#admin------------------------------------------------


@app.route('/admin/')
def admin_dashbord():
    if not session.get("emailid") :
         return redirect("/login")
    elif session.get("user_role") == 1:
        if not session.get("emailid"):
                return redirect("/login")
        dbdata = stock.query.all()
        return render_template("/admin/index.html" , params=params, dbdata=dbdata)
    else:
        return redirect("/")

@app.route('/admin/users')
def users():
    if not session.get("emailid") :
         return redirect("/login")
    elif session.get("user_role") == 1:
        dbdata = user.query.all()
        return render_template("/admin/user.html", params=params, dbdata=dbdata)
    else:
        return redirect("/")
    
@app.route('/admin/edit_stock', methods=['GET','POST'])
def edit_stock():
    if not session.get("emailid") :
         return redirect("/login")
    elif session.get("user_role") == 1:
        id = request.args.get("edit_stock")
        dbdata=stock.query.filter_by(id=id).first()
        if request.method == "POST":
            symbol = request.form.get("symbol")
            name = request.form.get("stockname")
            lastprice = request.form.get("lastprice")
            industry = request.form.get("industry")
            type = request.form.get("stocktype")
            exchange = request.form.get("exchange")
            stockinfo = stock(symbol=symbol,
                        name=name,
                        lastprice=lastprice,
                        industry=industry,
                        type=type,
                        exchange=exchange)
            stockinfo.verified = True
            db.session.commit()
            return redirect("/admin/")
        return render_template("/admin/edit_stock.html", params=params,dbdata=dbdata)
    else:
        return redirect("/")

@app.route('/admin/edit_user', methods=['GET','POST'])
def user_edit():
    if not session.get("emailid") :
         return redirect("/login")
    elif session.get("user_role") == 1:
        id = request.args.get("edit_user")
        dbdata=user.query.filter_by(id=id).first()
        if request.method == "POST":
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
                            lastname=lastname,
                            user_role=0)
                userinfo.verified = True
                db.session.commit()
                return redirect("/admin/users")
        return render_template("/admin/edit_user.html", params=params,dbdata=dbdata)
    else:
        return redirect("/")

@app.route('/admin/add_stock', methods=['GET','POST'])
def add_stock():
    if not session.get("emailid") :
         return redirect("/login")
    elif session.get("user_role") == 1:
        if request.method == "POST":
            symbol = request.form.get("symbol")
            name = request.form.get("stockname")
            lastprice = request.form.get("lastprice")
            industry = request.form.get("industry")
            type = request.form.get("stocktype")
            exchange = request.form.get("exchange")
            stockinfo = stock(symbol=symbol,
                        name=name,
                        lastprice=lastprice,
                        industry=industry,
                        type=type,
                        exchange=exchange)
            db.session.add(stockinfo)
            db.session.commit()
            return redirect("/admin/")
        return render_template("/admin/add_stock.html", params=params)
    else:
        return redirect("/")

@app.route('/admin/add_user', methods=['GET','POST'])
def add_user():
    if not session.get("emailid") :
         return redirect("/login")
    elif session.get("user_role") == 1:
        if request.method == "POST":
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
                            lastname=lastname,
                            user_role=0)
                db.session.add(userinfo)
                db.session.commit()
                return redirect("/admin/users")
        return render_template("/admin/add_user.html", params=params)
    else:
        return redirect("/")
    
@app.route('/admin/delete_user', methods=['GET','POST'])
def delete_user():
    if request.method == "POST":
        id = request.form.get("delete_stock")
        user.query.filter_by(id=id).delete()
        db.session.commit()
        return redirect("/admin/users")


@app.route('/admin/delete_stock', methods=['GET','POST'])
def delete_stock():
    if request.method == "POST":
        id = request.form.get("delete_user")
        stock.query.filter_by(id=id).delete()
        db.session.commit()
        return redirect("/admin/")


        

if __name__ == '__main__':
    app.run(debug=True, port=8800)
    