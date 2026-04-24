import feedparser
import requests
import os

# 從 GitHub Secrets 中讀取環境變數
RSS_URL = os.getenv("FB_RSS_URL")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
DB_FILE = "last_link.txt"

def check_updates():
    print("紅線正在偷偷觀察官網...")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("哎呀，什麼都沒抓到，是不是沒網路了？")
        return

    latest_entry = feed.entries[0]
    latest_link = latest_entry.link
    latest_title = latest_entry.title

    # 讀取上次發送過的紀錄
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_link = f.read().strip()
    else:
        last_link = ""

    # 比對是否有新貼文
    if latest_link != last_link:
        print(f"發現新消息：{latest_title}！趕快去回報！")
        
        # 設定紅線的人設訊息
        persona_content = (
            "老大，我又給你帶來新消息了，說好要給我松子糖的，你該不會又忘記了吧？🍬\n\n"
            f"📜 **【最新情報】：{latest_title}**\n"
            f"🔗 **【傳送門】：** {latest_link}\n\n"
            "**紅線特派員 · 期待松子糖中**"
        )

        payload = {
            "username": "紅線",
            # 如果你有紅線的頭像圖片網址，可以填在下面這行，會更像本人
            # "avatar_url": "https://example.com/hongxian_avatar.png", 
            "content": persona_content
        }
        
        res = requests.post(DISCORD_WEBHOOK, json=payload)
        
        if res.status_code == 204:
            print("消息傳達成功，松子糖穩了！")
            # 更新紀錄檔案
            with open(DB_FILE, "w") as f:
                f.write(latest_link)
        else:
            print(f"發送失敗，老大收不到消息... 錯誤代碼：{res.status_code}")
    else:
        print("官網靜悄悄的，看來可以先去睡一覺...")

if __name__ == "__main__":
    check_updates()
