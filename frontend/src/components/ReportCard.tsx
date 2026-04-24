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
        border: "1px solid #e2e8f0",
        borderRadius: 10,
        padding: 16,
        marginTop: 12,
        background: "#fafafa",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <div>
          <span style={{ fontSize: 11, color: "#94a3b8", fontFamily: "monospace" }}>
            Report #{report.report_id}
          </span>
          <p style={{ margin: "4px 0 0", fontWeight: 600, color: "#1e293b" }}>
            {report.summary}
          </p>
        </div>
        {savings > 0 && (
          <div style={{ textAlign: "right", flexShrink: 0, marginLeft: 16 }}>
            <div style={{ fontSize: 11, color: "#64748b" }}>Est. annual savings</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#16a34a" }}>
              ${savings.toLocaleString()}
            </div>
            <div style={{ fontSize: 11, color: "#94a3b8" }}>per 100 members</div>
          </div>
        )}
      </div>

      <PricingTable drugs={report.drugs} />

      {report.recommendation && (
        <div
          style={{
            marginTop: 12,
            padding: 12,
            background: "#f0fdf4",
            borderLeft: "3px solid #22c55e",
            borderRadius: 4,
            fontSize: 13,
            color: "#166534",
          }}
        >
          <strong>Recommendation:</strong> {report.recommendation}
        </div>
      )}
    </div>
  );
}
