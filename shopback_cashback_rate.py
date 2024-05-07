import requests
from bs4 import BeautifulSoup
import json
import sched
import time
from flask import Flask, render_template
from threading import Thread
from datetime import datetime

app = Flask(__name__)

import re

def fetch_merchant_info():
    url = "https://www.shopback.com.tw/all--stores"
    response = requests.get(url)
    html_content = response.content

    soup = BeautifulSoup(html_content, "html.parser")
    merchant_cards = soup.select("div.organism__grid__offer-card")
    merchant_info = []
    seen_merchants = set()

    for card in merchant_cards:
        merchant_name = card.select_one("img")["alt"]
        merchant_link = card.select_one("a")["href"]  # 獲取商家連結
        merchant_logo_url = card.select_one("img")["src"]
        
        # 過濾掉名為 "Adidas" 的商家
        if merchant_name == "Adidas":
            continue
        
        cashback_rate_text = card.select_one(".atom__typo--type-cashback").text.strip()
        
        # 使用正則表達式提取百分比數值
        match = re.search(r"(\d+)%?", cashback_rate_text)
        if match:
            cashback_rate = int(match.group(1))
        else:
            cashback_rate = 0

        # 如果是新的商家,才加入列表
        if merchant_name not in seen_merchants:
            merchant_info.append({"name": merchant_name, "cashback_rate": cashback_rate, "cashback_rate_text": cashback_rate_text, "link": merchant_link, "logo_url": merchant_logo_url})  # 添加商家連結
            seen_merchants.add(merchant_name)

    # 加入更新時間
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"update_time": update_time, "cashback_list": merchant_info}

def save_merchant_info(sc):
    merchant_info = fetch_merchant_info()
    with open("merchant_info.json", "w", encoding="utf-8") as f:
        json.dump(merchant_info, f, ensure_ascii=False, indent=2)
    print("Merchant info saved to merchant_info.json")
    sc.enter(600, 1, save_merchant_info, (sc,))

@app.route("/")
def index():
    with open("merchant_info.json", "r", encoding="utf-8") as f:
        merchant_info = json.load(f)
    update_time = merchant_info.get("update_time", "N/A")
    cashback_list = merchant_info.get("cashback_list", [])
    return render_template("index.html", cashback_list=cashback_list, update_time=update_time)

if __name__ == "__main__":
    scheduler = sched.scheduler(time.time, time.sleep)
    save_merchant_info(scheduler)

    # 在新的執行緒中執行排程器
    Thread(target=scheduler.run).start()

    # 在主執行緒中執行 Flask 應用程式
    app.run(debug=True)
