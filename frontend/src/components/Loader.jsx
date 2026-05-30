const STEPS = [
  { icon: "✦", label: "Expanding query…"         },
  { icon: "◈", label: "Running BM25 retrieval…"  },
  { icon: "◉", label: "Running semantic search…" },
  { icon: "⬡", label: "Fusing ranks via RRF…"    },
  { icon: "◇", label: "Cross-encoder reranking…" },
  { icon: "▲", label: "NLI claim verification…"  },
];

const S = {
  wrap:  { padding: "48px 0", display: "flex", flexDirection: "column", alignItems: "center", gap: 28 },
  steps: { width: 360, display: "flex", flexDirection: "column", gap: 10 },
  row:   { display: "flex", alignItems: "center", gap: 10 },
  icon:  { fontSize: 11, fontFamily: "monospace", color: "#818cf8", width: 14, textAlign: "center", flexShrink: 0 },
  track: { flex: 1, height: 3, background: "#f1f5f9", borderRadius: 10, overflow: "hidden" },
  label: { fontSize: 11, color: "#94a3b8", width: 170, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  foot:  { fontSize: 12, color: "#94a3b8" },
};

export default function Loader() {
  return (
    <div style={S.wrap}>
      <div style={S.steps}>
        {STEPS.map((step, i) => (
          <div key={i} style={{
            ...S.row,
            opacity: 0,
            animation: `fadeInStep 0.4s ease ${(i * 0.35).toFixed(2)}s forwards`,
          }}>
            <span style={S.icon}>{step.icon}</span>
            <div style={S.track}>
              <div style={{
                height: "100%", background: "#c7d2fe", borderRadius: 10,
                animation: `progressBar 2s ease-in-out ${(i * 0.35).toFixed(2)}s infinite`,
              }} />
            </div>
            <span style={S.label}>{step.label}</span>
          </div>
        ))}
      </div>
      <p className="pulse" style={S.foot}>Querying scientific literature…</p>
    </div>
  );
}