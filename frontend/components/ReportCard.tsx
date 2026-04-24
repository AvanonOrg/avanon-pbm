"use client";

import type { DiscrepancyReport } from "@/lib/types";
import PricingTable from "./PricingTable";

interface ReportCardProps {
  report: DiscrepancyReport;
}

export default function ReportCard({ report }: ReportCardProps) {
  return (
    <div className="mt-4 bg-[#1e1e1e] border border-[#3f3f3f] rounded-2xl p-5">
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-sm font-semibold text-[#ececec]">Discrepancy Analysis Report</h3>
        <span className="text-xs text-[#6b6b6b]">
          {new Date(report.created_at || Date.now()).toLocaleDateString()}
        </span>
      </div>

      {report.summary && (
        <p className="text-sm text-[#8e8ea0] mb-4">{report.summary}</p>
      )}

      <PricingTable drugs={report.drugs || []} />

      {report.total_annual_savings_100_members > 0 && (
        <div className="mt-4 p-3 bg-[#0f2318] border border-[#1a3a25] rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-sm text-[#4ade80] font-medium">Total Potential Annual Savings</span>
            <span className="text-lg font-bold text-[#4ade80]">
              ${report.total_annual_savings_100_members.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
          <p className="text-xs text-[#2d6b3a] mt-1">Per 100 members / year across all analyzed drugs</p>
        </div>
      )}

      {report.recommendation && (
        <div className="mt-3 p-3 bg-[#0f2318] border border-[#1a3a25] rounded-xl">
          <p className="text-xs font-semibold text-[#4ade80] mb-1 uppercase tracking-wide">Recommendation</p>
          <p className="text-sm text-[#a3e8b4]">{report.recommendation}</p>
        </div>
      )}
    </div>
  );
}
