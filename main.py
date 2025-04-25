from fastapi import FastAPI, Request, Form, Depends, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import bcrypt
import mysql.connector
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel
from stock import get_stock_info, load_favorites, save_favorites, show_favorites
from news import router  

# FastAPI 初始化

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)

# MySQL 資料庫連線設定

DATABASE_URL = "mysql+mysqlconnector://root:1234@localhost/user"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base() # 自動建立資料表

# 使用者模型

class User(Base): # 建立User資料表對應模型(ORM)
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)

# 創建資料表

Base.metadata.create_all(bind=engine)

# Pydantic 模型（用來驗證請求資料）

class SignupRequest(BaseModel):
    nickname: str
    email: str
    password: str

# 取得資料庫 Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 首頁

@app.get("/", response_class=HTMLResponse)  # 根路徑
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 註冊 API

@app.post("/signup")
async def signup(nickname: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # 檢查是否有重複的 email
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="信箱已經被註冊")

    # 密碼加密

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # 創建新的用戶資料

    new_user = User(
        nickname=nickname,
        email=email,
        password=hashed_password.decode('utf-8')  # 把字節資料轉換成字串
    )

    # 儲存新用戶

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    print(nickname, email, password)
    return RedirectResponse("/?success=1", status_code=302)

 # 登入 

@app.post("/signin")
async def signin(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()

    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):

        # 登入失敗 改導向首頁並帶錯誤訊息

        return RedirectResponse(url="/?error=帳號或密碼錯誤", status_code=302)

    # 登入成功設定 Cookie 並導向會員頁

    response = RedirectResponse(url="/member", status_code=302)
    response.set_cookie(key="nickname", value=user.nickname)
    return response

# 登出

@app.get("/signout")
async def signout(request: Request):
    # 刪除 cookie 中的資料來登出
    response = RedirectResponse(url="/")  
    response.delete_cookie("nickname")  
    return response

# 防止使用者直接輸入網址進入會員頁面 會檢查 Cookie 中有沒有登入過的資料

@app.get("/member", response_class=HTMLResponse)
async def member(request: Request, nickname: str = Cookie(default=None)):
    if not nickname:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("member.html", {"request": request,"nickname": nickname})

# GNews 查詢首頁

@app.get("/news", response_class=HTMLResponse)
def news_home(request: Request):
    return templates.TemplateResponse("news.html", {"request": request})

# 股票查詢首頁

@app.get("/stock", response_class=HTMLResponse)
def stock_home(request: Request):
    return templates.TemplateResponse("stock.html", {"request": request})

# 股票查詢

@app.post("/search", response_class=HTMLResponse)
async def search(request: Request, code: str = Form(...)):
    info = get_stock_info(code)  # ← 直接用
    favorites = load_favorites()
    return templates.TemplateResponse("stock.html", {
        "request": request,
        "info": info,
        "query": code,
        "favorites": favorites
    })

# 加入收藏

@app.post("/add", response_class=HTMLResponse)
def add_favorite(request: Request, code: str = Form(...)):
    favorites = load_favorites()
    added = False
    if code not in favorites:
        favorites.append(code)
        save_favorites(favorites)
        added = True

    info = get_stock_info(code)
    return templates.TemplateResponse("stock.html", {
        "request": request,
        "info": info,
        "query": code,
        "favorites": favorites,
        "message": " 已加入收藏" if added else " 此股票已在收藏中"
    })

# 移除收藏

@app.post("/remove", response_class=HTMLResponse)
def remove_favorite(request: Request, code: str = Form(...)):
    favorites = load_favorites()
    removed = False
    if code in favorites:
        favorites.remove(code)
        save_favorites(favorites)
        removed = True

    return templates.TemplateResponse("stock.html", {
        "request": request,
        "favorites": favorites,
        "message": f" 已移除 {code}" if removed else " 此股票不在收藏中"
    })

#  收藏清單

@app.get("/favorites", response_class=HTMLResponse)
def show_favorites(request: Request):
    favs = load_favorites()
    details = [{"code": c, "info": get_stock_info(c)} for c in favs]
    return templates.TemplateResponse("favorites.html", {
        "request": request,
        "favorites_detail": details
    })
