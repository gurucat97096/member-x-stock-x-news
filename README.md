# 會員系統 x 即時新聞 x 股票查詢平台

這是一個使用 **FastAPI** 建構的全端整合專案，結合會員登入註冊、股票即時查詢、GNews 新聞搜尋與股票收藏管理功能。

![image](https://github.com/user-attachments/assets/d5fa56dc-9860-434e-9c2d-2873e34c25ee)


---

##  專案介紹

使用者可以註冊並登入系統後，使用兩大功能：
![image](https://github.com/user-attachments/assets/db788d16-7a02-4e2f-a9b9-c821c223ed03)


1. **GNews 即時新聞查詢**（支援多語言、主題搜尋）
 ![image](https://github.com/user-attachments/assets/d1cebdbb-5cbd-4951-902c-a91f0e4273e6)

2. **股票查詢與收藏系統**（查詢台股個股資料並可加入收藏）
![image](https://github.com/user-attachments/assets/aedb3f8c-2e2e-4c70-989d-948e96971ab0)

---

##  功能特色

- 使用 **FastAPI** 作為後端框架
- **Jinja2** 模板渲染前端頁面
- 整合 **yfinance API** 與 **GNews API**
- **MySQL** 儲存會員資料
- 利用 **Cookies** 實現登入狀態保持
- 全中文介面，頁面美觀、互動友善

---

##  安裝教學

###  環境需求

- Python 3.8+
- MySQL 資料庫（帳號密碼請視情況修改）
- GNews API Key（可免費申請）

###  安裝步驟

```bash
# 1. 複製專案
git clone https://github.com/gurucat97096/member-x-stock-x-news
.git
cd member-system

# 2. 建立虛擬環境（可選）
python -m venv venv
venv\Scripts\activate  # Windows

# 3. 安裝套件
pip install -r requirements.txt

# 4. 啟動服務
uvicorn main:app --reload
