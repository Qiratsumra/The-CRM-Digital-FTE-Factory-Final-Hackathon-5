-- Migration 002: Add verification token to tickets
-- Created: 2026-02-20
-- Description: Add verification_token and token_expires_at columns for token-based email verification

-- Add verification_token column to tickets table
ALTER TABLE tickets
ADD COLUMN IF NOT EXISTS verification_token VARCHAR(64) UNIQUE;

-- Add token_expires_at column for token expiration
ALTER TABLE tickets
ADD COLUMN IF NOT EXISTS token_expires_at TIMESTAMPTZ;

-- Add index on verification_token for fast lookups
CREATE INDEX IF NOT EXISTS idx_tickets_verification_token ON tickets(verification_token);

-- Set token_expires_at to 24 hours from created_at for existing tickets
UPDATE tickets
SET token_expires_at = created_at + INTERVAL '24 hours'
WHERE token_expires_at IS NULL;

-- Add comment for documentation
COMMENT ON COLUMN tickets.verification_token IS 'Unique token for email verification (expires after 24 hours)';
COMMENT ON COLUMN tickets.token_expires_at IS 'Token expiration timestamp (24 hours from ticket creation)';
