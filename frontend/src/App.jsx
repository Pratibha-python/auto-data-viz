import { useState, useCallback, useRef } from "react";
import styles from "./App.module.css";

// ── Icon helpers ───────────────────────────────────────────────────────────────
const UploadIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </svg>
);

const DownloadIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7 10 12 15 17 10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </svg>
);

const SparkleIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>
  </svg>
);

const ChartIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10" />
    <line x1="12" y1="20" x2="12" y2="4" />
    <line x1="6" y1="20" x2="6" y2="14" />
  </svg>
);

const FileIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
  </svg>
);

const XIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

// ── Chart type badge colors ───────────────────────────────────────────────────
const BADGE_COLORS = {
  histogram: { bg: "rgba(99,102,241,0.18)",  color: "#818cf8", label: "Histogram"    },
  bar:       { bg: "rgba(34,211,238,0.15)",  color: "#22d3ee", label: "Bar Chart"    },
  line:      { bg: "rgba(52,211,153,0.15)",  color: "#34d399", label: "Line Chart"   },
  heatmap:   { bg: "rgba(244,114,182,0.15)", color: "#f472b6", label: "Heatmap"      },
  pie:       { bg: "rgba(251,191,36,0.15)",  color: "#fbbf24", label: "Pie Chart"    },
  scatter:   { bg: "rgba(96,165,250,0.15)",  color: "#60a5fa", label: "Scatter Plot" },
};

// ── Summary pill ──────────────────────────────────────────────────────────────
function Pill({ label, value, accent }) {
  return (
    <div className={styles.pill} style={{ "--acc": accent }}>
      <span className={styles.pillValue}>{value}</span>
      <span className={styles.pillLabel}>{label}</span>
    </div>
  );
}

// ── Chart card ────────────────────────────────────────────────────────────────
function ChartCard({ chart, index }) {
  const badge = BADGE_COLORS[chart.type] || BADGE_COLORS.histogram;

  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = `data:image/png;base64,${chart.image}`;
    link.download = `${chart.title.replace(/\s+/g, "_")}.png`;
    link.click();
  };

  return (
    <div
      className={styles.chartCard}
      style={{ animationDelay: `${index * 80}ms` }}
    >
      <div className={styles.chartHeader}>
        <span
          className={styles.typeBadge}
          style={{ background: badge.bg, color: badge.color }}
        >
          {badge.label}
        </span>
        <h3 className={styles.chartTitle}>{chart.title}</h3>
        <button className={styles.downloadBtn} onClick={handleDownload} title="Download PNG">
          <DownloadIcon />
          <span>Save PNG</span>
        </button>
      </div>
      <div className={styles.chartImageWrap}>
        <img
          src={`data:image/png;base64,${chart.image}`}
          alt={chart.title}
          className={styles.chartImage}
        />
      </div>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const acceptFile = (f) => {
    const name = f.name.toLowerCase();
    if (!name.endsWith(".csv") && !name.endsWith(".xlsx") && !name.endsWith(".xls")) {
      setError("Please upload a CSV or Excel (.xlsx / .xls) file.");
      return;
    }
    setError(null);
    setResult(null);
    setFile(f);
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) acceptFile(f);
  }, []);

  const onDragOver = (e) => { e.preventDefault(); setDragging(true); };
  const onDragLeave = () => setDragging(false);

  const onFileChange = (e) => {
    const f = e.target.files[0];
    if (f) acceptFile(f);
    e.target.value = "";
  };

  const handleCreate = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(
        "https://auto-data-viz-backend.onrender.com/upload",
        { method: "POST", body: formData }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Server error");
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError(null);
  };

  const summary = result?.summary;
  const charts = result?.charts || [];

  return (
    <div className={styles.app}>
      {/* ── BG decorations ── */}
      <div className={styles.bgOrb1} />
      <div className={styles.bgOrb2} />
      <div className={styles.bgOrb3} />

      {/* ── Header ── */}
      <header className={styles.header}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}><ChartIcon /></span>
          <span>DataViz</span>
          <span className={styles.logoBadge}>AUTO</span>
        </div>
        <p className={styles.tagline}>
          Upload any dataset · Get instant visualizations
        </p>
      </header>

      <main className={styles.main}>
        {/* ── Upload zone ── */}
        <section className={styles.uploadSection}>
          <div
            className={`${styles.dropzone} ${dragging ? styles.dragActive : ""} ${file ? styles.hasFile : ""}`}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onClick={() => !file && fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={onFileChange}
              className={styles.hiddenInput}
            />

            {!file ? (
              <div className={styles.dzContent}>
                <div className={styles.dzIcon}><UploadIcon /></div>
                <p className={styles.dzPrimary}>Drop your dataset here</p>
                <p className={styles.dzSecondary}>
                  or <span className={styles.dzLink}>browse files</span>
                </p>
                <p className={styles.dzHint}>Supports CSV · XLSX · XLS</p>
              </div>
            ) : (
              <div className={styles.filePreview}>
                <div className={styles.fileIcon}><FileIcon /></div>
                <div className={styles.fileInfo}>
                  <p className={styles.fileName}>{file.name}</p>
                  <p className={styles.fileSize}>
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <button
                  className={styles.removeFile}
                  onClick={(e) => { e.stopPropagation(); handleReset(); }}
                  title="Remove file"
                >
                  <XIcon />
                </button>
              </div>
            )}
          </div>

          {/* ── Action buttons ── */}
          <div className={styles.actions}>
            <button
              className={styles.createBtn}
              onClick={handleCreate}
              disabled={!file || loading}
            >
              {loading ? (
                <>
                  <span className={styles.spinner} />
                  Analyzing…
                </>
              ) : (
                <>
                  <span className={styles.btnIcon}><SparkleIcon /></span>
                  Create Visualizations
                </>
              )}
            </button>
          </div>

          {/* ── Error ── */}
          {error && (
            <div className={styles.errorBox}>
              <strong>⚠ Error:</strong> {error}
            </div>
          )}
        </section>

        {/* ── Summary ── */}
        {summary && (
          <section className={styles.summarySection}>
            <h2 className={styles.sectionTitle}>Dataset Overview</h2>
            <div className={styles.pillRow}>
              <Pill label="Rows"      value={summary.rows.toLocaleString()}    accent="#6366f1" />
              <Pill label="Columns"   value={summary.columns}                  accent="#22d3ee" />
              <Pill label="Numeric"   value={summary.column_types.numeric.length}    accent="#34d399" />
              <Pill label="Categorical" value={summary.column_types.categorical.length} accent="#f472b6" />
              <Pill label="Date"      value={summary.column_types.date.length}  accent="#fb923c" />
              <Pill label="Missing"   value={summary.missing_values}           accent="#94a3b8" />
            </div>
            <div className={styles.colList}>
              <p className={styles.colListLabel}>Columns detected:</p>
              <div className={styles.colTags}>
                {summary.column_names.map((c) => {
                  const type = summary.column_types.numeric.includes(c)      ? "numeric"
                             : summary.column_types.date.includes(c)          ? "date"
                             : "categorical";
                  const tagColor = { numeric: "#6366f1", date: "#fb923c", categorical: "#f472b6" }[type];
                  return (
                    <span key={c} className={styles.colTag} style={{ "--c": tagColor }}>
                      {c}
                    </span>
                  );
                })}
              </div>
            </div>
          </section>
        )}

        {/* ── Charts grid ── */}
        {charts.length > 0 && (
          <section className={styles.chartsSection}>
            <div className={styles.chartsSectionHeader}>
              <h2 className={styles.sectionTitle}>
                {charts.length} Chart{charts.length !== 1 ? "s" : ""} Generated
              </h2>
              <p className={styles.chartsHint}>Click <DownloadIcon /> to save any chart as PNG</p>
            </div>
            <div className={styles.chartsGrid}>
              {charts.map((chart, i) => (
                <ChartCard key={i} chart={chart} index={i} />
              ))}
            </div>
          </section>
        )}

        {/* ── Empty state ── */}
        {!file && !result && (
          <div className={styles.emptyState}>
            <div className={styles.emptyIllustration}>
              {["bar", "line", "pie"].map((t, i) => (
                <div key={t} className={styles.emptyBar} style={{ "--h": `${40 + i * 25}%`, "--d": `${i * 0.15}s` }} />
              ))}
            </div>
            <p className={styles.emptyText}>Your charts will appear here</p>
          </div>
        )}
      </main>

      <footer className={styles.footer}>
        <p>Auto Data Visualization · Powered by FastAPI + Pandas + Seaborn</p>
      </footer>
    </div>
  );
}
