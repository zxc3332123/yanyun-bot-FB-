import feedparser
import requests
import os
import re
from datetime import datetime

RSS_URL = os.getenv("FB_RSS_URL")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
DB_FILE = "last_link.txt"

if not RSS_URL or not DISCORD_WEBHOOK:
    raise ValueError("環境變數 FB_RSS_URL 或 DISCORD_WEBHOOK 未設定！")

def get_image_url(entry):
    if 'media_content' in entry and len(entry.media_content) > 0:
        return entry.media_content[0]['url']
    if 'summary' in entry:
        img_match = re.search(r'<img [^>]*src="([^"]+)"', entry.summary)
        if img_match:
            return img_match.group(1)
    return None

def check_updates():
    print("紅線特派員出動中...")
    
    try:
        feed = feedparser.parse(RSS_URL)
    except Exception as e:
        print(f"RSS 抓取失敗：{e}")
        return

    if not feed.entries:
        print("哎呀，情報網斷了，抓不到東西。")
        return

    latest_entry = feed.entries[0]
    latest_link = latest_entry.link
    latest_title = latest_entry.title
    image_url = get_image_url(latest_entry)

    last_link = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_link = f.read().strip()

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
            "footer": {"text": "紅線特派員 · 期待松子糖中"},
        }

        # 安全處理 timestamp
        published = latest_entry.get('published_parsed')
        if published:
            embed["timestamp"] = datetime(*published[:6]).strftime("%Y-%m-%dT%H:%M:%S")

        if image_url:
            embed["image"] = {"url": image_url}

        payload = {"username": "搖紅女俠", "embeds": [embed]}

        try:
            res = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
            if res.status_code in [200, 204]:
                print("紅線任務完成！")
                with open(DB_FILE, "w") as f:
                    f.write(latest_link)
            else:
                print(f"發送失敗，錯誤碼：{res.status_code}，回應：{res.text}")
        except requests.RequestException as e:
            print(f"Discord 發送異常：{e}")
    else:
        print("目前平安無事，繼續等糖吃。")

if __name__ == "__main__":
    check_updates()
