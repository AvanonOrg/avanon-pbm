import { useState } from "react";
import { ChatInterface } from "./components/ChatInterface";
import { getToken, clearAuth } from "./lib/api";
import { login } from "./lib/api";

export default function App() {
  const [authed, setAuthed] = useState(!!getToken());
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (authed) {
    return (
      <div>
        <button
          onClick={() => { clearAuth(); setAuthed(false); }}
          style={{ position: "fixed", top: 12, right: 16, fontSize: 11, color: "#94a3b8", background: "none", border: "none", cursor: "pointer", zIndex: 100 }}
        >
          Sign out
        </button>
        <ChatInterface />
      </div>
    );
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email, password);
      setAuthed(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", background: "#f8fafc", fontFamily: "Inter, system-ui, sans-serif" }}>
      <div style={{ background: "#fff", borderRadius: 12, padding: 40, width: 380, border: "1px solid #e2e8f0", boxShadow: "0 4px 24px rgba(0,0,0,0.06)" }}>
        <div style={{ marginBottom: 28 }}>
          <div style={{ fontSize: 24, marginBottom: 8 }}>💊</div>
          <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: "#0f172a" }}>PBM Intelligence</h1>
          <p style={{ margin: "6px 0 0", fontSize: 13, color: "#64748b" }}>Sign in to access pass-through pricing analysis</p>
        </div>
        <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ padding: "10px 12px", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: 14, outline: "none" }}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ padding: "10px 12px", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: 14, outline: "none" }}
          />
          {error && <p style={{ margin: 0, fontSize: 13, color: "#ef4444" }}>{error}</p>}
          <button
            type="submit"
            disabled={loading}
            style={{ padding: "11px", background: loading ? "#94a3b8" : "#0f172a", color: "#fff", border: "none", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: loading ? "not-allowed" : "pointer" }}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
        <p style={{ marginTop: 16, fontSize: 12, color: "#94a3b8", textAlign: "center" }}>
          Demo: demo@avanon.ai / pbm2026!
        </p>
      </div>
    </div>
  );
}
