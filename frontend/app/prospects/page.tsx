"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken, clearToken } from "@/lib/auth";

type Prospect = {
  id: string;
  company_name: string;
  ein: string | null;
  state: string | null;
  pbm: string | null;
  plan_type: string | null;
  employees: number | null;
  annual_drug_spend: number | string | null;
  estimated_spread_overpayment: number | string | null;
  cfo_email: string | null;
  chro_email: string | null;
  form_5500_year: number | null;
};

type Summary = {
  totals: {
    total_prospects: number | string;
    total_covered_lives: number | string;
    total_drug_spend: number | string;
    total_overpayment: number | string;
  };
  by_pbm: Array<{
    pbm: string;
    prospect_count: number | string;
    covered_lives: number | string;
    overpayment: number | string;
  }>;
};

const fmtMoney = (v: number | string | null) => {
  const n = typeof v === "string" ? parseFloat(v) : v ?? 0;
  if (!n) return "—";
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(2)}B`;
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
};

const fmtNum = (v: number | string | null) => {
  const n = typeof v === "string" ? parseFloat(v) : v ?? 0;
  if (!n) return "—";
  return n.toLocaleString();
};

export default function ProspectsPage() {
  const router = useRouter();
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [pbmFilter, setPbmFilter] = useState<string>("");
  const [stateFilter, setStateFilter] = useState<string>("");

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/");
      return;
    }
    const load = async () => {
      setLoading(true);
      setErr(null);
      try {
        const qs = new URLSearchParams({ path: "list", limit: "200" });
        if (pbmFilter) qs.set("pbm", pbmFilter);
        if (stateFilter) qs.set("state", stateFilter);
        const [listRes, sumRes] = await Promise.all([
          fetch(`/api/prospects?${qs}`, {
            headers: { Authorization: `Bearer ${token}` },
            cache: "no-store",
          }),
          fetch(`/api/prospects?path=summary`, {
            headers: { Authorization: `Bearer ${token}` },
            cache: "no-store",
          }),
        ]);
        if (listRes.status === 401 || sumRes.status === 401) {
          clearToken();
          router.replace("/");
          return;
        }
        if (!listRes.ok) throw new Error(`List failed: ${listRes.status}`);
        if (!sumRes.ok) throw new Error(`Summary failed: ${sumRes.status}`);
        const listData = await listRes.json();
        const sumData = await sumRes.json();
        setProspects(listData.prospects ?? []);
        setSummary(sumData ?? null);
      } catch (e) {
        setErr(String(e));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [pbmFilter, stateFilter, router]);

  const totalOverpay = useMemo(() => {
    if (!summary) return null;
    return fmtMoney(summary.totals.total_overpayment);
  }, [summary]);

  return (
    <main className="min-h-screen bg-[#0f0f0f] text-[#ececec]">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold">Prospect Pipeline</h1>
            <p className="text-sm text-[#8e8ea0] mt-1">
              Self-insured employers sourced from Form 5500 Schedule C filings, joined to PBM service-provider records.
            </p>
          </div>
          <button
            onClick={() => router.push("/chat")}
            className="rounded-lg px-4 py-2 text-sm bg-[#2f2f2f] hover:bg-[#3f3f3f] transition-colors"
          >
            ← Back to chat
          </button>
        </div>

        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card label="Qualified prospects" value={fmtNum(summary.totals.total_prospects)} />
            <Card label="Covered lives" value={fmtNum(summary.totals.total_covered_lives)} />
            <Card label="Annual drug spend" value={fmtMoney(summary.totals.total_drug_spend)} />
            <Card label="Est. annual overpayment" value={totalOverpay ?? "—"} highlight />
          </div>
        )}

        {summary && summary.by_pbm.length > 0 && (
          <div className="mb-8">
            <p className="text-[10px] uppercase tracking-wider text-[#4b4b4b] mb-2">Pipeline by PBM</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {summary.by_pbm.map((p) => (
                <div key={p.pbm} className="bg-[#171717] rounded-xl px-4 py-3 border border-[#2f2f2f]">
                  <div className="flex items-baseline justify-between">
                    <span className="text-sm font-medium">{p.pbm}</span>
                    <span className="text-xs text-[#8e8ea0]">{fmtNum(p.prospect_count)} accounts</span>
                  </div>
                  <div className="mt-1 text-lg font-semibold text-[#ececec]">{fmtMoney(p.overpayment)}</div>
                  <div className="text-xs text-[#8e8ea0]">{fmtNum(p.covered_lives)} covered lives</div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex flex-wrap gap-3 mb-4">
          <select
            value={pbmFilter}
            onChange={(e) => setPbmFilter(e.target.value)}
            className="bg-[#171717] border border-[#2f2f2f] rounded-lg px-3 py-2 text-sm"
          >
            <option value="">All PBMs</option>
            <option value="CVS Caremark">CVS Caremark</option>
            <option value="Express Scripts">Express Scripts</option>
            <option value="OptumRx">OptumRx</option>
          </select>
          <input
            type="text"
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value.toUpperCase().slice(0, 2))}
            placeholder="State (e.g. TX)"
            className="bg-[#171717] border border-[#2f2f2f] rounded-lg px-3 py-2 text-sm w-32"
          />
        </div>

        {loading && <p className="text-[#8e8ea0]">Loading prospects…</p>}
        {err && <p className="text-[#f87171]">Error: {err}</p>}
        {!loading && !err && (
          <div className="bg-[#171717] border border-[#2f2f2f] rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[10px] uppercase tracking-wider text-[#4b4b4b] border-b border-[#2f2f2f]">
                  <th className="px-4 py-3">Company</th>
                  <th className="px-4 py-3">PBM</th>
                  <th className="px-4 py-3">Plan</th>
                  <th className="px-4 py-3">State</th>
                  <th className="px-4 py-3 text-right">Employees</th>
                  <th className="px-4 py-3 text-right">Drug Spend</th>
                  <th className="px-4 py-3 text-right">Est. Overpayment</th>
                </tr>
              </thead>
              <tbody>
                {prospects.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-[#8e8ea0]">
                      No prospects match these filters.
                    </td>
                  </tr>
                ) : (
                  prospects.map((p) => (
                    <tr
                      key={p.id}
                      className="border-b border-[#232323] last:border-b-0 hover:bg-[#1f1f1f] transition-colors"
                    >
                      <td className="px-4 py-3 font-medium">{p.company_name}</td>
                      <td className="px-4 py-3 text-[#8e8ea0]">{p.pbm ?? "—"}</td>
                      <td className="px-4 py-3 text-[#8e8ea0]">{p.plan_type ?? "—"}</td>
                      <td className="px-4 py-3 text-[#8e8ea0]">{p.state ?? "—"}</td>
                      <td className="px-4 py-3 text-right">{fmtNum(p.employees)}</td>
                      <td className="px-4 py-3 text-right">{fmtMoney(p.annual_drug_spend)}</td>
                      <td className="px-4 py-3 text-right font-semibold">{fmtMoney(p.estimated_spread_overpayment)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        <p className="text-xs text-[#4b4b4b] mt-4">
          Source: DOL EFAST2 Form 5500 Schedule C filings · estimated overpayment uses 22% spread × $1,400 per-employee drug-spend baseline.
        </p>
      </div>
    </main>
  );
}

function Card({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div
      className={`rounded-xl px-4 py-4 border ${
        highlight ? "bg-[#1a1a1a] border-[#3f3f3f]" : "bg-[#171717] border-[#2f2f2f]"
      }`}
    >
      <p className="text-[10px] uppercase tracking-wider text-[#4b4b4b]">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-[#ececec]">{value}</p>
    </div>
  );
}
