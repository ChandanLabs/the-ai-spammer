-- ============================================================
-- Placement Nudge Bot — Database Schema for Supabase
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- 1. Hiring Drives
CREATE TABLE IF NOT EXISTS hiring_drives (
    id          VARCHAR(36)  PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    registration_link VARCHAR(512),
    deadline    TIMESTAMP    NOT NULL,
    is_active   BOOLEAN      DEFAULT TRUE,
    created_at  TIMESTAMP    DEFAULT NOW()
);

-- 2. Students
CREATE TABLE IF NOT EXISTS students (
    id               VARCHAR(36)  PRIMARY KEY,
    drive_id         VARCHAR(36)  REFERENCES hiring_drives(id) ON DELETE SET NULL,
    name             VARCHAR(255) NOT NULL,
    roll_number      VARCHAR(100) NOT NULL UNIQUE,
    email            VARCHAR(255),
    branch           VARCHAR(100),
    year             VARCHAR(20),
    phone            VARCHAR(20),
    telegram_chat_id BIGINT,
    status           VARCHAR(20)  NOT NULL DEFAULT 'PENDING'
                         CHECK (status IN ('PENDING', 'REGISTERED', 'BLOCKED')),
    last_nudge_sent_at TIMESTAMP,
    nudge_count      INTEGER      DEFAULT 0,
    created_at       TIMESTAMP    DEFAULT NOW(),
    updated_at       TIMESTAMP    DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_students_drive_id      ON students(drive_id);
CREATE INDEX IF NOT EXISTS idx_students_roll_number   ON students(roll_number);
CREATE INDEX IF NOT EXISTS idx_students_telegram_id   ON students(telegram_chat_id);

-- 3. Nudge Logs
CREATE TABLE IF NOT EXISTS nudge_logs (
    id            VARCHAR(36)  PRIMARY KEY,
    student_id    VARCHAR(36)  NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    drive_id      VARCHAR(36)  NOT NULL REFERENCES hiring_drives(id) ON DELETE CASCADE,
    message_sent  TEXT         NOT NULL,
    nudge_level   INTEGER      DEFAULT 1,
    sent_at       TIMESTAMP    DEFAULT NOW(),
    status        VARCHAR(20)  DEFAULT 'sent',
    error_message TEXT
);

-- Verify
SELECT 'Tables created successfully! ✅' AS result;
