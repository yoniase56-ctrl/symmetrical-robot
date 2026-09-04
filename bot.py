import os
import random
import requests
from datetime import datetime, timedelta

# Environment variables
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
    future_date = (datetime.utcnow() + timedelta(days=4)).strftime("%Y-%m-%d")
    
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
    home_len = len(home_team)
    away_len = len(away_team)
    home_goals = (home_len % 3)
    away_goals = (away_len % 2)
    
    if home_goals > away_goals:
        tip = f"ድል ለ {home_team} (Home Win)"
        odd = round(random.uniform(1.45, 1.95), 2)
    elif home_goals < away_goals:
        tip = f"ድል ለ {away_team} (Away Win)"
        odd = round(random.uniform(2.10, 3.20), 2)
    else:
        tip = "አቻ (Draw)"
        odd = round(random.uniform(3.00, 3.60), 2)
        
    return home_goals, away_goals, tip, odd

def main():
    print("Bot is starting...")
    matches = get_matches()
    
    if not matches:
        msg = (
            "⚽ <b>ሸገር የኳስ ግምት | ዕለታዊ መረጃ</b> ⚽\n\n"
            "📅 <b>ቀን፦</b> " + datetime.utcnow().strftime("%Y-%m-%d") + "\n\n"
            "ℹ️ <i>በተመረጡት ታላላቅ የአውሮፓ ሊጎች ዛሬ ምንም ጨዋታ የለም። የሚቀጥሉት ጨዋታዎች ሲቃረቡ ትንበያዎች ወዲያውኑ ይለቀቃሉ!</i>\n\n"
            "✅ <b>ሲስተም፦</b> ንቁ እና በተጠንቀቅ ላይ ነው!\n"
            "📢 <b>ቻናል፦</b> @shegerpridict"
        )
        send_telegram_message(msg)
        return

    message = "🔥 <b>ሸገር የኳስ ግምት | የጨዋታ ትንበያዎች & የ 10 ብር ትርፍ</b> 🔥\n\n"
    
    total_odds = 1.0
    selected_matches = matches[:5] # ከፍተኛ 5ቱን ጨዋታዎች ይመርጣል
    
    for match in selected_matches:
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        h_g, a_g, tip, odd = generate_prediction(home, away)
        
        # የ 10 ብር ትርፍ ስሌት
        single_payout = round(10 * odd, 2)
        total_odds *= odd
        
        message += f"⚽ <b>{home} VS {away}</b>\n"
        message += f"📊 <b>ግምት፦</b> {h_g} - {a_g}\n"
        message += f"💡 <b>ምክር፦</b> {tip}\n"
        message += f"💰 <b>ኦድ፦</b> <code>{odd}</code>\n"
        message += f"💵 <b>በ 10 ብር ቢያዝ፦</b> <b>{single_payout:.2f} ብር</b>\n"
        message += "———————————————\n"
        
    # የጥምር ትኬት (Combo Ticket) ስሌት
    total_odds = round(total_odds, 2)
    combo_payout = round(10 * total_odds, 2)
    
    message += "\n🎟 <b>የዕለቱ ባለ 5 ጨዋታ ጥምር ትኬት (Combo)</b> 🎟\n"
    message += f"📈 <b>ጠቅላላ ኦድ (Total Odds)፦</b> <code>{total_odds}</code>\n"
    message += f"🤑 <b>በ 10 ብር ሲመደብ የሚያስገኘው፦</b> <b>{combo_payout:,.2f} ብር</b>\n"
    message += "———————————————\n"
    message += "📢 ተከታተሉን፦ @shegerpridict"
    
    send_telegram_message(message)

if __name__ == "__main__":
    main()
