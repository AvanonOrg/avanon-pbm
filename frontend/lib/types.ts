export interface ThinkingStep {
  tool: string;
  step: string;
  timestamp: string;
}

export interface DrugAnalysis {
  drug_name: string;
  ndc?: string;
  strength?: string;
  quantity: number;
  nadac_per_unit: number;
  nadac_total: number;
  plan_price_estimate?: number;
  goodrx_lowest?: number;
  spread_per_unit?: number;
  spread_total?: number;
  annual_savings_100_members?: number;
  recommendation?: string;
}

export interface DiscrepancyReport {
  report_id: string;
  tenant_id: string;
  query: string;
  summary: string;
  drugs: DrugAnalysis[];
  recommendation: string;
  total_annual_savings_100_members: number;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
  thinkingSteps?: ThinkingStep[];
  currentThinkingStep?: string;
  report?: DiscrepancyReport;
  taskId?: string;
}

export type StreamEvent =
  | { type: "thinking"; step: string; tool: string }
  | { type: "text_delta"; delta: string }
  | { type: "done"; reply: string; report?: DiscrepancyReport; task_id?: string; task_status: string }
  | { type: "error"; message: string };
