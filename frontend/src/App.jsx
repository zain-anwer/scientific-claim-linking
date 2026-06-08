import { useState } from "react";
import SearchComponent from "./components/SearchComponent";
import MetricsWidget   from "./components/MetricsWidget";
import PaperCard       from "./components/PaperCard";
import Loader          from "./components/Loader";
import { useClaimSearch } from "./hooks/useClaimSearch";

// Styles for the application components
const S = {
  page:    { minHeight: "100vh", background: "#f8fafc" },                
  header:  {
    borderBottom: "1px solid #e2e8f0", background: "rgba(255,255,255,0.9)",
    backdropFilter: "blur(8px)", position: "sticky", top: 0, zIndex: 10,
    padding: "14px 24px", display: "flex", alignItems: "center",
    justifyContent: "space-between",
  },
  logoRow: { display: "flex", alignItems: "center", gap: 10 },
  logoIcon:{
    width: 28, height: 28, borderRadius: 7, background: "#4f46e5",
    display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
  },
  logoName:{ fontWeight: 600, fontSize: 15, color: "#1e293b", letterSpacing: "-0.3px" },
  logoBadge:{
    fontSize: 11, color: "#94a3b8", border: "1px solid #e2e8f0",
    borderRadius: 20, padding: "2px 8px", fontFamily: "monospace",
  },
  headerRight: { fontSize: 11, color: "#94a3b8" },
  main:  { maxWidth: 820, margin: "0 auto", padding: "0 24px" },
  hero:  { padding: "80px 0 32px", textAlign: "center" },
  heroCompact: { padding: "28px 0 20px" },
  pill:  {
    fontSize: 11, fontFamily: "monospace", color: "#6366f1",
    textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: 16,
  },
  h1:    { fontSize: 36, fontWeight: 600, color: "#0f172a", marginBottom: 12, letterSpacing: "-0.5px" },
  sub:   { fontSize: 17, color: "#64748b", maxWidth: 480, margin: "0 auto", lineHeight: 1.6 },
  error: {
    marginTop: 12, padding: "12px 16px", background: "#fef2f2",
    border: "1px solid #fecaca", borderRadius: 12, color: "#b91c1c",
    fontSize: 13, textAlign: "center", maxWidth: 720, margin: "12px auto 0",
  },
  resultsHeader: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    marginBottom: 10,
  },
  resultsLabel: {
    fontSize: 10.5, fontWeight: 600, color: "#64748b",
    textTransform: "uppercase", letterSpacing: "0.1em",
  },
  resultsCount: { fontSize: 11, color: "#94a3b8", fontFamily: "monospace" },
  empty: { textAlign: "center", padding: "80px 0", color: "#94a3b8" },
  emptyIcon: { fontSize: 36, marginBottom: 8 },
  stack: { display: "flex", flexDirection: "column", gap: 10, paddingBottom: 64 },
};
//  Main App component that renders the entire application UI
export default function App() {
  const [query, setQuery] = useState("");
  const { results, loading, error, submitted, search } = useClaimSearch();

  const handleSearch = (q) => { setQuery(q); search(q); };

  return (
    <div style={S.page}>
      {/* Header */}
      <header style={S.header}>
        <div style={S.logoRow}>
          <div style={S.logoIcon}>
            <svg width="16" height="16" fill="none" stroke="white" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <span style={S.logoName}>Specter</span>
          <span style={S.logoBadge}>Claim Verifier</span>
        </div>
        <span style={S.headerRight}>Scientific Literature · NLI Pipeline</span>
      </header>

      <main style={S.main}>
        {/* Search section */}
        <section style={submitted ? S.heroCompact : S.hero}>
          {!submitted && (
            <>
              <p style={S.pill}>Hybrid BM25 · Semantic · NLI Reranking</p>
              <h1 style={S.h1}>Verify any scientific claim</h1>
              <p style={S.sub}>
                Paste a social media post or claim. We retrieve and verify it
                against peer-reviewed scientific literature.
              </p>
              <div style={{ height: 36 }} />
            </>
          )}
          <SearchComponent onSearch={handleSearch} loading={loading} submitted={submitted} />
          {error && <div style={S.error}>{error}</div>}
        </section>

        {loading && <Loader />}

        {!loading && submitted && results.length > 0 && (
          <div style={S.stack}>
            <MetricsWidget results={results} query={query} />
            <div style={S.resultsHeader}>
              <span style={S.resultsLabel}>Retrieved Papers</span>
              <span style={S.resultsCount}>{results.length} results</span>
            </div>
            {results.map((p) => <PaperCard key={p.rank} paper={p} />)}
          </div>
        )}

        {!loading && submitted && results.length === 0 && !error && (
          <div style={S.empty}>
            <div style={S.emptyIcon}>∅</div>
            <p style={{ fontSize: 14 }}>No papers found for this claim.</p>
          </div>
        )}
      </main>
    </div>
  );
}