from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import yfinance as yf
import json
import os
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

FAVORITES_FILE = "favorites.json"

field_translation = {
    "previousClose"             : "前收市價",
    "open"                      : "開市",
    "bid"                       : "買盤",
    "ask"                       : "賣出價",
    "dayLow"                    : "今日最低價",
    "dayHigh"                   : "今日最高價",
    "fiftyTwoWeekLow"           : "52週最低價",
    "fiftyTwoWeekHigh"          : "52週最高價",
    "volume"                    : "成交量",
    "averageVolume"             : "平均成交量",
    "marketCap"                 : "市值",
    "totalAssets"               : "淨資產",
    "bookValue"                 : "每股資產淨值",
    "priceToBook"               : "股價淨值比",
    "trailingPE"                : "市盈率 (最近 12 個月)",
    "trailingEps"               : "每股盈利 (最近 12 個月)",
    "dividendYield"             : "收益率",
    "dividendRate"              : "遠期股息",
    "exDividendDate"            : "除息日",
    "nextEarningsDate"          : "業績公佈日",
    "annualReportExpenseRatio"  : "支出比率 (淨計)",
    "returnOnEquity"            : "股東權益報酬率 ROE",
    "earningsQuarterlyGrowth"   : "季度盈餘成長率",
    "beta"                      : "Beta 值 (5年)",
    "recommendationKey"         : "分析師評等",
    "sector"                    : "產業類別",
    "industry"                  : "產業細項",
    "longName"                  : "公司全名",
    "shortName"                 : "公司簡稱"
}

def format_date(value):
    try:
        if isinstance(value, (int, float)) and value > 1000000000:
            return datetime.fromtimestamp(value).strftime('%Y年%m月%d日')
        elif isinstance(value, datetime):
            return value.strftime('%Y年%m月%d日')
        return value
    except:
        return value

def is_meaningful(value):
    return value not in (None, '', 'N/A', 0, 0.0)

def get_stock_info(code: str):
    try:
        stock = yf.Ticker(f"{code}.TW")
        info = stock.info
        fast_price = stock.fast_info.get("lastPrice")
        data = {}
        if fast_price:
            data[" 當前價格"] = f"{fast_price} 元"
        for key, cname in field_translation.items():
            value = info.get(key)
            if is_meaningful(value):
                value = format_date(value)
                if key == "dividendYield" and isinstance(value, float):
                    value = f"{round(value * 100, 2)}%"
                if key == "dividendRate":
                    yield_val = info.get("dividendYield")
                    if yield_val and is_meaningful(yield_val):
                        value = f"{value} ({round(yield_val * 100, 2)}%)"
                data[cname] = value
        return data
    except Exception as e:
        return {"錯誤": str(e)}

def load_favorites():
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, "r") as f:
            return json.load(f)
    return []

def save_favorites(favs):
    with open(FAVORITES_FILE, "w") as f:
        json.dump(favs, f)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("stock.html", {"request": request})

@app.post("/add", response_class=HTMLResponse)
def add_favorite(request: Request, code: str = Form(...)):
    favs = load_favorites()
    added = False
    if code not in favs:
        favs.append(code)
        save_favorites(favs)
        added = True
    info = get_stock_info(code)
    return templates.TemplateResponse("stock.html", {
        "request": request,
        "info": info,
        "query": code,
        "favorites": favs,
        "message": " 已加入收藏" if added else " 此股票已在收藏中"
    })

@app.post("/remove", response_class=HTMLResponse)
def remove_favorite(request: Request, code: str = Form(...)):
    favs = load_favorites()
    removed = False
    if code in favs:
        favs.remove(code)
        save_favorites(favs)
        removed = True

    details = [{"code": c, "info": get_stock_info(c)} for c in favs]
    return templates.TemplateResponse("favorites.html", {
        "request": request,
        "favorites_detail": details,
        "message": f" 已移除 {code}" if removed else " 不存在於收藏"
    })

@app.get("/search", response_class=HTMLResponse)
def search(request: Request, code: str = Query(...)):
    info = get_stock_info(code)
    favs = load_favorites()
    return templates.TemplateResponse("stock.html", {
        "request": request,
        "info": info,
        "query": code,
        "favorites": favs
    })

@app.get("/favorites", response_class=HTMLResponse)
def show_favorites(request: Request):
    favs = load_favorites()
    details = [{"code": c, "info": get_stock_info(c)} for c in favs]
    return templates.TemplateResponse("favorites.html", {
        "request": request,
        "favorites_detail": details
    })

