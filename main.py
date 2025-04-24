from fastapi import *
from fastapi.responses import *
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import mysql.connector
import bcrypt
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from stock import get_stock_info, load_favorites, save_favorites, show_favorites
from news import router

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)

@app.get("/", response_class=HTMLResponse)  # 根路徑
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/member")
async def member(request: Request):
    # 透過 cookies 取得用戶的 nickname
    nickname = request.cookies.get("nickname")

    if not nickname:
        # 如果沒有登入，重定向回首頁或登入頁面
        # 使用 303 重定向，強制使用 GET 請求
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse("member.html", {"request": request, "nickname": nickname})


@app.get("/error", response_class=HTMLResponse)
def error(request: Request, msg: str = "發生錯誤,請聯繫客服"):
    return templates.TemplateResponse("error.html", {"request": request, "message": msg})


DATABASE_URL = "mysql+mysqlconnector://root:1234@localhost/user"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base() # 自動建立資料表

# 定義User資料庫模型


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


@app.post("/signin")
async def signin(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()

    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        # 登入失敗：改導向首頁並帶錯誤訊息
        return RedirectResponse(url="/?error=帳號或密碼錯誤", status_code=302)

    # 登入成功：設定 Cookie 並導向會員頁
    response = RedirectResponse(url="/member", status_code=302)
    response.set_cookie(key="nickname", value=user.nickname)
    return response


@app.get("/signout")
async def signout(request: Request):
    # 刪除 nickname cookie 來登出
    response = RedirectResponse(url="/")  # 這裡會重定向到首頁
    response.delete_cookie("nickname")  # 刪除存儲在 cookie 中的 nickname
    return response


@app.get("/member", response_class=HTMLResponse)
async def member(request: Request, nickname: str = Cookie(default=None)):
    if not nickname:
        return RedirectResponse(url="/", status_code=302)

    favorites = load_favorites()
    return templates.TemplateResponse("member.html", {
        "request": request,
        "nickname": nickname,
        "favorites": favorites
    })


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
        "message": "✅ 已加入收藏" if added else "⚠️ 此股票已在收藏中"
    })

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
        "message": f"✅ 已移除 {code}" if removed else "⚠️ 此股票不在收藏中"
    })

@app.get("/news", response_class=HTMLResponse)
def news_home(request: Request):
    return templates.TemplateResponse("news.html", {"request": request})

@app.get("/stock", response_class=HTMLResponse)
def stock_home(request: Request):
    return templates.TemplateResponse("stock.html", {"request": request})

@app.get("/favorites", response_class=HTMLResponse)
def show_favorites(request: Request):
    favs = load_favorites()
    details = [{"code": c, "info": get_stock_info(c)} for c in favs]
    return templates.TemplateResponse("favorites.html", {
        "request": request,
        "favorites_detail": details
    })
