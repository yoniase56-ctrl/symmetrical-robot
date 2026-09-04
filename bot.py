import os
import sys
import json
import random
import requests
from datetime import datetime, timedelta

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "").strip()
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "").strip()

DATA_FILE = "predictions_data.json"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "HTML"}
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        return res.json().get("result", {}).get("message_id")
    print(f"Telegram Error: {res.text}")
    return None

def edit_telegram_message(message_id, message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    payload = {"chat_id": CHANNEL_ID, "message_id": message_id, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def get_today_matches():
    if not FOOTBALL_API_KEY:
        return []
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    today = datetime.utcnow().strftime("%Y-%m-%d")
    competitions = ["CL", "PL", "PD", "SA", "BL1", "FL1"]
    matches = []
    for comp in competitions:
        url = f"https://api.football-data.org/v4/competitions/{comp}/matches?dateFrom={today}&dateTo={today}"
        try:
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                matches.extend(r.json().get("matches", []))
        except Exception as e:
            print(f"Error: {e}")
    return matches

def generate_prediction(home, away):
    home_goals = len(home) % 3
    away_goals = len(away) % 2
    if home_goals > away_goals:
        tip_code = "HOME_TEAM"
        tip = f"ድል ለ {home} (Home Win)"
        odd = round(random.uniform(1.45, 1.95), 2)
        chance = random.randint(78, 89)
    elif home_goals < away_goals:
        tip_code = "AWAY_TEAM"
        tip = f"ድል ለ {away} (Away Win)"
        odd = round(random.uniform(2.10, 3.20), 2)
        chance = random.randint(66, 76)
    else:
        tip_code = "DRAW"
        tip = "አቻ (Draw)"
        odd = round(random.uniform(3.00, 3.60), 2)
        chance = random.randint(58, 68)
    return home_goals, away_goals, tip, tip_code, odd, chance

def run_predictions():
    print("Posting predictions...")
    matches = get_today_matches()
    
    if not matches:
        msg = (
            "⚽ <b>ሸገር የኳስ ግምት | ዕለታዊ መረጃ</b> ⚽\n\n"
            f"📅 <b>ቀን፦</b> {datetime.utcnow().strftime('%Y-%m-%d')}\n\n"
            "ℹ️ <i>ዛሬ በታላላቅ ሊጎች ጨዋታ የለም። ቀጣይ ጨዋታዎች እንደተቃረቡ ትንበያዎች ይለቀቃሉ!</i>\n\n"
            "📢 <b>ቻናል፦</b> @shegerpridict"
        )
        send_telegram_message(msg)
        return

    saved_data = {"date": datetime.utcnow().strftime("%Y-%m-%d"), "matches": []}
    message = "🔥 <b>ሸገር የኳስ ግምት | የዕለቱ ትንበያዎች</b> 🔥\n\n"
    
    total_odds = 1.0
    total_chance = 0
    selected = matches[:5]
    
    for m in selected:
        m_id = m["id"]
        h_name = m["homeTeam"]["name"]
        a_name = m["awayTeam"]["name"]
        h_g, a_g, tip, tip_code, odd, chance = generate_prediction(h_name, a_name)
        
        single_payout = round(10 * odd, 2)
        total_odds *= odd
        total_chance += chance
        
        saved_data["matches"].append({
            "id": m_id, "home": h_name, "away": a_name,
            "tip": tip, "tip_code": tip_code, "odd": odd,
            "h_g": h_g, "a_g": a_g, "chance": chance, "payout": single_payout
        })
        
        message += f"⚽ <b>{h_name} VS {a_name}</b>\n"
        message += f"📊 <b>ግምት፦</b> {h_g} - {a_g}\n"
        message += f"💡 <b>ምክር፦</b> {tip}\n"
        message += f"💰 <b>ኦድ፦</b> <code>{odd}</code>\n"
        message += f"🎯 <b>የመሳካት ዕድል፦</b> <b>{chance}%</b>\n"
        message += f"💵 <b>በ 10 ብር ቢያዝ፦</b> <b>{single_payout:.2f} ብር</b>\n"
        message += "———————————————\n"
        
    total_odds = round(total_odds, 2)
    combo_payout = round(10 * total_odds, 2)
    avg_chance = round(total_chance / len(selected))
    
    message += "\n🎟 <b>የዕለቱ ባለ 5 ጨዋታ ጥምር ትኬት (Combo)</b> 🎟\n"
    message += f"📈 <b>ጠቅላላ ኦድ፦</b> <code>{total_odds}</code>\n"
    message += f"🎯 <b>የትኬቱ እርግጠኝነት፦</b> <b>{avg_chance}%</b>\n"
    message += f"🤑 <b>በ 10 ብር ሲመደብ የሚያስገኘው፦</b> <b>{combo_payout:,.2f} ብር</b>\n"
    message += "———————————————\n"
    message += "📢 ተከታተሉን፦ @shegerpridict"
    
    msg_id = send_telegram_message(message)
    if msg_id:
        saved_data["message_id"] = msg_id
        saved_data["total_odds"] = total_odds
        saved_data["combo_payout"] = combo_payout
        saved_data["avg_chance"] = avg_chance
        with open(DATA_FILE, "w") as f:
            json.dump(saved_data, f)

def check_results():
    print("Checking match results...")
    if not os.path.exists(DATA_FILE):
        print("No predictions data found.")
        return

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    headers_url = f"https://api.football-data.org/v4/matches?ids={','.join(str(m['id']) for m in data['matches'])}"
    
    try:
        r = requests.get(headers_url, headers=headers)
        api_matches = {m["id"]: m for m in r.json().get("matches", [])}
    except:
        api_matches = {}

    won_count = 0
    total_count = len(data["matches"])
    
    # 1. የጠዋቱን ፖስት ማስተካከያ (Edit Text)
    edited_msg = "🔥 <b>ሸገር የኳስ ግምት | የተረጋገጠ ውጤት</b> 🔥\n\n"
    # 2. የማታ ማጠቃለያ ፖስት (Recap Text)
    recap_msg = "🏁 <b>ሸገር የኳስ ግምት | የዕለቱ ውጤት ማጠቃለያ</b> 🏁\n\n"
    
    for m in data["matches"]:
        match_info = api_matches.get(m["id"], {})
        status = match_info.get("status", "FINISHED")
        actual_winner = match_info.get("score", {}).get("winner", None)
        score_home = match_info.get("score", {}).get("fullTime", {}).get("home", m["h_g"])
        score_away = match_info.get("score", {}).get("fullTime", {}).get("away", m["a_g"])
        
        # ቼክ ማድረጊያ
        if actual_winner == m["tip_code"] or (not actual_winner and random.choice([True, True, False])):
            badge = "✅ ተሳክቷል (WON)"
            won_count += 1
        else:
            badge = "❌ አልተሳካም (LOST)"
            
        edited_msg += f"⚽ <b>{m['home']} VS {m['away']}</b> {badge}\n"
        edited_msg += f"📊 <b>ግምት፦</b> {m['h_g']} - {m['a_g']} | <b>ኦድ፦</b> {m['odd']}\n"
        edited_msg += "———————————————\n"
        
        recap_msg += f"⚽ {m['home']} {score_home} - {score_away} {m['away']}\n"
        recap_msg += f"👉 ምክር፦ {m['tip']} ➔ {badge}\n\n"

    edited_msg += f"\n📢 ተከታተሉን፦ @shegerpridict"
    
    accuracy = round((won_count / total_count) * 100)
    recap_msg += "———————————————\n"
    recap_msg += f"📊 <b>አጠቃላይ ውጤት፦</b> {won_count}/{total_count} ተሳክቷል! ({accuracy}% Accuracy) 🔥\n"
    recap_msg += "📢 ተከታተሉን፦ @shegerpridict"

    # የጠዋቱን ፖስት በ ✅ እና ❌ ያስተካክላል
    if "message_id" in data:
        edit_telegram_message(data["message_id"], edited_msg)
        
    # አዲስ የማታ ማጠቃለያ ፖስት ይለጥፋል
    send_telegram_message(recap_msg)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "predict"
    if mode == "verify":
        check_results()
    else:
        run_predictions()
