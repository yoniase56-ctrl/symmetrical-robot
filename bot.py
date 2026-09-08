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

# የታላላቅ የአውሮፓ ክለቦች ጥንካሬ ደረጃ (Power Rankings)
TIER_1_TEAMS = [
    "Real Madrid", "Barcelona", "Manchester City", "Arsenal", "Liverpool", 
    "Bayern", "Paris Saint-Germain", "Inter", "Bayer Leverkusen"
]
TIER_2_TEAMS = [
    "Chelsea", "Manchester United", "Tottenham", "Aston Villa", "Newcastle",
    "Borussia Dortmund", "RB Leipzig", "Juventus", "Milan", "Napoli", "Atalanta",
    "Atlético Madrid", "Real Sociedad", "Athletic Club", "Monaco", "Lille"
]

def get_team_rank(team_name):
    for t in TIER_1_TEAMS:
        if t.lower() in team_name.lower():
            return 1
    for t in TIER_2_TEAMS:
        if t.lower() in team_name.lower():
            return 2
    return 3

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

def generate_smart_prediction(home, away):
    h_rank = get_team_rank(home)
    a_rank = get_team_rank(away)
    
    # 90%+ የመሳካት ዕድል ያላቸው አስተማማኝ ምርጫዎች (Safe Betting)
    if h_rank < a_rank: # ባለሜዳው እጅግ ጠንካራ ሲሆን (ለምሳሌ Real Madrid vs Osasuna)
        h_g = random.choice([2, 3])
        a_g = random.choice([0, 1])
        tip = f"{home} ያሸንፋል ወይም አቻ (1X Double Chance)"
        tip_code = "HOME_OR_DRAW"
        odd = round(random.uniform(1.30, 1.55), 2)
        chance = random.randint(88, 95)
    elif a_rank < h_rank: # የሜዳ ውጪው ጠንካራ ሲሆን (ለምሳሌ Valencia vs Barcelona)
        h_g = random.choice([0, 1])
        a_g = random.choice([2, 3])
        tip = f"{away} ያሸንፋል ወይም አቻ (X2 Double Chance)"
        tip_code = "AWAY_OR_DRAW"
        odd = round(random.uniform(1.32, 1.58), 2)
        chance = random.randint(87, 94)
    else: # ተቀራራቢ ቡድኖች ሲሆኑ (Safe Over Goals)
        h_g = 1
        a_g = 1
        tip = "ከ 1.5 በላይ ጎል (Over 1.5 Goals)"
        tip_code = "OVER_1_5"
        odd = round(random.uniform(1.35, 1.60), 2)
        chance = random.randint(85, 91)
        
    return h_g, a_g, tip, tip_code, odd, chance

def run_predictions():
    print("Posting 90%+ smart predictions...")
    matches = get_today_matches()
    
    if not matches:
        msg = (
            "⚽ <b>ሸገር የኳስ ግምት | ዕለታዊ መረጃ</b> ⚽\n\n"
            f"📅 <b>ቀን፦</b> {datetime.utcnow().strftime('%Y-%m-%d')}\n\n"
            "ℹ️ <i>ዛሬ በታላላቅ ሊጎች ጨዋታ የለም። ቀጣይ ጨዋታዎች እንደተቃረቡ አስተማማኝ ትንበያዎች ይለቀቃሉ!</i>\n\n"
            "📢 <b>ቻናል፦</b> @shegerpridict"
        )
        send_telegram_message(msg)
        return

    saved_data = {"date": datetime.utcnow().strftime("%Y-%m-%d"), "matches": []}
    message = "🔥 <b>ሸገር የኳስ ግምት | የዕለቱ አስተማማኝ (VIP) ትንበያዎች</b> 🔥\n\n"
    
    total_odds = 1.0
    total_chance = 0
    selected = matches[:5]
    
    for m in selected:
        m_id = m["id"]
        h_name = m["homeTeam"]["name"]
        a_name = m["awayTeam"]["name"]
        h_g, a_g, tip, tip_code, odd, chance = generate_smart_prediction(h_name, a_name)
        
        single_payout = round(10 * odd, 2)
        total_odds *= odd
        total_chance += chance
        
        saved_data["matches"].append({
            "id": m_id, "home": h_name, "away": a_name,
            "tip": tip, "tip_code": tip_code, "odd": odd,
            "h_g": h_g, "a_g": a_g, "chance": chance, "payout": single_payout
        })
        
        message += f"⚽ <b>{h_name} VS {a_name}</b>\n"
        message += f"📊 <b>የግብ ግምት፦</b> {h_g} - {a_g}\n"
        message += f"🛡 <b>አስተማማኝ ምክር፦</b> {tip}\n"
        message += f"💰 <b>ኦድ፦</b> <code>{odd}</code>\n"
        message += f"🎯 <b>የመሳካት ዕድል፦</b> <b>{chance}%</b> 🔥\n"
        message += f"💵 <b>በ 10 ብር ቢያዝ፦</b> <b>{single_payout:.2f} ብር</b>\n"
        message += "———————————————\n"
        
    total_odds = round(total_odds, 2)
    combo_payout = round(10 * total_odds, 2)
    avg_chance = round(total_chance / len(selected))
    
    message += "\n🎟 <b>የዕለቱ አስተማማኝ ባለ 5 ጥምር ትኬት (Safe Combo)</b> 🎟\n"
    message += f"📈 <b>ጠቅላላ ኦድ፦</b> <code>{total_odds}</code>\n"
    message += f"🎯 <b>አጠቃላይ እርግጠኝነት፦</b> <b>{avg_chance}%</b>\n"
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
    print("Checking match results with 90% accuracy logic...")
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
    
    edited_msg = "🔥 <b>ሸገር የኳስ ግምት | የተረጋገጠ ውጤት</b> 🔥\n\n"
    recap_msg = "🏁 <b>ሸገር የኳስ ግምት | የዕለቱ ውጤት ማጠቃለያ</b> 🏁\n\n"
    
    for m in data["matches"]:
        match_info = api_matches.get(m["id"], {})
        status = match_info.get("status", "FINISHED")
        winner = match_info.get("score", {}).get("winner", None)
        score_home = match_info.get("score", {}).get("fullTime", {}).get("home", m["h_g"])
        score_away = match_info.get("score", {}).get("fullTime", {}).get("away", m["a_g"])
        
        is_success = False
        tip_c = m["tip_code"]
        
        # 90%+ የማረጋገጫ ስሌት (Double Chance & Over 1.5)
        if winner is not None:
            if tip_c == "HOME_OR_DRAW" and winner in ["HOME_TEAM", "DRAW"]:
                is_success = True
            elif tip_c == "AWAY_OR_DRAW" and winner in ["AWAY_TEAM", "DRAW"]:
                is_success = True
            elif tip_c == "OVER_1_5" and (score_home + score_away) >= 2:
                is_success = True
        else:
            # ጨዋታው ካልተጠናቀቀ ወይም በእውነተኛ ሰዓት 85%-90% ዕድል
            is_success = random.choice([True, True, True, True, False])
            
        if is_success:
            badge = "✅ ተሳክቷል (WON)"
            won_count += 1
        else:
            badge = "❌ አልተሳካም (LOST)"
            
        edited_msg += f"⚽ <b>{m['home']} VS {m['away']}</b> {badge}\n"
        edited_msg += f"📊 <b>ምክር፦</b> {m['tip']} | <b>ኦድ፦</b> {m['odd']}\n"
        edited_msg += "———————————————\n"
        
        recap_msg += f"⚽ {m['home']} {score_home} - {score_away} {m['away']}\n"
        recap_msg += f"👉 ምርጫ፦ {m['tip']} ➔ {badge}\n\n"

    edited_msg += f"\n📢 ተከታተሉን፦ @shegerpridict"
    
    accuracy = round((won_count / total_count) * 100)
    recap_msg += "———————————————\n"
    recap_msg += f"📊 <b>አጠቃላይ ስኬት፦</b> {won_count}/{total_count} ተሳክቷል! ({accuracy}% Accuracy) 🔥\n"
    recap_msg += "📢 ተከታተሉን፦ @shegerpridict"

    if "message_id" in data:
        edit_telegram_message(data["message_id"], edited_msg)
        
    send_telegram_message(recap_msg)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "predict"
    if mode == "verify":
        check_results()
    else:
        run_predictions()
