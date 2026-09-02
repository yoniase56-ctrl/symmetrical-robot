from datetime import datetime, timedelta, timezone
import math
import os
import requests

# 1. API Keys & Configurations
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}

# Top 6 European Competitions
COMPETITIONS = ["CL", "PL", "PD", "SA", "BL1", "FL1"]

# Top European Clubs List
FAMOUS_TEAMS = [
    "Manchester City",
    "Arsenal",
    "Liverpool",
    "Manchester United",
    "Chelsea",
    "Tottenham",
    "Aston Villa",
    "Newcastle",
    "Real Madrid",
    "Barcelona",
    "Atlético Madrid",
    "Real Sociedad",
    "Athletic Club",
    "Sevilla",
    "Bayern München",
    "Borussia Dortmund",
    "Bayer Leverkusen",
    "RB Leipzig",
    "Eintracht Frankfurt",
    "Inter",
    "Milan",
    "Juventus",
    "Napoli",
    "Roma",
    "Lazio",
    "Atalanta",
    "Paris Saint-Germain",
    "Monaco",
    "Marseille",
    "Lyon",
    "Lille",
]


# 2. Poisson Distribution Model
def poisson_pmf(lam, k):
    return (math.exp(-lam) * (lam**k)) / math.factorial(k)


def calculate_prediction(home_xg=1.70, away_xg=1.20):
    home_win, draw, away_win = 0.0, 0.0, 0.0
    over_2_5 = 0.0
    btts = 0.0

    for h in range(6):
        for a in range(6):
            prob = poisson_pmf(home_xg, h) * poisson_pmf(away_xg, a)
            if h > a:
                home_win += prob
            elif h == a:
                draw += prob
            else:
                away_win += prob

            if (h + a) > 2.5:
                over_2_5 += prob
            if h > 0 and a > 0:
                btts += prob

    probs = {"Home Win": home_win, "Draw": draw, "Away Win": away_win}
    best_pick = max(probs, key=probs.get)
    return (
        best_pick,
        probs[best_pick] * 100,
        over_2_5 * 100,
        btts * 100,
    )


# 3. Send Message to Telegram
def send_telegram_message(text):
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    max_len = 4000
    for i in range(0, len(text), max_len):
        chunk = text[i : i + max_len]
        payload = {
            "chat_id": TELEGRAM_CHANNEL_ID,
            "text": chunk,
            "parse_mode": "HTML",
        }
        res = requests.post(tg_url, json=payload, timeout=10)
        if res.status_code != 200:
            print(f"Telegram Error: {res.text}")
        else:
            print("Telegram Message Sent Successfully!")


# 4. Fetch Matches
def fetch_matches(date_from, date_to):
    matches = []
    for comp in COMPETITIONS:
        url = f"https://api.football-data.org/v4/competitions/{comp}/matches?dateFrom={date_from}&dateTo={date_to}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                data = res.json()
                competition_name = data.get("competition", {}).get(
                    "name", "Europe"
                )

                for match in data.get("matches", []):
                    home = match["homeTeam"]["name"]
                    away = match["awayTeam"]["name"]

                    is_famous = any(
                        team.lower() in home.lower()
                        or team.lower() in away.lower()
                        for team in FAMOUS_TEAMS
                    )

                    if is_famous or comp == "CL":
                        matches.append(
                            {
                                "competition": competition_name,
                                "home": home,
                                "away": away,
                                "date": match["utcDate"][:10],
                                "time": match["utcDate"][11:16] + " UTC",
                            }
                        )
            else:
                print(f"API Error {comp}: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"Fetch Error: {e}")

    matches.sort(key=lambda x: (x["date"], x["time"]))
    return matches


# 5. Main Execution
def main():
    now = datetime.now(timezone.utc)
    is_monday = now.weekday() == 0

    if is_monday:
        # On Mondays: Look ahead 7 days
        date_from = now.strftime("%Y-%m-%d")
        date_to = (now + timedelta(days=6)).strftime("%Y-%m-%d")
        header = f"🗓️ <b>WEEKLY EUROPEAN FOOTBALL PREVIEW</b> 🇪🇺\n📅 <i>Week of {date_from} to {date_to}</i>\n\n"
        matches = fetch_matches(date_from, date_to)
    else:
        # First check today
        date_from = now.strftime("%Y-%m-%d")
        date_to = date_from
        matches = fetch_matches(date_from, date_to)

        if matches:
            header = f"⚡ <b>TODAY'S TOP EUROPEAN MATCHES</b> ⚽\n📅 <i>{now.strftime('%d %B %Y')}</i>\n\n"
        else:
            # If no games today, fetch upcoming games for next 4 days!
            date_to = (now + timedelta(days=4)).strftime("%Y-%m-%d")
            matches = fetch_matches(date_from, date_to)
            header = f"🔥 <b>UPCOMING TOP EUROPEAN MATCHES</b> ⚽\n📅 <i>Next 4 Days ({date_from} - {date_to})</i>\n\n"

    if not matches:
        # Fallback test message so your channel always verifies connection
        test_msg = "🤖 <b>Sheger Football AI Bot is Online! 🇪🇹⚽</b>\n\nNo European matches scheduled for today. Regular predictions will post before upcoming matchdays!"
        send_telegram_message(test_msg)
        return

    message = header
    current_date = ""

    for m in matches[:8]:  # Limit to top 8 matches to keep it clean
        if m["date"] != current_date:
            current_date = m["date"]
            message += f"\n📆 <b>--- {current_date} ---</b>\n"

        pick, pick_prob, over_prob, btts_prob = calculate_prediction()

        message += f"🏆 <b>{m['competition']}</b>\n"
        message += f"⚔️ <b>{m['home']} vs {m['away']}</b> ({m['time']})\n"
        message += f"📊 <b>Pick:</b> {pick} ({pick_prob:.0f}%)\n"
        message += (
            f"🎯 <b>Over 2.5:</b> {over_prob:.0f}% | <b>BTTS:</b> {btts_prob:.0f}%\n"
        )
        message += "-----------------------------------\n"

    message += "\n<i>⚠️ Statistical model probabilities. Gamble responsibly.</i>"

    send_telegram_message(message)


if __name__ == "__main__":
    main()
