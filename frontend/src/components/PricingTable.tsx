import type { DrugPriceAnalysis } from "../lib/types";

interface Props {
  drugs: DrugPriceAnalysis[];
}

const FLAG_COLORS: Record<string, string> = {
  LOW: "#22c55e",
  MEDIUM: "#f59e0b",
  HIGH: "#ef4444",
  CRITICAL: "#7c3aed",
};

export function PricingTable({ drugs }: Props) {
  if (!drugs.length) return null;

  return (
    <div style={{ overflowX: "auto", marginTop: 12 }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr style={{ background: "#2a2a2a", textAlign: "left" }}>
            <th style={th}>Drug</th>
            <th style={th}>Qty</th>
            <th style={th}>NADAC (cost)</th>
            <th style={th}>Plan Est.</th>
            <th style={{ ...th, color: "#ef4444" }}>Spread $</th>
            <th style={{ ...th, color: "#ef4444" }}>Spread %</th>
            <th style={th}>Annual Savings / 100 members</th>
            <th style={th}>Risk</th>
          </tr>
        </thead>
        <tbody>
          {drugs.map((d, i) => (
            <tr key={i} style={{ borderBottom: "1px solid #2f2f2f" }}>
              <td style={td}>
                <strong style={{ color: "#ececec" }}>{d.drug_name}</strong>
                {d.strength && <span style={{ color: "#8e8ea0" }}> {d.strength}</span>}
              </td>
              <td style={td}>{d.quantity}</td>
              <td style={td}>${d.nadac_total.toFixed(2)}</td>
              <td style={td}>
                {d.plan_price_estimate != null
                  ? `$${d.plan_price_estimate.toFixed(2)}`
                  : d.goodrx_lowest != null
                  ? `$${d.goodrx_lowest.toFixed(2)}`
                  : "—"}
              </td>
              <td style={{ ...td, color: "#ef4444", fontWeight: 600 }}>
                ${d.spread_dollar.toFixed(2)}
              </td>
              <td style={{ ...td, color: FLAG_COLORS[d.flag], fontWeight: 600 }}>
                {d.spread_pct.toFixed(0)}%
              </td>
              <td style={{ ...td, color: "#4ade80", fontWeight: 600 }}>
                ${d.annual_savings_100_members.toLocaleString()}
              </td>
              <td style={td}>
                <span
                  style={{
                    background: FLAG_COLORS[d.flag],
                    color: "white",
                    padding: "2px 8px",
                    borderRadius: 999,
                    fontSize: 11,
                    fontWeight: 700,
                  }}
                >
                  {d.flag}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const th: React.CSSProperties = {
  padding: "8px 10px",
  fontWeight: 600,
  fontSize: 12,
  color: "#8e8ea0",
  whiteSpace: "nowrap",
};

const td: React.CSSProperties = {
  padding: "8px 10px",
  verticalAlign: "top",
  color: "#c8c8c8",
};
