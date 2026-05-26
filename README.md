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
# Edit backend/.env and set your password + Gemini API key
```

### 3. Start the backend
```bash
python backend/app.py
```

### 4. Open the frontend
Open `frontend/index.html` in your browser (or serve it with any static server).

---

## 📁 Project Structure

```
misbah-magic/
├── backend/
│   ├── app.py                  # Flask server (main entry point)
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment variables template
│   └── utils/
│       ├── excel_engine.py     # Core reconciliation logic
│       ├── pdf_engine.py       # Gemini AI PDF extraction
│       └── report_generator.py # Color-coded Excel report generation
├── frontend/
│   ├── index.html              # Main UI
│   ├── css/
│   │   └── style.css           # All styles
│   └── js/
│       ├── api.js              # Backend API client
│       └── app.js              # UI logic & state management
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
| 🔒 **Secure Access** | Password-protected gateway |

---

## 🔧 Configuration

Edit `backend/.env`:

```env
ACCESS_PASSWORD=misbah2024          # App login password
GEMINI_API_KEY=your_key_here        # For PDF mode (optional)
PORT=5000
DEBUG=false
```

Get a free Gemini API key at: https://aistudio.google.com/apikey

---

## 📊 Supported File Formats

- **Bank Statement**: `.xlsx`, `.xls`, `.csv`, `.pdf` (PDF requires Gemini)
- **QuickBooks Export**: `.xlsx`, `.xls`, `.csv`

The app auto-detects column names (Date, Description/Memo, Amount).

---

## 🛠 Tech Stack

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python, Flask, Flask-CORS
- **Processing**: pandas, openpyxl
- **AI**: Google Gemini 1.5 Pro (PDF mode)
- **Reports**: openpyxl (color-coded Excel)
