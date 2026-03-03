-- Migration: 002_premium_token
-- Description: Add premium_token delivery to email validation
-- Date: 2026-02-20
-- Product: Mega Brain - [YOUR_PRODUCT_NAME] Edition
--
-- PURPOSE:
--   Closes the "premium_token gap": validate_buyer_email() previously returned
--   only {valid, name, install_count}. After this migration, validated buyers
--   also receive a premium_token used to clone the mega-brain-premium private repo.
--
-- ARCHITECTURE:
--   system_config table stores the shared read-only GitHub PAT.
--   validate_buyer_email() reads it and returns it ONLY to validated buyers.
--   The token never leaves the server unless the buyer is active and validated.
--
-- SECURITY:
--   - system_config has RLS enabled, no anon/public access
--   - Only service_role can read/write system_config directly
--   - The token is exposed only through the SECURITY DEFINER function
--   - The GitHub PAT should have minimal scope: contents:read on mega-brain-premium only

-- ═══════════════════════════════════════════════════════════════
-- TABLE: system_config
-- ═══════════════════════════════════════════════════════════════
-- Key-value store for system-level configuration.
-- Used by RPC functions to retrieve operational secrets.

CREATE TABLE IF NOT EXISTS system_config (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: no public/anon access
ALTER TABLE system_config ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_full_access" ON system_config
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════
-- UPDATED RPC FUNCTION: validate_buyer_email
-- ═══════════════════════════════════════════════════════════════
-- Now returns premium_token from system_config on successful validation.
-- Token is only returned when the buyer is active and email matches.

CREATE OR REPLACE FUNCTION validate_buyer_email(buyer_email TEXT)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  buyer RECORD;
  token TEXT;
BEGIN
  -- Validate buyer
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

  -- Fetch premium token from config
  SELECT value INTO token
  FROM system_config
  WHERE key = 'premium_repo_token';

  RETURN json_build_object(
    'valid', true,
    'name', buyer.name,
    'install_count', buyer.install_count + 1,
    'premium_token', token
  );
END;
$$;

-- Ensure anon can still call the function
GRANT EXECUTE ON FUNCTION validate_buyer_email TO anon;
