from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from datetime import datetime, timedelta

router = APIRouter()
templates = Jinja2Templates(directory="templates")

API_KEY = "a85058c857c7d9989bf4d56ebf48b492"

@router.get("/member/news", response_class=HTMLResponse)
def news_index(
    request: Request,
    q: str = Query("", description="搜尋關鍵字"),
    lang: str = Query("zh", description="語言")
):
    articles = []
    if q:
        now = datetime.utcnow()
        three_days_ago = now - timedelta(days=7)

        params = {
            "q": q,
            "lang": lang,
            "from": three_days_ago.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sortby": "publishedAt",
            "max": 10,
            "token": API_KEY
        }

        res = requests.get("https://gnews.io/api/v4/search", params=params)
        if res.ok:
            articles = res.json().get("articles", [])

    return templates.TemplateResponse("news.html", {
        "request": request,
        "q": q,
        "lang": lang,
        "articles": articles
    })