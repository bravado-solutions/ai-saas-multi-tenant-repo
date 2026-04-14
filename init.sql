-- 1. Create Tenants Table 
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    stripe_id TEXT,
    subscription_status TEXT DEFAULT 'inactive',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create Users Table 
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    tenant_id TEXT REFERENCES tenants(id) ON DELETE CASCADE
);

-- 3. Create Usage Tracking Table 
CREATE TABLE IF NOT EXISTS usage_logs (
    id SERIAL PRIMARY KEY,
    tenant_id TEXT REFERENCES tenants(id) ON DELETE CASCADE,
    tokens INTEGER DEFAULT 1,
    endpoint TEXT,
    synced_to_stripe BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Multi-tenant Performance Indexes
CREATE INDEX idx_usage_tenant ON usage_logs(tenant_id);
CREATE INDEX idx_usage_sync ON usage_logs(synced_to_stripe) WHERE synced_to_stripe = FALSE;