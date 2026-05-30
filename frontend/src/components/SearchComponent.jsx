import { useState } from "react";

const S = {
  wrap: { maxWidth: 720, margin: "0 auto" },
  box: {
    display: "flex", alignItems: "center",
    background: "#fff", border: "1px solid #e2e8f0", borderRadius: 16,
    boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
    transition: "border-color 0.15s, box-shadow 0.15s",
  },
  boxFocus: {
    borderColor: "#6366f1",
    boxShadow: "0 0 0 4px rgba(99,102,241,0.1)",
  },
  icon: { padding: "0 10px 0 16px", color: "#94a3b8", flexShrink: 0 },
  textarea: {
    flex: 1, padding: "14px 8px", background: "transparent",
    border: "none", outline: "none", fontSize: 14, color: "#334155",
    resize: "none", minHeight: 52, maxHeight: 160, lineHeight: 1.6,
    fontFamily: "inherit",
  },
  btnWrap: { padding: "0 10px 0 0", flexShrink: 0 },
  btn: {
    display: "flex", alignItems: "center", gap: 7,
    padding: "9px 18px", background: "#4f46e5", color: "#fff",
    fontSize: 13, fontWeight: 500, border: "none", borderRadius: 10,
    cursor: "pointer", transition: "background 0.15s",
  },
  btnDisabled: { background: "#a5b4fc", cursor: "not-allowed" },
  hint: { textAlign: "center", fontSize: 12, color: "#94a3b8", marginTop: 10 },
  kbd: {
    background: "#f1f5f9", border: "1px solid #e2e8f0", borderRadius: 4,
    padding: "1px 5px", fontFamily: "monospace", fontSize: 11, color: "#64748b",
  },
};

export default function SearchComponent({ onSearch, loading, submitted }) {
  const [input, setInput]   = useState("");
  const [focused, setFocused] = useState(false);

  const submit = (e) => {
    e?.preventDefault();
    if (input.trim() && !loading) onSearch(input.trim());
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
  };

  const onInput = (e) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + "px";
  };

  const disabled = !input.trim() || loading;

  return (
    <form onSubmit={submit} style={S.wrap}>
      <div style={{ ...S.box, ...(focused ? S.boxFocus : {}) }}>
        <div style={S.icon}>
          <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.5"
            strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="7"/><path d="m21 21-4.35-4.35"/>
          </svg>
        </div>

        <textarea
          style={S.textarea}
          placeholder='Paste a claim to verify… e.g. "Coffee causes cancer according to a new study"'
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onInput={onInput}
          onKeyDown={onKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          rows={1}
        />

        <div style={S.btnWrap}>
          <button type="submit" disabled={disabled}
            style={{ ...S.btn, ...(disabled ? S.btnDisabled : {}) }}>
            {loading ? (
              <>
                <svg className="spin" width="14" height="14" fill="none" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"
                    style={{ opacity: 0.25 }}/>
                  <path fill="currentColor" style={{ opacity: 0.75 }}
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Verifying…
              </>
            ) : (
              <>
                Verify
                <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2"
                  strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
                  <path d="M13 7l5 5m0 0l-5 5m5-5H6"/>
                </svg>
              </>
            )}
          </button>
        </div>
      </div>

      {!submitted && (
        <p style={S.hint}>
          Press <kbd style={S.kbd}>Enter</kbd> to search ·{" "}
          <kbd style={S.kbd}>Shift+Enter</kbd> for new line
        </p>
      )}
    </form>
  );
}