-- Avanon PBM Intelligence — Supabase Schema
-- Run this in: https://supabase.com/dashboard/project/lxmkyoxpkapjvzztcviq/sql/new

CREATE TABLE IF NOT EXISTS pricing_snapshots (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    drug_name TEXT NOT NULL,
    ndc TEXT,
    strength TEXT,
    quantity INTEGER,
    source TEXT,          -- nadac | goodrx | pbm_cvs | pbm_esi | pbm_optum | wac
    price DECIMAL(10,2),
    price_per_unit DECIMAL(10,4),
    pharmacy TEXT,
    state TEXT,
    captured_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_id TEXT UNIQUE NOT NULL,
    tenant_id TEXT NOT NULL,
    title TEXT,
    description TEXT,
    status TEXT DEFAULT 'pending',   -- pending | running | complete | failed
    progress INTEGER DEFAULT 0,
    current_step TEXT,
    result_report_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS reports (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    report_id TEXT UNIQUE NOT NULL,
    tenant_id TEXT NOT NULL,
    query TEXT,
    summary TEXT,
    drugs_json JSONB DEFAULT '[]',
    recommendation TEXT,
    total_annual_savings DECIMAL(15,2),
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    tenant_id TEXT NOT NULL,
    messages_json JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_tasks_tenant ON tasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_reports_tenant ON reports(tenant_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_drug ON pricing_snapshots(drug_name, captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
