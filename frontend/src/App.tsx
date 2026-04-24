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
          style={{ position: "fixed", top: 12, right: 16, fontSize: 11, color: "#6b6b6b", background: "none", border: "none", cursor: "pointer", zIndex: 100 }}
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
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", background: "#212121", fontFamily: "ui-sans-serif, system-ui, sans-serif" }}>
      <div style={{ background: "#1a1a1a", borderRadius: 12, padding: 40, width: 380, border: "1px solid #2f2f2f" }}>
        <div style={{ marginBottom: 28 }}>
          <div style={{ fontSize: 28, marginBottom: 10 }}>💊</div>
          <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: "#ececec" }}>PBM Intelligence</h1>
          <p style={{ margin: "6px 0 0", fontSize: 13, color: "#8e8ea0" }}>Sign in to access pass-through pricing analysis</p>
        </div>
        <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="login-input"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="login-input"
          />
          {error && <p style={{ margin: 0, fontSize: 13, color: "#ef4444" }}>{error}</p>}
          <button
            type="submit"
            disabled={loading}
            style={{ padding: "11px", background: loading ? "#3a3a3a" : "#ececec", color: "#1a1a1a", border: "none", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: loading ? "not-allowed" : "pointer", marginTop: 2 }}
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <p style={{ marginTop: 16, fontSize: 12, color: "#4a4a4a", textAlign: "center" }}>
          demo@avanon.ai / pbm2026!
        </p>
      </div>
    </div>
  );
}
