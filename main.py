import feedparser
import requests
import os
import re

# 從 GitHub Secrets 中讀取環境變數
RSS_URL = os.getenv("FB_RSS_URL")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
DB_FILE = "last_link.txt"

def get_image_url(entry):
    """嘗試從 RSS 項目中提取圖片網址"""
    if 'media_content' in entry and len(entry.media_content) > 0:
        return entry.media_content[0]['url']
    
    if 'summary' in entry:
        img_match = re.search(r'<img [^>]*src="([^"]+)"', entry.summary)
        if img_match:
            return img_match.group(1)
    return None

def check_updates():
    print("紅線特派員出動中...")
    
    # 檢查環境變數是否讀取成功
    if not RSS_URL or not DISCORD_WEBHOOK:
        print("錯誤：找不到環境變數 FB_RSS_URL 或 DISCORD_WEBHOOK，請檢查 Github Secrets 設定。")
        return

    # 修正：加入 User-Agent 偽裝瀏覽器，否則很多 RSS 服務會擋掉 Python 請求
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 使用 requests 抓取內容再丟給 feedparser，這樣才能自定義 headers
    try:
        response = requests.get(RSS_URL, headers=headers, timeout=30)
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"抓取 RSS 時發生錯誤：{e}")
        return
    
    if not feed.entries:
        print("哎呀，情報網斷了，抓不到東西（RSS 內容為空）。")
        # 列印出 feed 中的錯誤訊息協助偵錯
        if hasattr(feed, 'bozo_exception'):
            print(f"解析異常原因：{feed.bozo_exception}")
        return

    latest_entry = feed.entries[0]
    latest_link = latest_entry.link
    latest_title = latest_entry.title
    image_url = get_image_url(latest_entry)

    # 讀取上次發送過的紀錄
    last_link = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_link = f.read().strip()

    # 偵錯資訊
    print(f"最新情報連結: {latest_link}")
    print(f"上次紀錄連結: {last_link}")

    if latest_link != last_link:
        print(f"發現新情報！標題：{latest_title}")
        
        embed = {
            "title": "🏮 《燕雲十六聲》最新情報",
            "url": latest_link,
            "description": (
                "「老大，我又給你帶來新消息了，說好要給我松子糖的，你該不會又忘記了吧？🍬」\n\n"
                f"**新公告**\n\n{latest_title}"
            ),
            "color": 15548997,
            "footer": { "text": "紅線特派員 · 期待松子糖中" },
            "timestamp": latest_entry.get('published', '') 
        }

        if image_url:
            embed["image"] = {"url": image_url}

        payload = {
            "username": "搖紅女俠",
            "embeds": [embed]
        }
        
        res = requests.post(DISCORD_WEBHOOK, json=payload)
        
        # 修正：Discord 成功狀態碼可能是 200 或 204
        if res.status_code in [200, 204]:
            print("紅線任務完成！Discord 已成功接收。")
            with open(DB_FILE, "w") as f:
                f.write(latest_link)
        else:
            print(f"紅線在半路跌倒了，Discord 錯誤碼：{res.status_code}")
            print(f"回應內容：{res.text}")
    else:
        print("目前平安無事，繼續等糖吃。")

if __name__ == "__main__":
    check_updates()
