"use client";

import { useState } from "react";
import { login } from "@/lib/api";

interface LoginFormProps {
  onSuccess: (token: string) => void;
}

export default function LoginForm({ onSuccess }: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const token = await login(email, password);
      onSuccess(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-full items-center justify-center bg-[#212121]">
      <div className="w-full max-w-sm bg-[#1a1a1a] border border-[#2f2f2f] rounded-2xl p-8">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold text-[#ececec] mb-1">Avanon PBM</h1>
          <p className="text-sm text-[#8e8ea0]">Pass-Through Intelligence Platform</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-[#8e8ea0] mb-1.5 uppercase tracking-wide">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="w-full bg-[#2f2f2f] border border-[#3f3f3f] text-[#ececec] rounded-lg px-4 py-3 text-sm outline-none focus:border-[#6b6b6b] placeholder-[#6b6b6b] transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs text-[#8e8ea0] mb-1.5 uppercase tracking-wide">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full bg-[#2f2f2f] border border-[#3f3f3f] text-[#ececec] rounded-lg px-4 py-3 text-sm outline-none focus:border-[#6b6b6b] placeholder-[#6b6b6b] transition-colors"
            />
          </div>

          {error && (
            <p className="text-sm text-red-400 text-center">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#ececec] text-[#212121] font-medium rounded-lg py-3 text-sm transition-opacity disabled:opacity-50 hover:opacity-90 mt-2"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="text-xs text-[#6b6b6b] text-center mt-6">
          Demo: demo@avanon.ai / pbm2026!
        </p>
      </div>
    </div>
  );
}
