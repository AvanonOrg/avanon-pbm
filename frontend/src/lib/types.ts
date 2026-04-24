export interface DrugPriceAnalysis {
  drug_name: string;
  generic_name?: string;
  ndc?: string;
  strength: string;
  quantity: number;
  nadac_total: number;
  nadac_per_unit: number;
  goodrx_lowest?: number;
  plan_price_estimate?: number;
  spread_dollar: number;
  spread_pct: number;
  flag: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  pass_through_savings: number;
  annual_savings_100_members: number;
  medicaid_citation?: string;
}

export interface DiscrepancyReport {
  report_id: string;
  tenant_id: string;
  generated_at: string;
  query: string;
  summary: string;
  drugs: DrugPriceAnalysis[];
  recommendation: string;
  total_annual_savings_100_members: number;
}

export interface ThinkingStep {
  tool: string;
  step: string;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  report?: DiscrepancyReport;
  task_id?: string;
  task_status?: string;
  isStreaming?: boolean;
  thinkingSteps?: ThinkingStep[];
  currentThinkingStep?: string;
}

export interface ChatResponse {
  reply: string;
  session_id: string;
  report?: DiscrepancyReport;
  task_id?: string;
  task_status: string;
}

export type StreamEvent =
  | { type: "thinking"; step: string; tool: string }
  | { type: "text_delta"; delta: string }
  | { type: "done"; reply: string; report?: DiscrepancyReport; task_id?: string; task_status: string }
  | { type: "error"; message: string };
