/**
 * Mega Brain - Email Validation Module
 * Validates MoneyClub buyer emails via Supabase RPC
 *
 * Uses native fetch (Node.js 18+) instead of Supabase client
 * to avoid assertion errors from dangling WebSocket handles.
 *
 * On successful validation, returns a premium_token for
 * accessing the premium content repository.
 */

// Supabase connection — loaded from environment variables.
// SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env
// Supabase anon keys are public by design (protected by RLS),
// but we load from env to avoid hardcoding in source control.
// See: https://supabase.com/docs/guides/auth#api-keys
const SUPABASE_URL = process.env.SUPABASE_URL || '';
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || '';

const TIMEOUT_MS = 10000;
const MAX_ATTEMPTS = 3;

let attemptCount = 0;

/**
 * Validate a buyer email against MoneyClub database
 * @param {string} email - Email to validate
 * @returns {Promise<{valid: boolean, name?: string, reason?: string, installCount?: number, premium_token?: string}>}
 */
export async function validateEmail(email) {
  if (attemptCount >= MAX_ATTEMPTS) {
    return {
      valid: false,
      reason: 'max_attempts_exceeded',
    };
  }

  attemptCount++;

  if (!email || !email.includes('@')) {
    return {
      valid: false,
      reason: 'invalid_email_format',
    };
  }

  try {
    const response = await fetch(
      `${SUPABASE_URL}/rest/v1/rpc/validate_buyer_email`,
      {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ buyer_email: email.trim().toLowerCase() }),
        signal: AbortSignal.timeout(TIMEOUT_MS),
      }
    );

    if (!response.ok) {
      return {
        valid: false,
        reason: 'validation_error',
      };
    }

    const data = await response.json();

    return {
      valid: data.valid,
      name: data.name || null,
      reason: data.reason || null,
      installCount: data.install_count || 0,
      premium_token: data.premium_token || null,
    };
  } catch (err) {
    if (err.name === 'TimeoutError' || err.name === 'AbortError') {
      return {
        valid: false,
        reason: 'timeout',
      };
    }

    return {
      valid: false,
      reason: 'network_error',
    };
  }
}

/**
 * Get user-friendly error messages in Portuguese
 * @param {string} reason - Error reason code
 * @returns {string} Human-readable message
 */
export function getErrorMessage(reason) {
  const messages = {
    email_not_found: 'Email não autorizado.\nAcesse a página do produto para adquirir acesso.',
    invalid_email_format: 'Formato de email inválido. Verifique e tente novamente.',
    max_attempts_exceeded: 'Número máximo de tentativas excedido. Reinicie o instalador.',
    timeout: 'Tempo de conexão esgotado. Verifique sua internet e tente novamente.',
    network_error: 'Erro de conexão. Verifique sua internet e tente novamente.',
    validation_error: 'Erro na validação. Tente novamente em alguns minutos.',
  };

  return messages[reason] || 'Erro desconhecido. Tente novamente.';
}

export function resetAttempts() {
  attemptCount = 0;
}
