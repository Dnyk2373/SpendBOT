"""
SpendBot AI - Standalone Monthly Expense Tracker & Budget Analyst
Supports both an interactive conversational CLI chatbot and a full-featured Flask Web Server.
Automatically synchronizes expenses and budgets across your Laptop and Phone over Wi-Fi or Cloud.
"""

import sys
import os
import re
import sqlite3
import datetime
import json
import socket
from typing import Dict, Any, List, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "expenses.db")
HTML_FILE = os.path.join(os.path.dirname(__file__), "expense_tracker_chatbot.html")

DEFAULT_CATEGORIES = {
    "housing": {"name": "Housing & Rent", "budget": 1100.0, "icon": "🏠", "type": "need"},
    "groceries": {"name": "Groceries", "budget": 400.0, "icon": "🛒", "type": "need"},
    "utilities": {"name": "Utilities & Bills", "budget": 200.0, "icon": "⚡", "type": "need"},
    "transport": {"name": "Transportation", "budget": 150.0, "icon": "🚗", "type": "need"},
    "dining": {"name": "Dining Out & Food", "budget": 300.0, "icon": "🍔", "type": "want"},
    "entertainment": {"name": "Entertainment", "budget": 150.0, "icon": "🎬", "type": "want"},
    "shopping": {"name": "Shopping & Gear", "budget": 250.0, "icon": "🛍️", "type": "want"},
    "healthcare": {"name": "Healthcare & Fitness", "budget": 150.0, "icon": "💊", "type": "need"},
    "subscriptions": {"name": "Subscriptions", "budget": 100.0, "icon": "📱", "type": "want"},
    "other": {"name": "Miscellaneous", "budget": 100.0, "icon": "📦", "type": "want"}
}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            category TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            budget REAL NOT NULL,
            icon TEXT,
            color TEXT,
            cat_type TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            time TEXT,
            card_html TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Populate default budgets if empty
    c.execute("SELECT COUNT(*) FROM budgets")
    if c.fetchone()[0] == 0:
        colors = {
            "housing": "#6366f1", "groceries": "#10b981", "utilities": "#06b6d4",
            "transport": "#3b82f6", "dining": "#f59e0b", "entertainment": "#ec4899",
            "shopping": "#8b5cf6", "healthcare": "#14b8a6", "subscriptions": "#f43f5e", "other": "#64748b"
        }
        for cat_id, data in DEFAULT_CATEGORIES.items():
            c.execute(
                "INSERT INTO budgets (category, name, budget, icon, color, cat_type) VALUES (?, ?, ?, ?, ?, ?)",
                (cat_id, data["name"], data["budget"], data["icon"], colors.get(cat_id, "#64748b"), data["type"])
            )
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('monthly_income', '4000.0')")
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('currency', '$')")
        conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_FILE)

def get_local_ip() -> str:
    """Detects local LAN IP for easy phone connection."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def parse_expense(text: str) -> Optional[Dict[str, Any]]:
    amt_match = re.search(r'(?:[$€£₹¥])?\s*(\d+(?:\.\d{1,2})?)\s*(?:dollars|bucks|usd|eur|gbp|inr)?', text, re.I)
    if not amt_match:
        return None
    try:
        amount = float(amt_match.group(1))
    except ValueError:
        return None
    if amount <= 0:
        return None

    lower = text.lower()
    cat = "other"
    if re.search(r'grocer|supermarket|trader joe|whole foods|walmart|produce|milk|bread|food store', lower):
        cat = "groceries"
    elif re.search(r'dinner|lunch|breakfast|restaurant|dining|sushi|pizza|burger|cafe|coffee|starbucks|chipotle|drinks|bar', lower):
        cat = "dining"
    elif re.search(r'rent|mortgage|apartment|lease|housing', lower):
        cat = "housing"
    elif re.search(r'electric|electricity|utility|utilities|water|gas bill|power|wifi|internet|cable|phone bill', lower):
        cat = "utilities"
    elif re.search(r'uber|lyft|taxi|gas|gasoline|fuel|metro|subway|bus|transit|parking|car', lower):
        cat = "transport"
    elif re.search(r'movie|cinema|theatre|concert|game|gaming|steam|playstation|xbox|bowling|ticket', lower):
        cat = "entertainment"
    elif re.search(r'clothes|clothing|shoes|jacket|shirt|shopping|amazon|target|electronics|gadget|mall', lower):
        cat = "shopping"
    elif re.search(r'doctor|medicine|pharmacy|clinic|dental|dentist|hospital|gym|fitness|vitamin', lower):
        cat = "healthcare"
    elif re.search(r'netflix|spotify|hulu|disney|apple|youtube|icloud|subscription|patreon', lower):
        cat = "subscriptions"

    clean_desc = re.sub(r'spent|paid|bought|cost|purchased|for|on|at|an|a', '', text, flags=re.I)
    clean_desc = re.sub(r'(?:[$€£₹¥])?\s*\d+(?:\.\d{1,2})?\s*(?:dollars|bucks|usd|eur|gbp|inr)?', '', clean_desc, flags=re.I).strip()
    if not clean_desc:
        clean_desc = f"{DEFAULT_CATEGORIES.get(cat, {}).get('name', 'Expense')} Purchase"
    else:
        clean_desc = clean_desc[0].upper() + clean_desc[1:]

    date_str = datetime.date.today().isoformat()
    if "yesterday" in lower:
        date_str = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

    return {
        "id": "tx_" + str(int(datetime.datetime.now().timestamp() * 1000)),
        "amount": amount,
        "category": cat,
        "description": clean_desc,
        "date": date_str
    }

def add_expense(tx_id: str, date: str, description: str, category: str, amount: float):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO expenses (id, date, description, category, amount) VALUES (?, ?, ?, ?, ?)",
        (tx_id, date, description, category, amount)
    )
    conn.commit()
    conn.close()

def get_analytics(month_str: Optional[str] = None) -> Dict[str, Any]:
    if not month_str:
        month_str = datetime.date.today().strftime("%Y-%m")

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT category, name, budget, icon, color, cat_type FROM budgets")
    budgets = {row[0]: {"name": row[1], "budget": row[2], "icon": row[3], "color": row[4], "type": row[5]} for row in c.fetchall()}

    c.execute("SELECT category, SUM(amount) FROM expenses WHERE date LIKE ? GROUP BY category", (f"{month_str}%",))
    spent_by_cat = {row[0]: row[1] for row in c.fetchall()}

    total_budget = sum(b["budget"] for b in budgets.values())
    total_spent = sum(spent_by_cat.values())
    remaining = total_budget - total_spent

    overspent = []
    warning = []
    for cat_id, b in budgets.items():
        s = spent_by_cat.get(cat_id, 0.0)
        ratio = (s / b["budget"]) if b["budget"] > 0 else (2.0 if s > 0 else 0.0)
        if s > b["budget"]:
            overspent.append({
                "category": cat_id,
                "name": b["name"],
                "icon": b["icon"],
                "spent": s,
                "budget": b["budget"],
                "over": s - b["budget"],
                "pct": ratio * 100
            })
        elif ratio >= 0.75:
            warning.append({
                "category": cat_id,
                "name": b["name"],
                "icon": b["icon"],
                "spent": s,
                "budget": b["budget"],
                "remaining": b["budget"] - s,
                "pct": ratio * 100
            })

    today = datetime.date.today()
    day_of_month = today.day if today.strftime("%Y-%m") == month_str else 30
    burn_rate = total_spent / day_of_month if day_of_month > 0 else 0.0
    projected_total = burn_rate * 30
    conn.close()

    return {
        "month": month_str,
        "total_budget": total_budget,
        "total_spent": total_spent,
        "remaining": remaining,
        "spent_by_cat": spent_by_cat,
        "budgets": budgets,
        "overspent": overspent,
        "warning": warning,
        "burn_rate": burn_rate,
        "projected_total": projected_total
    }

def plan_50_30_20(income: float) -> Dict[str, Any]:
    needs = income * 0.50
    wants = income * 0.30
    savings = income * 0.20

    allocations = {
        "housing": round(needs * 0.55, 2),
        "groceries": round(needs * 0.20, 2),
        "utilities": round(needs * 0.10, 2),
        "transport": round(needs * 0.08, 2),
        "healthcare": round(needs * 0.07, 2),
        "dining": round(wants * 0.35, 2),
        "shopping": round(wants * 0.25, 2),
        "entertainment": round(wants * 0.20, 2),
        "subscriptions": round(wants * 0.10, 2),
        "other": round(wants * 0.10, 2),
    }

    conn = get_db()
    c = conn.cursor()
    for cat_id, amt in allocations.items():
        c.execute("UPDATE budgets SET budget = ? WHERE category = ?", (amt, cat_id))
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('monthly_income', ?)", (str(income),))
    conn.commit()
    conn.close()

    return {
        "income": income,
        "needs": needs,
        "wants": wants,
        "savings": savings,
        "allocations": allocations
    }

def handle_bot_message(user_input: str) -> str:
    text = user_input.strip()
    lower = text.lower()

    if lower in ["help", "commands"]:
        return (
            "🤖 **SpendBot Capabilities:**\n"
            "• Log expense: 'Spent $45 on groceries', 'Dinner at Chipotle $18.50', 'Gas 40'\n"
            "• Overspending check: 'Am I overspending?', 'Check over budget categories'\n"
            "• Analysis: 'Show spending analysis', 'How much did I spend this month?'\n"
            "• Budget Plan: 'Recommend 50/30/20 budget', 'Plan budget for $4000 income'\n"
            "• Set budget: 'Set dining budget to 250', 'Set groceries budget to 450'\n"
            "• Category status: 'How much did I spend on dining?', 'Groceries status'"
        )

    if any(k in lower for k in ["overspend", "over budget", "exceeded"]):
        analytics = get_analytics()
        if not analytics["overspent"]:
            resp = f"🎉 **Great news!** You haven't exceeded any category budgets this month.\n"
            resp += f"• Total Spent: ${analytics['total_spent']:,.2f} of ${analytics['total_budget']:,.2f}\n"
            resp += f"• Remaining Cushion: ${analytics['remaining']:,.2f}\n"
            if analytics["warning"]:
                resp += "⚠️ Categories nearing limit (>75%): " + ", ".join(f"{c['name']} ({c['pct']:.0f}%)" for c in analytics["warning"])
            return resp

        resp = f"🚨 **Overspending Alert!** You have exceeded your budget in {len(analytics['overspent'])} categories:\n"
        for c in analytics["overspent"]:
            resp += f"• **{c['name']}**: Spent ${c['spent']:,.2f} / ${c['budget']:,.2f} (Over by +${c['over']:,.2f}, {c['pct']:.0f}%)\n"
        resp += f"\nTotal Overspent Deficit: +${sum(c['over'] for c in analytics['overspent']):,.2f}."
        return resp

    if any(k in lower for k in ["analysis", "analyze", "report", "summary", "breakdown"]):
        analytics = get_analytics()
        pct = (analytics['total_spent'] / analytics['total_budget'] * 100) if analytics['total_budget'] > 0 else 0
        resp = (
            f"📊 **Monthly Budget & Spending Analysis:**\n"
            f"• Total Budget: ${analytics['total_budget']:,.2f}\n"
            f"• Total Spent: ${analytics['total_spent']:,.2f} ({pct:.1f}% utilized)\n"
            f"• Remaining: ${analytics['remaining']:,.2f}\n"
            f"• Daily Burn Rate: ${analytics['burn_rate']:,.2f}/day (Projected: ${analytics['projected_total']:,.2f})\n\n"
            f"🏆 **Top Spending Breakdown:**\n"
        )
        sorted_cats = sorted(analytics["spent_by_cat"].items(), key=lambda x: x[1], reverse=True)[:5]
        for cat_id, spent in sorted_cats:
            cat_name = analytics["budgets"].get(cat_id, {}).get("name", cat_id.title())
            resp += f"• {cat_name}: ${spent:,.2f}\n"
        return resp

    if "50/30/20" in lower or "plan budget" in lower or "budget plan" in lower:
        income_match = re.search(r'\d+(?:\.\d+)?', text)
        income = float(income_match.group(0)) if income_match else 4000.0
        plan = plan_50_30_20(income)
        return (
            f"🎯 **50/30/20 Budget Plan Applied for ${income:,.2f} Monthly Income:**\n"
            f"• 🏠 **Needs (50%):** ${plan['needs']:,.2f} (Housing, Groceries, Utilities, Transport, Health)\n"
            f"• 🍔 **Wants (30%):** ${plan['wants']:,.2f} (Dining, Shopping, Entertainment, Subscriptions)\n"
            f"• 💰 **Savings & Debt (20%):** ${plan['savings']:,.2f} (Emergency Cushion, Investments)\n"
            f"Category limits have been updated automatically in your database!"
        )

    if lower.startswith("set ") and "budget" in lower:
        amt_match = re.search(r'\d+(?:\.\d+)?', text)
        if amt_match:
            new_budget = float(amt_match.group(0))
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT category, name FROM budgets")
            rows = c.fetchall()
            matched_cat = None
            for cat_id, name in rows:
                if cat_id in lower or any(word in lower for word in name.lower().split() if len(word) > 3):
                    matched_cat = (cat_id, name)
                    break
            if matched_cat:
                c.execute("UPDATE budgets SET budget = ? WHERE category = ?", (new_budget, matched_cat[0]))
                conn.commit()
                conn.close()
                return f"✅ Updated monthly budget for **{matched_cat[1]}** to **${new_budget:,.2f}**!"
            conn.close()

    parsed = parse_expense(text)
    if parsed:
        add_expense(parsed["id"], parsed["date"], parsed["description"], parsed["category"], parsed["amount"])
        analytics = get_analytics()
        cat_info = analytics["budgets"].get(parsed["category"], {"name": parsed["category"].title(), "budget": 0})
        cat_spent = analytics["spent_by_cat"].get(parsed["category"], 0.0)
        is_over = cat_spent > cat_info["budget"]
        return (
            f"✅ **Expense Logged!**\n"
            f"• Description: {parsed['description']}\n"
            f"• Amount: ${parsed['amount']:,.2f} ({cat_info['name']})\n"
            f"• Date: {parsed['date']}\n"
            f"• Status: {f'🚨 Over budget by +${cat_spent - cat_info[\"budget\"]:,.2f}!' if is_over else f'${cat_info[\"budget\"] - cat_spent:,.2f} remaining in category.'}"
        )

    return (
        "I didn't quite catch that. Try:\n"
        "• 'Spent $45 on groceries'\n"
        "• 'Am I overspending?'\n"
        "• 'Show spending analysis'\n"
        "• '50/30/20 budget plan for 4500'"
    )

def interactive_cli():
    print("=" * 60)
    print(" 🤖 SpendBot AI - Monthly Expense & Budget Tracker")
    print(" Type 'help' for commands, or type 'exit' to quit.")
    print("=" * 60)
    init_db()
    while True:
        try:
            user_msg = input("\nYou > ").strip()
            if not user_msg:
                continue
            if user_msg.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
            reply = handle_bot_message(user_msg)
            print(f"\nSpendBot > {reply}")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

def run_flask_server():
    from flask import Flask, request, jsonify, send_file
    app = Flask(__name__)

    @app.route("/")
    def index():
        if os.path.exists(HTML_FILE):
            return send_file(HTML_FILE)
        return "<h3>SpendBot Server running! Put expense_tracker_chatbot.html in the same directory.</h3>"

    @app.route("/api/state", methods=["GET"])
    def get_state():
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, date, description, category, amount FROM expenses ORDER BY date DESC")
        txs = [{"id": r[0], "date": r[1], "description": r[2], "category": r[3], "amount": r[4]} for r in c.fetchall()]

        c.execute("SELECT category, name, budget, icon, color, cat_type FROM budgets")
        cats = [{"id": r[0], "name": r[1], "budget": r[2], "icon": r[3], "color": r[4], "type": r[5]} for r in c.fetchall()]

        c.execute("SELECT key, value FROM settings")
        settings = dict(c.fetchall())
        conn.close()

        return jsonify({
            "transactions": txs,
            "categories": cats,
            "monthlyIncome": float(settings.get("monthly_income", 4000)),
            "currency": settings.get("currency", "$")
        })

    @app.route("/api/state", methods=["POST"])
    def save_state():
        data = request.json or {}
        conn = get_db()
        c = conn.cursor()
        if "monthlyIncome" in data:
            c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('monthly_income', ?)", (str(data["monthlyIncome"]),))
        if "currency" in data:
            c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('currency', ?)", (str(data["currency"]),))
        if "categories" in data:
            for cat in data["categories"]:
                c.execute(
                    "UPDATE budgets SET budget = ? WHERE category = ?",
                    (float(cat.get("budget", 0)), cat["id"])
                )
        if "transactions" in data:
            c.execute("DELETE FROM expenses")
            for tx in data["transactions"]:
                c.execute(
                    "INSERT INTO expenses (id, date, description, category, amount) VALUES (?, ?, ?, ?, ?)",
                    (str(tx.get("id")), tx.get("date"), tx.get("description"), tx.get("category"), float(tx.get("amount", 0)))
                )
        conn.commit()
        conn.close()
        return jsonify({"status": "saved"})

    @app.route("/api/chat", methods=["POST"])
    def api_chat():
        data = request.json or {}
        msg = data.get("message", "")
        reply = handle_bot_message(msg)
        return jsonify({"reply": reply})

    @app.route("/api/analytics", methods=["GET"])
    def api_analytics():
        return jsonify(get_analytics())

    local_ip = get_local_ip()
    port = int(os.environ.get("PORT", 5000))

    print("\n" + "=" * 65)
    print(" 🚀 SpendBot Live Server is Running (Cross-Device Sync)")
    print(f" 💻 On your Laptop:  http://localhost:{port}")
    print(f" 📱 On your Phone:   http://{local_ip}:{port}  (on same Wi-Fi)")
    print("=" * 65 + "\n")

    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    init_db()
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        try:
            run_flask_server()
        except ImportError:
            print("Flask is not installed. Run 'pip install flask' or use interactive CLI mode.")
            interactive_cli()
    else:
        interactive_cli()
