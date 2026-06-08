import { useState } from "react";
// Custom hook to manage the state and logic for searching claims
export function useClaimSearch() {
  const [results,   setResults]   = useState([]);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState(null);
  const [submitted, setSubmitted] = useState(false);

// Function to perform the search by sending a POST request to the backend API
  const search = async (query) => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setSubmitted(true);
    setResults([]);

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ post: query }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error: ${res.status}`);
      }
      const data = await res.json();
      setResults(data.results || []);
    } catch (err) {
      setError(err.message || "Failed to connect. Is the FastAPI backend running on port 8000?");
    } finally {
      setLoading(false);
    }
  };

  return { results, loading, error, submitted, search };
}