# SpendBot AI - Monthly Expense Tracker & Budget Analyst

SpendBot is an intelligent financial chatbot that tracks your monthly expenses, facilitates smart 50/30/20 budget planning, and performs real-time overspending and spending burn-rate analysis.

## Features

- **Natural Language Expense Logging:** Log transactions naturally like `"Spent $45 on groceries"`, `"Dinner at Chipotle 18.50"`, or `"Paid electric bill $120"`.
- **Smart Category Auto-Detection:** Automatically maps transactions to Housing, Groceries, Utilities, Transport, Dining Out, Entertainment, Shopping, Healthcare, Subscriptions, and Miscellaneous.
- **Budget Planning (50/30/20 Rule):** Auto-calculates and allocates your monthly take-home income into 50% Needs, 30% Wants, and 20% Savings/Debt.
- **Overspending & Budget Analysis:**
  - Instantly checks if any category exceeded 100% of its budget and computes the exact dollar overage.
  - Warns about categories in the caution zone (75%–99%).
  - Tracks monthly daily burn rate and projected end-of-month spend.
- **Dual Interface:**
  1. **Interactive Single-File Web App (`expense_tracker_chatbot.html`):** Full visual dashboard with interactive Chart.js charts, transactions table, 50/30/20 planner, and live chatbot.
  2. **Standalone Python CLI / REST API (`app.py`):** Runs interactively in your terminal or serves a REST API with persistent SQLite database storage (`expenses.db`).

---

## Quickstart (Terminal CLI)

Run the bot directly using Python 3:

```bash
python3 app.py
```

### Example Commands:
```text
You > Spent $45 on groceries
SpendBot > ✅ Expense Logged!
• ID: #1 | 2026-10-20
• Description: Groceries Purchase
• Amount: $45.00 (Groceries)
• Status: $355.00 remaining in category.

You > Am I overspending?
SpendBot > 🎉 Great news! You haven't exceeded any category budgets this month.

You > Recommend 50/30/20 budget for 4500 income
SpendBot > 🎯 50/30/20 Budget Plan Applied for $4,500.00 Monthly Income:
• 🏠 Needs (50%): $2,250.00
• 🍔 Wants (30%): $1,350.00
• 💰 Savings & Debt (20%): $900.00

You > Show spending analysis
SpendBot > 📊 Monthly Budget & Spending Analysis:
• Total Budget: $3,600.00
• Total Spent: $1,245.00 (34.6% utilized)
• Remaining: $2,355.00
• Daily Burn Rate: $62.25/day (Projected: $1,867.50)
```

---

## Running the Web API Server

Install optional requirements and run the Flask API:

```bash
pip install -r requirements.txt
python3 app.py --server
```

Endpoints:
- `POST /chat`: `{"message": "Spent $30 on dining"}` -> returns SpendBot's response.
- `GET /analytics`: Returns complete JSON summary of category budgets, actual spent, overspending alerts, and burn rate.
