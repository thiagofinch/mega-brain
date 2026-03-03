-- ============================================================
-- Mega Brain — Supabase RPC Setup for L2 Premium Distribution
-- ============================================================
-- Run in Supabase SQL Editor (Dashboard → SQL Editor).
--
-- This script is SELF-CONTAINED: creates tables, sets RLS,
-- inserts config, and creates the RPC function.
--
-- After running, `npx mega-brain-ai install` will work end-to-end.
-- ============================================================


-- ─────────────────────────────────────────────────────────────
-- STEP 0: Create tables if they don't exist
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.moneyclub_buyers (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT,
  email TEXT UNIQUE NOT NULL,
  status TEXT DEFAULT 'active',
  install_count INTEGER DEFAULT 0,
  last_install_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.system_config (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);


-- ─────────────────────────────────────────────────────────────
-- STEP 1: Protect tables from public API reads
-- ─────────────────────────────────────────────────────────────

ALTER TABLE public.moneyclub_buyers ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.moneyclub_buyers FROM anon;
REVOKE ALL ON public.moneyclub_buyers FROM authenticated;

ALTER TABLE public.system_config ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.system_config FROM anon;
REVOKE ALL ON public.system_config FROM authenticated;


-- ─────────────────────────────────────────────────────────────
-- STEP 2: Insert the GitHub PAT
-- ─────────────────────────────────────────────────────────────
-- >>> REPLACE ghp_YOUR_GITHUB_PAT_HERE with your actual PAT <<<
-- PAT scope: contents:read on thiagofinch/mega-brain-premium

INSERT INTO public.system_config (key, value, description)
VALUES (
  'premium_repo_token',
  'ghp_YOUR_GITHUB_PAT_HERE',
  'GitHub PAT for cloning mega-brain-premium repo (contents:read)'
)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();


-- ─────────────────────────────────────────────────────────────
-- STEP 3: Create/replace the RPC function
-- ─────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.validate_buyer_email(buyer_email TEXT)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  _buyer  RECORD;
  _token  TEXT;
  _count  INTEGER;
BEGIN
  buyer_email := LOWER(TRIM(COALESCE(buyer_email, '')));

  IF buyer_email = '' OR POSITION('@' IN buyer_email) = 0 THEN
    RETURN json_build_object(
      'valid', FALSE, 'name', NULL,
      'reason', 'invalid_email_format',
      'install_count', 0, 'premium_token', NULL
    );
  END IF;

  SELECT * INTO _buyer
  FROM public.moneyclub_buyers
  WHERE LOWER(email) = buyer_email AND status = 'active'
  LIMIT 1;

  IF NOT FOUND THEN
    RETURN json_build_object(
      'valid', FALSE, 'name', NULL,
      'reason', 'email_not_found',
      'install_count', 0, 'premium_token', NULL
    );
  END IF;

  UPDATE public.moneyclub_buyers
  SET install_count = COALESCE(install_count, 0) + 1,
      last_install_at = NOW(), updated_at = NOW()
  WHERE id = _buyer.id
  RETURNING install_count INTO _count;

  SELECT value INTO _token
  FROM public.system_config
  WHERE key = 'premium_repo_token';

  RETURN json_build_object(
    'valid', TRUE, 'name', _buyer.name, 'reason', NULL,
    'install_count', _count, 'premium_token', _token
  );
END;
$$;

GRANT EXECUTE ON FUNCTION public.validate_buyer_email(TEXT) TO anon;
GRANT EXECUTE ON FUNCTION public.validate_buyer_email(TEXT) TO authenticated;


-- ============================================================
-- TEST (replace with real email):
--   SELECT public.validate_buyer_email('buyer@example.com');
-- ============================================================
