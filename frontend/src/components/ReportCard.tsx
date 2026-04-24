import type { DiscrepancyReport } from "../lib/types";
import { PricingTable } from "./PricingTable";

interface Props {
  report: DiscrepancyReport;
}

export function ReportCard({ report }: Props) {
  const savings = report.total_annual_savings_100_members;

  return (
    <div
      style={{
        border: "1px solid #3f3f3f",
        borderRadius: 10,
        padding: 16,
        marginTop: 14,
        background: "#1a1a1a",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
        <div>
          <span style={{ fontSize: 11, color: "#6b6b6b", fontFamily: "monospace" }}>
            Report #{report.report_id}
          </span>
          <p style={{ margin: "4px 0 0", fontWeight: 600, color: "#ececec" }}>
            {report.summary}
          </p>
        </div>
        {savings > 0 && (
          <div style={{ textAlign: "right", flexShrink: 0, marginLeft: 16 }}>
            <div style={{ fontSize: 11, color: "#8e8ea0" }}>Est. annual savings</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#4ade80" }}>
              ${savings.toLocaleString()}
            </div>
            <div style={{ fontSize: 11, color: "#6b6b6b" }}>per 100 members</div>
          </div>
        )}
      </div>

      <PricingTable drugs={report.drugs} />

      {report.recommendation && (
        <div
          style={{
            marginTop: 12,
            padding: 12,
            background: "#0f2318",
            borderLeft: "3px solid #22c55e",
            borderRadius: 4,
            fontSize: 13,
            color: "#4ade80",
          }}
        >
          <strong style={{ color: "#86efac" }}>Recommendation:</strong>{" "}
          <span style={{ color: "#a7f3c0" }}>{report.recommendation}</span>
        </div>
      )}
    </div>
  );
}
