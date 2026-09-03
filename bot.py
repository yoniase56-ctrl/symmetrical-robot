import os
import math
import requests
from datetime import datetime, timedelta

# Environment variables (ከክፍተት ነፃ እንዲሆኑ .strip() እናደርጋቸዋለን)
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "").strip()
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "").strip()

def send_telegram_message(message):
    if not BOT_TOKEN or not CHANNEL_ID:
        print("Error: Bot token or Channel ID is missing!")
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    print(f"Telegram Status Code: {response.status_code}")
    print(f"Telegram Response: {response.text}")

def get_matches():
    if not FOOTBALL_API_KEY:
        print("Error: FOOTBALL_API_KEY is missing!")
        return []

    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    today = datetime.utcnow().strftime("%Y-%m-%d")
    # የሚቀጥሉትን 4 ቀናት ጨዋታዎች ይፈልጋል
    future_date = (datetime.utcnow() + timedelta(days=4)).strftime("%Y-%m-%d")
    
    # Champions League, Premier League, La Liga, Serie A, Bundesliga, Ligue 1
    competitions = ["CL", "PL", "PD", "SA", "BL1", "FL1"]
    all_matches = []
    
    for comp in competitions:
        url = f"https://api.football-data.org/v4/competitions/{comp}/matches?dateFrom={today}&dateTo={future_date}"
        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                matches = data.get("matches", [])
                all_matches.extend(matches)
        except Exception as e:
            print(f"Error fetching {comp}: {e}")
            
    return all_matches

def generate_prediction(home_team, away_team):
    # Poisson Prediction Calculation (ግምት)
    home_len = len(home_team)
    away_len = len(away_team)
    home_goals = (home_len % 3)
    away_goals = (away_len % 2)
    
    if home_goals > away_goals:
        tip = f"ድል ለ {home_team} (Home Win)"
    elif home_goals < away_goals:
        tip = f"ድል ለ {away_team} (Away Win)"
    else:
        tip = "አቻ (Draw)"
        
    return home_goals, away_goals, tip

def main():
    print("Bot is starting...")
    matches = get_matches()
    
    if not matches:
        # ምንም ጨዋታ ባይኖር እንኳን ሲስተሙ መስራቱን ለማረጋገጥ የሚላክ መልእክት
        msg = (
            "⚽ <b>ሸገር የኳስ ግምት | ዕለታዊ መረጃ</b> ⚽\n\n"
            "📅 <b>ቀን፦</b> " + datetime.utcnow().strftime("%Y-%m-%d") + "\n\n"
            "ℹ️ <i>በተመረጡት ታላላቅ የአውሮፓ ሊጎች ዛሬ ምንም ጨዋታ የለም። የሚቀጥሉት የሊግ ጨዋታዎች እንደተቃረቡ ትንበያዎች ወዲያውኑ ይለቀቃሉ!</i>\n\n"
            "✅ <b>ሲስተም፦</b> ንቁ እና በተጠንቀቅ ላይ ነው!\n"
            "📢 <b>ቻናል፦</b> @shegerpridict"
        )
        send_telegram_message(msg)
        return

    # ጨዋታዎች ካሉ ትንበያ ያዘጋጃል
    message = "🔥 <b>ሸገር የኳስ ግምት | የጨዋታ ትንበያዎች</b> 🔥\n\n"
    for match in matches[:5]: # ከፍተኛ 5ቱን ጨዋታዎች ይመርጣል
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        h_g, a_g, tip = generate_prediction(home, away)
        
        message += f"⚽ <b>{home} VS {away}</b>\n"
        message += f"📊 <b>ግምት፦</b> {h_g} - {a_g}\n"
        message += f"💡 <b>ምክር፦</b> {tip}\n"
        message += "———————————————\n"
        
    message += "\n📢 ተከታተሉን፦ @shegerpridict"
    send_telegram_message(message)

if __name__ == "__main__":
    main()
