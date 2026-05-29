# ✨ Misbah's Magic
### Professional Bank & QuickBooks Reconciliation Tool

A high-performance reconciliation tool that matches Bank Statements with QuickBooks records using intelligent fuzzy matching and optional AI-powered PDF extraction via Google Gemini.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp backend/.env.example backend/.env
# Edit backend/.env — set USERS and GEMINI_API_KEY
```

### 3. Start the app
```bash
# Development
python backend/app.py

# Production (gunicorn)
gunicorn "backend.app:create_app()" --bind 0.0.0.0:8080
```

### 4. Open the frontend
Open `frontend/index.html` in your browser (or serve with any static server).

---

## 📁 Project Structure

```
misbah-magic/
├── backend/
│   ├── app.py                          # Flask application factory
│   ├── config.py                       # Config (env vars + defaults)
│   ├── wsgi.py                         # Production WSGI entry point
│   ├── requirements.txt
│   ├── .env / .env.example
│   │
│   ├── core/                           # Shared infrastructure
│   │   ├── dirs.py                     # Temp directory handles
│   │   └── exceptions.py              # Custom app exceptions
│   │
│   ├── modules/                        # Feature modules (Blueprint-based)
│   │   ├── auth/
│   │   │   └── routes.py              # Login / session
│   │   ├── reconciliation/
│   │   │   ├── routes.py              # POST /api/reconcile/excel|pdf
│   │   │   ├── excel_engine.py        # Load + normalise Excel/CSV files
│   │   │   ├── pdf_engine.py          # Gemini AI PDF extraction
│   │   │   └── fuzzy_matcher.py       # Core matching algorithm
│   │   └── reports/
│   │       ├── routes.py              # GET /api/reports/<filename>
│   │       └── generator.py           # Color-coded Excel report writer
│   │
│   └── tests/                         # pytest test suite
│       ├── test_fuzzy_matcher.py
│       └── test_excel_engine.py
│
├── frontend/
│   ├── index.html                      # Main UI (single page)
│   └── assets/
│       ├── css/
│       │   ├── variables.css          # Design tokens
│       │   ├── base.css               # Reset + typography
│       │   ├── components.css         # UI components
│       │   └── animations.css         # Motion
│       └── js/
│           ├── config.js              # API base URL + constants
│           ├── state.js               # App state management
│           ├── api.js                 # Backend API client
│           ├── uploader.js            # Drag-and-drop file handling
│           ├── ui.js                  # DOM rendering helpers
│           ├── results.js             # Results table + tabs
│           └── app.js                 # Entry point + event wiring
│
├── docs/                               # Project documentation
├── scripts/                            # Terminal / automation scripts
├── render.yaml                         # Render.com deploy config
├── run.sh                              # Local start script
├── runtime.txt                         # Python version pin
├── .gitignore
└── README.md
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **Excel Mode** | Match Bank Excel/CSV with QuickBooks Excel/CSV |
| 🤖 **AI PDF Mode** | Extract transactions from PDF statements using Gemini |
| 🔍 **Smart Matching** | Fuzzy description + exact amount + date proximity |
| 📈 **Live Dashboard** | Matched, Missing, Duplicate, Discrepancy views |
| 🔎 **Search & Filter** | Search across all transaction views |
| ⬇️ **Excel Export** | Color-coded professional report download |
| 🔒 **Secure Access** | Password-protected gateway (multi-user supported) |

---

## 🔧 Configuration

Edit `backend/.env`:

```env
# Multi-user format: "user1:pass1,user2:pass2"
USERS=misbah:misbah2024

GEMINI_API_KEY=your_key_here    # For PDF mode (optional)
PORT=8080
DEBUG=false

# Matching tuning
AMOUNT_TOLERANCE=0.01
DATE_TOLERANCE_DAYS=3
SIMILARITY_THRESHOLD=0.60
```

Get a free Gemini API key at: https://aistudio.google.com/apikey

---

## 🧪 Running Tests

```bash
cd backend
pip install pytest
pytest tests/
```

---

## 📊 Supported File Formats

- **Bank Statement**: `.xlsx`, `.xls`, `.csv`, `.pdf` (PDF requires Gemini)
- **QuickBooks Export**: `.xlsx`, `.xls`, `.csv`

The app auto-detects column names (Date, Description/Memo, Amount).

---

## 🛠 Tech Stack

- **Frontend**: HTML5, CSS3, Vanilla JavaScript (no framework)
- **Backend**: Python 3.11+, Flask, Flask-CORS
- **Processing**: pandas, openpyxl
- **AI**: Google Gemini 1.5 Pro (PDF mode)
- **Reports**: openpyxl (color-coded Excel output)
- **Deploy**: Render.com (render.yaml included)
