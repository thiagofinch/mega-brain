-- Migration: 001_product_buyers
-- Description: Product buyers table for email validation during Mega Brain installation
-- Date: 2026-02-18
-- Product: Mega Brain - [YOUR_PRODUCT_NAME] Edition
--
-- DATA FLOW:
--   Google Sheets (source) → Sync (n8n/Apps Script) → Supabase (source of truth) → CLI validator
--
-- SPREADSHEET COLUMNS:
--   Nome do Cliente | E-mail do Cliente | DDI | DDD | Número do Telefone | Telefone Completo
--
-- SYNC STRATEGY:
--   The Google Sheet is the data entry point (updated by sales team).
--   A sync mechanism (n8n workflow or Google Apps Script) upserts rows
--   into this table using email as the unique key.
--   The CLI installer calls validate_buyer_email() via Supabase anon RPC.

-- ═══════════════════════════════════════════════════════════════
-- TABLE: product_buyers
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS product_buyers (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

  -- From Google Sheets
  name TEXT,                          -- "Nome do Cliente"
  email TEXT NOT NULL UNIQUE,         -- "E-mail do Cliente" (VALIDATOR KEY)
  phone_ddi TEXT,                     -- "DDI do Cliente" (ex: +55)
  phone_ddd TEXT,                     -- "DDD do Cliente" (ex: 11)
  phone_number TEXT,                  -- "Número do Telefone do Cliente"
  phone_full TEXT,                    -- "Telefone Completo do Cliente"

  -- Installer tracking (managed by RPC function)
  product TEXT NOT NULL DEFAULT '[YOUR_PRODUCT_CODE]',
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'refunded')),
  activated_at TIMESTAMPTZ,           -- First install timestamp
  install_count INTEGER DEFAULT 0,    -- How many times installed
  last_install_at TIMESTAMPTZ,        -- Last install timestamp

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast email lookup (used by RPC function)
CREATE INDEX IF NOT EXISTS idx_product_buyers_email ON product_buyers(email);

-- Index for status filtering
CREATE INDEX IF NOT EXISTS idx_product_buyers_status ON product_buyers(status);

-- ═══════════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY
-- ═══════════════════════════════════════════════════════════════
-- No direct access for anon role. All access goes through the RPC function.

ALTER TABLE product_buyers ENABLE ROW LEVEL SECURITY;

-- Service role can do everything (for sync scripts)
CREATE POLICY "service_role_full_access" ON product_buyers
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════
-- RPC FUNCTION: validate_buyer_email
-- ═══════════════════════════════════════════════════════════════
-- Called by the CLI installer (npx mega-brain install)
-- Uses SECURITY DEFINER so anon key can access the table safely
-- Only returns: valid (bool), name (string), install_count (int)
-- Never exposes: phone, email list, or other buyer data

CREATE OR REPLACE FUNCTION validate_buyer_email(buyer_email TEXT)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  buyer RECORD;
BEGIN
  SELECT id, email, name, status, install_count
  INTO buyer
  FROM product_buyers
  WHERE LOWER(email) = LOWER(buyer_email)
  AND status = 'active';

  IF buyer IS NULL THEN
    RETURN json_build_object(
      'valid', false,
      'reason', 'email_not_found'
    );
  END IF;

  -- Update install tracking
  UPDATE product_buyers
  SET install_count = install_count + 1,
      last_install_at = NOW(),
      activated_at = COALESCE(activated_at, NOW()),
      updated_at = NOW()
  WHERE id = buyer.id;

  RETURN json_build_object(
    'valid', true,
    'name', buyer.name,
    'install_count', buyer.install_count + 1
  );
END;
$$;

-- Grant execute to anon role (used by installer CLI via public anon key)
GRANT EXECUTE ON FUNCTION validate_buyer_email TO anon;

-- ═══════════════════════════════════════════════════════════════
-- UPSERT FUNCTION: sync_buyer_from_sheet
-- ═══════════════════════════════════════════════════════════════
-- Called by the sync mechanism (n8n or Google Apps Script)
-- Upserts a row using email as the unique key
-- Preserves install tracking data on update

CREATE OR REPLACE FUNCTION sync_buyer_from_sheet(
  p_name TEXT,
  p_email TEXT,
  p_phone_ddi TEXT DEFAULT NULL,
  p_phone_ddd TEXT DEFAULT NULL,
  p_phone_number TEXT DEFAULT NULL,
  p_phone_full TEXT DEFAULT NULL
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result RECORD;
BEGIN
  INSERT INTO product_buyers (name, email, phone_ddi, phone_ddd, phone_number, phone_full)
  VALUES (p_name, LOWER(TRIM(p_email)), p_phone_ddi, p_phone_ddd, p_phone_number, p_phone_full)
  ON CONFLICT (email) DO UPDATE SET
    name = EXCLUDED.name,
    phone_ddi = COALESCE(EXCLUDED.phone_ddi, product_buyers.phone_ddi),
    phone_ddd = COALESCE(EXCLUDED.phone_ddd, product_buyers.phone_ddd),
    phone_number = COALESCE(EXCLUDED.phone_number, product_buyers.phone_number),
    phone_full = COALESCE(EXCLUDED.phone_full, product_buyers.phone_full),
    updated_at = NOW()
  RETURNING id, email, name INTO result;

  RETURN json_build_object(
    'success', true,
    'id', result.id,
    'email', result.email,
    'name', result.name
  );
END;
$$;

-- Only service_role can call sync (not anon)
-- IMPORTANT: PostgreSQL grants EXECUTE to PUBLIC by default on functions.
-- We must explicitly REVOKE from public/anon to prevent unauthorized inserts.
REVOKE EXECUTE ON FUNCTION sync_buyer_from_sheet FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION sync_buyer_from_sheet FROM anon;
GRANT EXECUTE ON FUNCTION sync_buyer_from_sheet TO service_role;
