from flask import Flask, render_template, request, redirect, url_for, flash , session
import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf
from datetime import datetime
from tabulate import tabulate

app = Flask(__name__)
app.secret_key = 'SEC'

yf.pdr_override()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyzeNF', methods=['POST'])
def analyzeNF():
    with open(f"List.txt") as f:
        data = f.read()
    result = analyze_stocks(data,False)
    if result:
        flash('Analysis completed successfully', 'success')

    return render_template('index.html', result=result)

@app.route('/analyze', methods=['POST'])
def analyze():
    result = False
    if request.method == 'POST':
        
        if len(list(request.form)) == 1:
            fileName = request.form['fileName']
            result = analyze_stocks(fileName,False)

        else:
            file = request.files['fileInput']
            if not file:
                flash('No File Detected', 'error')
            result = analyze_stocks(file,True)


    if result:
        flash('Analysis completed successfully', 'success')

    return render_template('index.html', result=result)


def RSI(tickerNS, ticker, Dict):
    startdate = datetime(2022, 1, 1)
    
    data = pdr.get_data_yahoo(tickerNS, start=startdate)
    if data.empty:
        flash(f"{tickerNS[:-2]} not exits","error")


    momentum_period = 10
    bars_back = 150
    days = 14
    gap = 10
    RSIUpper = 61
    RSILower = 35

    data['Momentum'] = data["Close"].diff(momentum_period - 1)

    delta = data["Close"].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    average_up = up.ewm(com=(days - 1), adjust=False).mean()
    average_down = down.ewm(com=(days - 1), adjust=False).mean()
    rs = average_up / average_down
    rsi = 100 - (100 / (1 + rs))
    data["RSI"] = rsi

    if len(data['RSI']) < 5:
        return
        
    datalast = data["RSI"].iloc[-1]
    dataPrev2 = data["RSI"].iloc[-2]
    dataPrev3 = data["RSI"].iloc[-3]
    dataPrev4 = data["RSI"].iloc[-4]
    dataPrev5 = data["RSI"].iloc[-5]
    datalast = round(datalast, 2)
    dataPrev2 = round(dataPrev2, 2)
    dataPrev3 = round(dataPrev3, 2)
    dataPrev4 = round(dataPrev4, 2)
    dataPrev5 = round(dataPrev5, 2)

    divergence_points = []
    buySell = 3

    momentumBoolBuy = data["Close"].iloc[-(gap+1)] > data["Close"].iloc[-1] and data['Momentum'].iloc[-(gap+1)] > data['Momentum'].iloc[-1]
    RSIBoolBuy = data["RSI"].iloc[-1] < RSILower

    momentumBoolSell = data["Close"].iloc[-(gap+1)] < data["Close"].iloc[-1] and data['Momentum'].iloc[-(gap+1)] < data['Momentum'].iloc[-1]
    RSIBoolSell = data["RSI"].iloc[-1] > RSIUpper

    if RSIBoolBuy and  momentumBoolBuy:
        buySell = 0
            
    elif RSIBoolSell and  momentumBoolSell:
        buySell = 1

    if len(divergence_points) !=0:
        divergence_dates, divergence_prices = zip(*divergence_points)

    Dict.update({str(ticker): [datalast, dataPrev2, dataPrev3, dataPrev4, dataPrev5, buySell]})

def STOCKS(fileName,Dict,bool):
    tickers_nse = []
    if not bool: 
        if len(fileName) > 2:
            data = fileName
            tickers_nse = data.split(",")
        else:
            flash('Empty Field!', 'error')
            return False
        
    else:
        data = fileName.read().decode("utf-8")
        tickers_nse = data.split(",")
    




    if len(tickers_nse) != 0 and tickers_nse[0] != "":
        for ticker in tickers_nse:
            tickerNS = ticker + ".NS"
            RSI(tickerNS, ticker ,Dict)


def analyze_stocks(fileName,bool):
    Dict = {}
    STOCKS(fileName,Dict,bool)

    buy = []
    sell = []
    hold = []
    nothold = []

    Dict = dict(sorted(Dict.items(), reverse=True, key=lambda item: item[1][0]))

    for key, value in Dict.items():
        if value[5] == 0:
            buy.append(f"{key} : {value[0]}")

        elif value[5] == 1:
            sell.append(f"{key} : {value[0]}")

        elif ((value[0] < value[1] < value[2] < value[3] < value[4]) or
              (value[0] < value[1] < value[2] < value[3]) or
              (value[0] < value[1] < value[2]) or
              (value[0] < value[1] < value[2] < value[4]) or
              (value[0] < value[1] < value[3] < value[4]) or
              (value[0] < value[2] < value[3] < value[4]) or
              (value[1] < value[2] < value[3] < value[4]) or
              (value[0] < value[1] < value[3]) or
              (value[0] < value[2] < value[3]) or
              (value[0] < value[3] < value[4]) or
              (value[0] < value[1] < value[4])):
            nothold.append(f"{key} : {value[0]}")

        else:
            hold.append(f"{key} : {value[0]}")

    if len(buy) > 1:
        buy.reverse()

    length = [len(buy), len(sell), len(hold), len(nothold)]
    max_length = max(length)

    buy.extend([" "] * (max_length - len(buy)))
    sell.extend([" "]* (max_length - len(sell)))
    hold.extend([" "]* (max_length - len(hold)))
    nothold.extend([" "]* (max_length - len(nothold)))

    data = []
    for buy_stock, sell_stock, hold_stock, nothold_stock in zip(buy, sell, hold, nothold):
        data.append([buy_stock, sell_stock, hold_stock, nothold_stock])

    headers = ["BUY", "SELL", "HOLD", "DOWN"]

    table = tabulate(data, headers=headers, tablefmt="grid")

    with open("Table.txt", "w") as file:
        file.write(table)


    return data


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')
