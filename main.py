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
    # 1. 嘗試從 media_content 抓取
    if 'media_content' in entry and len(entry.media_content) > 0:
        return entry.media_content[0]['url']
    
    # 2. 嘗試從 description 中的 <img> 標籤抓取 (常用於 FB RSS)
    if 'summary' in entry:
        img_match = re.search(r'<img [^>]*src="([^"]+)"', entry.summary)
        if img_match:
            return img_match.group(1)
            
    return None

def check_updates():
    print("紅線特派員出動中...")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("哎呀，情報網斷了，抓不到東西。")
        return

    latest_entry = feed.entries[0]
    latest_link = latest_entry.link
    latest_title = latest_entry.title
    image_url = get_image_url(latest_entry)

    # 讀取上次發送過的紀錄
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_link = f.read().strip()
    else:
        last_link = ""

    if latest_link != last_link:
        print(f"發現新情報！標題：{latest_title}")
        
        # 建立 Discord Embed 結構
        embed = {
            "title": "🏮 《燕雲十六聲》最新情報",
            "url": latest_link,
            "description": (
                "「老大，我又給你帶來新消息了，說好要給我松子糖的，你該不會又忘記了吧？🍬」\n\n"
                f"**新公告**\n\n{latest_title}"
            ),
            "color": 15548997, # 這裡設定左側邊條的顏色 (十六進位紅色)
            "footer": {
                "text": "紅線特派員 · 期待松子糖中"
            },
            "timestamp": latest_entry.get('published', '') # 顯示貼文時間
        }

        # 如果有抓到圖片，就加入 Embed 中
        if image_url:
            embed["image"] = {"url": image_url}

        payload = {
            "username": "紅線",
            "embeds": [embed] # 注意這裡改成了 embeds 陣列
        }
        
        res = requests.post(DISCORD_WEBHOOK, json=payload)
        
        # 修正：Discord 成功狀態碼可能是 200 或 204
        if res.status_code in [200, 204]:
            print("紅線任務完成！")
            with open(DB_FILE, "w") as f: # 確保這行會被執行
                f.write(latest_link)
        else:
            print(f"發送失敗，錯誤碼：{res.status_code}")
    else:
        print("目前平安無事，繼續等糖吃。")

if __name__ == "__main__":
    check_updates()
