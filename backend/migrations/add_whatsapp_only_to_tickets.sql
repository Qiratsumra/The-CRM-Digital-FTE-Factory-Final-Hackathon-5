-- Migration: Add whatsapp_only column to tickets table
-- Purpose: Mark WhatsApp tickets that should only be visible on WhatsApp app

ALTER TABLE tickets 
ADD COLUMN IF NOT EXISTS whatsapp_only BOOLEAN DEFAULT FALSE;

-- Set whatsapp_only = TRUE for existing WhatsApp channel tickets
UPDATE tickets 
SET whatsapp_only = TRUE 
WHERE source_channel = 'whatsapp';

-- Add index for faster filtering
CREATE INDEX IF NOT EXISTS idx_tickets_whatsapp_only ON tickets(whatsapp_only);
