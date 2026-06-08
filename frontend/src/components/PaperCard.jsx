import { useState } from "react";
// Component to display the metrics and reliability index for a given claim based on the retrieved papers and their stances
function normalize(stance) {
  const s = (stance || "").toLowerCase().trim();
  if (s === "supports" || s === "support") return "support";
  if (s === "refutes"  || s === "refute")  return "refute";
  return "neutral";
}
// Styles for the MetricsWidget component
const STANCE = {
  support: { label: "Supports", bg: "#f0fdf4", text: "#15803d", border: "#bbf7d0",
    icon: <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.5"
      strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg> },
  refute:  { label: "Refutes",  bg: "#fff1f2", text: "#be123c", border: "#fecdd3",
    icon: <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.5"
      strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12"/></svg> },
  neutral: { label: "Neutral",  bg: "#f8fafc", text: "#475569", border: "#e2e8f0",
    icon: <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.5"
      strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><path d="M20 12H4"/></svg> },
};
// MetricsWidget component definition that calculates the reliability index and displays the supporting, neutral, and refuting paper counts along with a visual representation of the evidence distribution
const S = {
  card: {
    background: "#fff", border: "1px solid #e2e8f0", borderRadius: 16,
    padding: "18px 20px", transition: "border-color 0.15s, box-shadow 0.15s",
  },
  topRow: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 10 },
  left:   { display: "flex", alignItems: "flex-start", gap: 10, minWidth: 0 },
  rank:   {
    flexShrink: 0, width: 24, height: 24, borderRadius: 7,
    background: "#f1f5f9", color: "#64748b", fontSize: 10,
    fontFamily: "monospace", display: "flex", alignItems: "center",
    justifyContent: "center", marginTop: 1,
  },
  title:  { fontSize: 13, fontWeight: 600, color: "#1e293b", lineHeight: 1.45 },
  badge:  (cfg) => ({
    display: "flex", alignItems: "center", gap: 5,
    padding: "4px 10px", borderRadius: 8, border: `1px solid ${cfg.border}`,
    background: cfg.bg, color: cfg.text, fontSize: 11, fontWeight: 600, flexShrink: 0,
  }),
  abstract: { marginLeft: 34, marginBottom: 10 },
  abstractText: { fontSize: 12, color: "#64748b", lineHeight: 1.65 },
  expandBtn: {
    marginTop: 4, background: "none", border: "none", cursor: "pointer",
    fontSize: 12, color: "#6366f1", fontWeight: 500,
    display: "flex", alignItems: "center", gap: 4, padding: 0,
  },
  footer: {
    marginLeft: 34, display: "flex", alignItems: "center",
    justifyContent: "space-between", flexWrap: "wrap", gap: 8,
  },
  scoreRow: { display: "flex", alignItems: "center", gap: 6 },
  scoreLabel: { fontSize: 11, color: "#94a3b8" },
  scoreTrack: { width: 72, height: 5, background: "#f1f5f9", borderRadius: 10, overflow: "hidden" },
  scoreFill: (pct) => ({ width: `${pct}%`, height: "100%", background: "#818cf8", borderRadius: 10 }),
  scoreNum: { fontSize: 11, fontFamily: "monospace", color: "#94a3b8" },
  viewBtn: {
    display: "inline-flex", alignItems: "center", gap: 5,
    padding: "6px 12px", borderRadius: 8,
    border: "1px solid #c7d2fe", background: "#eef2ff",
    color: "#4338ca", fontSize: 12, fontWeight: 600,
    textDecoration: "none", transition: "background 0.15s",
    cursor: "pointer",
  },
  noUrl: {
    display: "inline-flex", alignItems: "center", gap: 5,
    padding: "6px 12px", borderRadius: 8,
    border: "1px solid #e2e8f0", background: "#f8fafc",
    color: "#94a3b8", fontSize: 12, cursor: "not-allowed", userSelect: "none",
  },
};

const TRUNCATE = 240;
// PaperCard component definition that renders the information of a single paper including its title, abstract, relevance score, and a link to view the paper if available. It also handles the logic for expanding/collapsing long abstracts and displays the stance of the paper towards the claim.
export default function PaperCard({ paper }) {
  const [expanded, setExpanded] = useState(false);
  const [hovered,  setHovered]  = useState(false);

  const cfg      = STANCE[normalize(paper.stance)];
  const abstract = paper.abstract || "";
  const isLong   = abstract.length > TRUNCATE;
  const display  = expanded || !isLong ? abstract : abstract.slice(0, TRUNCATE) + "…";
  const scorePct = Math.min(Math.round(paper.score * 100), 100);
  const hasUrl   = Boolean(paper.url?.trim());

  return (
    <article
      style={{
        ...S.card,
        ...(hovered ? { borderColor: "#cbd5e1", boxShadow: "0 2px 10px rgba(0,0,0,0.06)" } : {}),
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Title row */}
      <div style={S.topRow}>
        <div style={S.left}>
          <span style={S.rank}>{paper.rank}</span>
          <h3 style={S.title}>{paper.title}</h3>
        </div>
        <div style={S.badge(cfg)}>
          {cfg.icon}
          {cfg.label}
        </div>
      </div>

      {/* Abstract */}
      {abstract && (
        <div style={S.abstract}>
          <p style={S.abstractText}>{display}</p>
          {isLong && (
            <button style={S.expandBtn} onClick={() => setExpanded(v => !v)}>
              {expanded ? "Show less" : "Read full abstract"}
              <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2"
                strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"
                style={{ transform: expanded ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}>
                <path d="M19 9l-7 7-7-7"/>
              </svg>
            </button>
          )}
        </div>
      )}

      {/* Footer: score + View Paper */}
      <div style={S.footer}>
        <div style={S.scoreRow}>
          <span style={S.scoreLabel}>Relevance</span>
          <div style={S.scoreTrack}>
            <div style={S.scoreFill(scorePct)} />
          </div>
          <span style={S.scoreNum}>{paper.score.toFixed(4)}</span>
        </div>

        {hasUrl ? (
          <a href={paper.url} target="_blank" rel="noopener noreferrer" style={S.viewBtn}>
            View Paper
            <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
              <path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
            </svg>
          </a>
        ) : (
          <span style={S.noUrl}>No URL available</span>
        )}
      </div>
    </article>
  );
}