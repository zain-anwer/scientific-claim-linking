function normalize(stance) {
  const s = (stance || "").toLowerCase().trim();
  if (s === "supports" || s === "support") return "support";
  if (s === "refutes"  || s === "refute")  return "refute";
  return "neutral";
}

const S = {
  card: {
    background: "#fff", border: "1px solid #e2e8f0", borderRadius: 16,
    padding: "18px 20px",
  },
  topRow: {
    display: "flex", justifyContent: "space-between", alignItems: "flex-start",
    flexWrap: "wrap", gap: 12, marginBottom: 16,
  },
  claimLabel: {
    fontSize: 10, color: "#94a3b8", textTransform: "uppercase",
    letterSpacing: "0.1em", fontFamily: "monospace", marginBottom: 4,
  },
  claimText: { fontSize: 13, color: "#334155", fontWeight: 500, lineHeight: 1.45, maxWidth: 400 },
  badge: (color) => ({
    display: "flex", alignItems: "center", gap: 10, padding: "10px 16px",
    borderRadius: 12, border: `1px solid ${color.border}`,
    background: color.bg, flexShrink: 0,
  }),
  score: (color) => ({
    fontSize: 26, fontWeight: 700, fontFamily: "monospace",
    lineHeight: 1, color: color.text,
  }),
  relLabel: (color) => ({ fontSize: 10, color: color.muted, marginBottom: 1 }),
  relName:  (color) => ({ fontSize: 13, fontWeight: 600, color: color.text }),
  barTrack: {
    height: 8, background: "#f1f5f9", borderRadius: 20,
    overflow: "hidden", display: "flex", gap: 2,
  },
  statsRow: {
    display: "flex", flexWrap: "wrap", gap: "6px 20px",
    marginTop: 8, fontSize: 12, color: "#64748b", alignItems: "center",
  },
  statItem: { display: "flex", alignItems: "center", gap: 5 },
  dot: (bg) => ({ width: 7, height: 7, borderRadius: "50%", background: bg, flexShrink: 0 }),
  statCount: { fontWeight: 600, color: "#334155" },
  total: { marginLeft: "auto", fontFamily: "monospace", fontSize: 11, color: "#94a3b8" },
};

const COLORS = {
  high:   { text: "#15803d", bg: "#f0fdf4", border: "#bbf7d0", muted: "#86efac" },
  mid:    { text: "#b45309", bg: "#fffbeb", border: "#fde68a", muted: "#fcd34d" },
  low:    { text: "#be123c", bg: "#fff1f2", border: "#fecdd3", muted: "#fda4af" },
};

export default function MetricsWidget({ results, query }) {
  const counts = results.reduce(
    (a, p) => { const s = normalize(p.stance); a[s]++; return a; },
    { support: 0, refute: 0, neutral: 0 }
  );
  const total = results.length;
  const score = total > 0
    ? Math.round(((counts.support + counts.neutral * 0.5) / total) * 100) : 0;

  const { label, color } =
    score >= 70 ? { label: "Well Supported", color: COLORS.high } :
    score >= 40 ? { label: "Mixed Evidence",  color: COLORS.mid  } :
                  { label: "Disputed",         color: COLORS.low  };

  const pct = (n) => (total > 0 ? (n / total) * 100 : 0);

  return (
    <div style={S.card}>
      <div style={S.topRow}>
        <div>
          <div style={S.claimLabel}>Claim</div>
          <div style={S.claimText}>"{query}"</div>
        </div>
        <div style={S.badge(color)}>
          <span style={S.score(color)}>{score}</span>
          <div>
            <div style={S.relLabel(color)}>Reliability Index</div>
            <div style={S.relName(color)}>{label}</div>
          </div>
        </div>
      </div>

      {/* Stacked bar */}
      <div style={S.barTrack}>
        {counts.support > 0 &&
          <div style={{ width: `${pct(counts.support)}%`, background: "#10b981", transition: "width 0.6s" }} />}
        {counts.neutral > 0 &&
          <div style={{ width: `${pct(counts.neutral)}%`, background: "#cbd5e1", transition: "width 0.6s" }} />}
        {counts.refute > 0 &&
          <div style={{ width: `${pct(counts.refute)}%`,  background: "#f43f5e", transition: "width 0.6s" }} />}
      </div>

      <div style={S.statsRow}>
        {[
          { n: counts.support, label: "Supporting", bg: "#10b981" },
          { n: counts.neutral, label: "Neutral",    bg: "#cbd5e1" },
          { n: counts.refute,  label: "Refuting",   bg: "#f43f5e" },
        ].map(({ n, label, bg }) => (
          <span key={label} style={S.statItem}>
            <span style={S.dot(bg)} />
            <span style={S.statCount}>{n}</span>
            {label}
          </span>
        ))}
        <span style={S.total}>{total} papers</span>
      </div>
    </div>
  );
}