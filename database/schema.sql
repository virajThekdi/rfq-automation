
-- RFQ System Database Schema
-- SQLite 3.x compatible

CREATE TABLE IF NOT EXISTS rfqs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    footer TEXT,
    deadline_minutes INTEGER NOT NULL,
    deadline_time TEXT NOT NULL,  -- ISO format timestamp
    followup_count INTEGER DEFAULT 0,
    followup_interval INTEGER DEFAULT 30,
    status TEXT DEFAULT 'active',  -- active, completed, expired
    created_at TEXT NOT NULL,
    completed_at TEXT,
    total_vendors INTEGER DEFAULT 0,
    responded_vendors INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfq_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    quantity TEXT,
    unit TEXT,
    FOREIGN KEY (rfq_id) REFERENCES rfqs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfq_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    sent_at TEXT NOT NULL,
    responded_at TEXT,
    response_status TEXT DEFAULT 'pending',  -- pending, responded, no_response
    followup_sent_count INTEGER DEFAULT 0,
    last_followup_at TEXT,
    FOREIGN KEY (rfq_id) REFERENCES rfqs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER NOT NULL,
    email_subject TEXT,
    email_body TEXT NOT NULL,
    received_at TEXT NOT NULL,
    parsed_json TEXT,  -- AI-parsed quotation as JSON
    is_quotation INTEGER DEFAULT 0,  -- 0=false, 1=true
    ai_provider TEXT,  -- gemini, openai, grok
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS quotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    price REAL,
    unit TEXT,
    notes TEXT,
    FOREIGN KEY (response_id) REFERENCES responses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    encrypted INTEGER DEFAULT 0,  -- 0=plain, 1=encrypted
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rfqs_status ON rfqs(status);
CREATE INDEX IF NOT EXISTS idx_vendors_rfq ON vendors(rfq_id);
CREATE INDEX IF NOT EXISTS idx_responses_vendor ON responses(vendor_id);
CREATE INDEX IF NOT EXISTS idx_quotations_response ON quotations(response_id);
