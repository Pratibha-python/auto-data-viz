# 📊 Auto Data Visualization App

Upload any CSV or Excel file and get instant, beautiful charts — automatically generated based on your data's column types.

---

## 🚀 Quick Start (VS Code)

### Prerequisites
- Python 3.9+ installed
- Node.js 18+ installed
- Two terminal windows in VS Code

---

### Step 1 — Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be live at: http://localhost:8000

---

### Step 2 — Frontend Setup

Open a **second terminal**, then:

```bash
cd frontend
npm install
npm run dev
```

The app will open at: http://localhost:5173

---

## 🎯 Features

| Feature | Details |
|---|---|
| **Upload** | CSV, XLSX, XLS files |
| **Auto-detect** | Numeric, Categorical, Date columns |
| **Histogram** | One per numeric column (up to 6) |
| **Bar Chart** | Categorical × Numeric combinations |
| **Line Chart** | Date × Numeric time series |
| **Heatmap** | Correlation matrix for numeric columns |
| **Download** | Save any chart as PNG |
| **In-memory** | No files saved to disk, resets on restart |

---

## 📁 Project Structure

```
auto-data-viz/
├── backend/
│   ├── main.py            ← FastAPI app
│   └── requirements.txt   ← Python deps
├── frontend/
│   ├── src/
│   │   ├── main.jsx       ← React entry point
│   │   ├── App.jsx        ← Main UI component
│   │   ├── App.module.css ← Component styles
│   │   └── index.css      ← Global styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js     ← Dev proxy → localhost:8000
└── README.md
```

---

## 🧪 Try It With Sample Data

Any CSV with mixed columns works great. Examples:
- Sales data (dates + amounts + categories)
- Survey results (multiple numeric columns)
- Stock prices (date + price columns)
- Iris dataset, Titanic dataset, etc.

---

# 🚀 Auto Data Visualization Tool

🔗 **Live Demo:** https://auto-data-viz-iv5q.vercel.app/

---

# Output Page

<img width="1813" height="956" alt="image" src="https://github.com/user-attachments/assets/d909168d-b736-4512-ad71-37cdab890174" />

<img width="1763" height="964" alt="image" src="https://github.com/user-attachments/assets/b41dfa7e-45ac-48f4-8374-c4588f7501bd" />

