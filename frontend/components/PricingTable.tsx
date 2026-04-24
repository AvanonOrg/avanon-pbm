"use client";

import type { DrugAnalysis } from "@/lib/types";

interface PricingTableProps {
  drugs: DrugAnalysis[];
}

function fmt(val?: number, prefix = "$") {
  if (val == null) return "—";
  return `${prefix}${val.toFixed(2)}`;
}

export default function PricingTable({ drugs }: PricingTableProps) {
  if (!drugs.length) return null;

  return (
    <div className="overflow-x-auto rounded-xl border border-[#3f3f3f] mt-4">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-[#2a2a2a] text-[#ececec] text-left">
            <th className="px-4 py-3 font-medium border-b border-[#3f3f3f]">Drug</th>
            <th className="px-4 py-3 font-medium border-b border-[#3f3f3f]">Qty</th>
            <th className="px-4 py-3 font-medium border-b border-[#3f3f3f]">NADAC Total</th>
            <th className="px-4 py-3 font-medium border-b border-[#3f3f3f]">GoodRx Low</th>
            <th className="px-4 py-3 font-medium border-b border-[#3f3f3f]">Spread</th>
            <th className="px-4 py-3 font-medium border-b border-[#3f3f3f]">Annual / 100 Members</th>
          </tr>
        </thead>
        <tbody>
          {drugs.map((d, i) => (
            <tr
              key={i}
              className="border-b border-[#3f3f3f] last:border-0"
              style={{ background: i % 2 === 0 ? "#1a1a1a" : "#1e1e1e" }}
            >
              <td className="px-4 py-3 text-[#ececec] font-medium">
                {d.drug_name}
                {d.strength && <span className="text-[#8e8ea0] ml-1 text-xs">{d.strength}</span>}
              </td>
              <td className="px-4 py-3 text-[#8e8ea0]">{d.quantity}</td>
              <td className="px-4 py-3 text-[#ececec]">{fmt(d.nadac_total)}</td>
              <td className="px-4 py-3 text-[#ececec]">{fmt(d.goodrx_lowest)}</td>
              <td className="px-4 py-3 text-red-400 font-medium">{fmt(d.spread_total)}</td>
              <td className="px-4 py-3 text-green-400 font-medium">{fmt(d.annual_savings_100_members)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
