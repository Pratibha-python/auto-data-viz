from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import io
import base64
import numpy as np
from typing import Optional

app = FastAPI(title="Auto Data Visualization API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Seaborn / Matplotlib theme ────────────────────────────────────────────────
sns.set_theme(style="darkgrid", palette="muted")
plt.rcParams.update({
    "figure.facecolor": "#0f1117",
    "axes.facecolor":   "#1a1d27",
    "axes.edgecolor":   "#30354a",
    "grid.color":       "#30354a",
    "text.color":       "#e2e8f0",
    "axes.labelcolor":  "#e2e8f0",
    "xtick.color":      "#94a3b8",
    "ytick.color":      "#94a3b8",
    "axes.titlecolor":  "#f1f5f9",
    "axes.titlesize":   14,
    "axes.labelsize":   11,
    "figure.titlesize": 16,
})

ACCENT_COLORS = ["#6366f1", "#22d3ee", "#f472b6", "#34d399", "#fb923c", "#a78bfa"]

# ── Helper: detect column types ───────────────────────────────────────────────
def detect_column_types(df: pd.DataFrame) -> dict:
    import datetime as dt
    types = {"numeric": [], "categorical": [], "date": []}
    date_keywords = {"date", "time", "year", "month", "day", "dt", "timestamp", "period"}

    for col in df.columns:
        col_lower = col.lower()
        series = df[col]
        non_null = series.dropna()
        if non_null.empty:
            types["categorical"].append(col)
            continue

        # ── 1. Already a proper datetime dtype ───────────────────────────────
        if pd.api.types.is_datetime64_any_dtype(series):
            types["date"].append(col)
            continue

        # ── 2. Numeric dtype ─────────────────────────────────────────────────
        if pd.api.types.is_numeric_dtype(series):
            is_year_like = (
                any(kw in col_lower for kw in date_keywords)
                and non_null.between(1900, 2100).mean() > 0.9
                and non_null.nunique() <= 200
            )
            is_date_int = False
            if series.dtype in [np.int32, np.int64] and non_null.between(19000101, 21001231).mean() > 0.9:
                try:
                    parsed = pd.to_datetime(non_null.astype(str), format="%Y%m%d", errors="coerce")
                    is_date_int = parsed.notna().mean() > 0.6
                except Exception:
                    pass

            if is_year_like or is_date_int:
                types["date"].append(col)
            else:
                types["numeric"].append(col)
            continue

        # ── 3. String / object / StringDtype (pandas 2.x Excel columns) ─────
        # Convert to plain Python strings for uniform handling
        try:
            str_series = non_null.astype(str)
        except Exception:
            types["categorical"].append(col)
            continue

        # Check if values are Python datetime objects (openpyxl sometimes does this)
        first_val = non_null.iloc[0]
        if isinstance(first_val, (dt.datetime, dt.date, pd.Timestamp)):
            types["date"].append(col)
            continue

        # Try parsing as dates — works for "2025-01-01", "01/01/2025", etc.
        try:
            parsed = pd.to_datetime(str_series, errors="coerce")
            if parsed.notna().mean() > 0.6:
                types["date"].append(col)
                continue
        except Exception:
            pass

        # Looser check: column name suggests date + at least 40% parse OK
        if any(kw in col_lower for kw in date_keywords):
            try:
                parsed = pd.to_datetime(str_series, dayfirst=False, errors="coerce")
                if parsed.notna().mean() > 0.4:
                    types["date"].append(col)
                    continue
            except Exception:
                pass

        types["categorical"].append(col)
    return types


# ── Helper: figure → base64 PNG ───────────────────────────────────────────────
def fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


# ── Chart generators ──────────────────────────────────────────────────────────
def make_histogram(df: pd.DataFrame, col: str, color: str) -> dict:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    data = df[col].dropna()
    bins = min(30, max(10, len(data) // 10))
    ax.hist(data, bins=bins, color=color, edgecolor="#0f1117", alpha=0.85)
    ax.set_title(f"Distribution of {col}")
    ax.set_xlabel(col)
    ax.set_ylabel("Frequency")
    return {
        "type": "histogram",
        "title": f"Histogram – {col}",
        "image": fig_to_base64(fig),
    }


def make_bar_chart(df: pd.DataFrame, cat_col: str, num_col: str, color: str) -> dict:
    fig, ax = plt.subplots(figsize=(9, 5))
    grouped = df.groupby(cat_col)[num_col].mean().nlargest(15).sort_values(ascending=False)
    bars = ax.bar(grouped.index.astype(str), grouped.values, color=color,
                  edgecolor="#0f1117", alpha=0.85)
    ax.set_title(f"Average {num_col} by {cat_col}")
    ax.set_xlabel(cat_col)
    ax.set_ylabel(f"Mean {num_col}")
    plt.xticks(rotation=35, ha="right", fontsize=9)
    # value labels on bars
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"{h:,.1f}",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, color="#94a3b8")
    return {
        "type": "bar",
        "title": f"Bar Chart – {cat_col} vs {num_col}",
        "image": fig_to_base64(fig),
    }


def make_line_chart(df: pd.DataFrame, date_col: str, num_col: str, color: str) -> dict:
    fig, ax = plt.subplots(figsize=(10, 4.5))
    temp = df[[date_col, num_col]].copy()

    # Normalize date col — handles datetime64, object, StringDtype (pandas 2.x), int
    if pd.api.types.is_datetime64_any_dtype(temp[date_col]):
        parsed = temp[date_col]
    else:
        str_dates = temp[date_col].astype(str)
        parsed = pd.to_datetime(str_dates, errors="coerce")
        if parsed.isna().mean() > 0.4:
            try:
                parsed = pd.to_datetime(str_dates, format="%Y%m%d", errors="coerce")
            except Exception:
                pass
        if parsed.isna().mean() > 0.4:
            try:
                parsed = pd.to_datetime(str_dates.str[:4], format="%Y", errors="coerce")
            except Exception:
                pass

    temp[date_col] = parsed
    temp = temp.dropna().sort_values(date_col)

    if temp.empty:
        plt.close(fig)
        return None

    ax.plot(temp[date_col], temp[num_col], color=color, linewidth=1.8)
    ax.fill_between(temp[date_col], temp[num_col], alpha=0.15, color=color)
    ax.set_title(f"{num_col} over Time ({date_col})")
    ax.set_xlabel(date_col)
    ax.set_ylabel(num_col)
    fig.autofmt_xdate(rotation=30)
    return {
        "type": "line",
        "title": f"Line Chart – {date_col} vs {num_col}",
        "image": fig_to_base64(fig),
    }


def make_pie_chart(df: pd.DataFrame, cat_col: str, num_col: str) -> dict:
    grouped = df.groupby(cat_col)[num_col].sum().nlargest(8)
    if len(grouped) < 2:
        return None
    PIE_COLORS = ["#6366f1", "#22d3ee", "#f472b6", "#34d399", "#fb923c", "#a78bfa", "#fbbf24", "#60a5fa"]
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor("#0f1117")
    wedges, texts, autotexts = ax.pie(
        grouped.values,
        labels=grouped.index.astype(str),
        autopct="%1.1f%%",
        colors=PIE_COLORS[:len(grouped)],
        startangle=140,
        wedgeprops={"edgecolor": "#0f1117", "linewidth": 2},
        pctdistance=0.82,
    )
    for t in texts:
        t.set_color("#94a3b8")
        t.set_fontsize(9)
    for at in autotexts:
        at.set_color("#f0f4ff")
        at.set_fontsize(8)
        at.set_fontweight("bold")
    ax.set_title(f"{num_col} share by {cat_col}")
    ax.set_facecolor("#0f1117")
    return {
        "type": "pie",
        "title": f"Pie Chart – {cat_col} vs {num_col}",
        "image": fig_to_base64(fig),
    }


def make_scatter_plot(df: pd.DataFrame, x_col: str, y_col: str, color: str) -> dict:
    fig, ax = plt.subplots(figsize=(8, 5))
    data = df[[x_col, y_col]].dropna()
    # Sample up to 1000 points for readability
    if len(data) > 1000:
        data = data.sample(1000, random_state=42)
    ax.scatter(data[x_col], data[y_col], color=color, alpha=0.6, s=30, edgecolors="none")
    # Trend line
    try:
        z = np.polyfit(data[x_col], data[y_col], 1)
        p = np.poly1d(z)
        x_line = np.linspace(data[x_col].min(), data[x_col].max(), 200)
        ax.plot(x_line, p(x_line), color="#f0f4ff", linewidth=1.2, linestyle="--", alpha=0.5)
    except Exception:
        pass
    ax.set_title(f"{x_col} vs {y_col}")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    return {
        "type": "scatter",
        "title": f"Scatter Plot – {x_col} vs {y_col}",
        "image": fig_to_base64(fig),
    }


def make_correlation_heatmap(df: pd.DataFrame, numeric_cols: list) -> dict:
    if len(numeric_cols) < 2:
        return None
    fig, ax = plt.subplots(figsize=(max(6, len(numeric_cols)), max(5, len(numeric_cols) - 1)))
    corr = df[numeric_cols].corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    cmap = sns.diverging_palette(230, 20, as_cmap=True)
    sns.heatmap(corr, mask=mask, cmap=cmap, vmax=1, vmin=-1, center=0,
                annot=True, fmt=".2f", square=True, linewidths=0.5,
                linecolor="#0f1117", ax=ax,
                annot_kws={"size": 9, "color": "#e2e8f0"})
    ax.set_title("Correlation Heatmap")
    return {
        "type": "heatmap",
        "title": "Correlation Heatmap",
        "image": fig_to_base64(fig),
    }


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Auto Data Visualization API is running."}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename or ""
    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        raise HTTPException(status_code=400, detail="Only CSV or Excel files are supported.")

    contents = await file.read()
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents), parse_dates=True)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not parse file: {e}")

    if df.empty:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    # Basic cleaning
    df = df.dropna(how="all").reset_index(drop=True)

    col_types = detect_column_types(df)
    charts = []
    color_idx = 0

    def next_color():
        nonlocal color_idx
        c = ACCENT_COLORS[color_idx % len(ACCENT_COLORS)]
        color_idx += 1
        return c

    # 1. Histograms for numeric columns (up to 6)
    for col in col_types["numeric"][:6]:
        try:
            charts.append(make_histogram(df, col, next_color()))
        except Exception:
            pass

    # 2. Bar charts: each categorical col × first numeric col
    if col_types["numeric"]:
        for cat_col in col_types["categorical"][:4]:
            try:
                charts.append(make_bar_chart(df, cat_col, col_types["numeric"][0], next_color()))
            except Exception:
                pass

    # 3. Line charts: date col × each numeric col (up to 3)
    for date_col in col_types["date"][:2]:
        for num_col in col_types["numeric"][:3]:
            try:
                lc = make_line_chart(df, date_col, num_col, next_color())
                if lc:
                    charts.append(lc)
            except Exception:
                pass

    # 4. Pie charts: each categorical col × first numeric col (up to 3 cats)
    if col_types["numeric"]:
        for cat_col in col_types["categorical"][:3]:
            try:
                pc = make_pie_chart(df, cat_col, col_types["numeric"][0])
                if pc:
                    charts.append(pc)
            except Exception:
                pass

    # 5. Scatter plots: pairs of numeric columns (up to 3 pairs)
    nums = col_types["numeric"]
    scatter_count = 0
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if scatter_count >= 3:
                break
            try:
                charts.append(make_scatter_plot(df, nums[i], nums[j], next_color()))
                scatter_count += 1
            except Exception:
                pass

    # 6. Correlation heatmap
    if len(col_types["numeric"]) >= 2:
        try:
            hm = make_correlation_heatmap(df, col_types["numeric"][:10])
            if hm:
                charts.append(hm)
        except Exception:
            pass

    if not charts:
        raise HTTPException(status_code=422,
                            detail="Could not generate any charts from this dataset.")

    summary = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": df.columns.tolist(),
        "column_types": col_types,
        "missing_values": int(df.isnull().sum().sum()),
    }

    return JSONResponse({"summary": summary, "charts": charts})
