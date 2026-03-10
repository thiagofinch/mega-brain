# API Documentation - Mega Brain

**REST API Reference - Version 1.0.0**

---

## Overview

The Mega Brain API provides access to sales data, tariff information, and system health metrics.

**Base URL:** `https://api.yourdomain.com/api`

**Response Format:** JSON

**Authentication:** Bearer token (API key)

---

## Authentication

All protected endpoints require an Authorization header:

```
Authorization: Bearer <your-api-key>
```

To obtain an API key:
1. Log in to your account at https://yourdomain.com
2. Go to Settings → API Keys
3. Create a new API key

---

## Security Requirements

### CSRF Protection

State-changing operations (POST, PUT, DELETE, PATCH) require a CSRF token:

```javascript
// 1. Get CSRF token
const { token } = await fetch('/api/csrf-token').then(r => r.json());

// 2. Include token in request headers
const response = await fetch('/api/endpoint', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': token,
  },
  body: JSON.stringify(data),
});
```

### Rate Limiting

All endpoints are rate limited to **100 requests per minute per IP**.

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1234567890
```

When rate limit is exceeded:
```json
{
  "error": "Too many requests",
  "retryAfter": 60
}
```

### CORS

API endpoints only accept requests from whitelisted origins.

Allowed origins (production):
- `https://yourdomain.com`
- `https://www.yourdomain.com`

---

## Endpoints

### GET /api/health

Check API health status.

**Authentication:** None required

**Request:**
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-06T10:00:00.000Z",
  "version": "1.0.0"
}
```

**Status Codes:**
- `200 OK` - Service is healthy

---

### GET /api/sales

Retrieve sales data for a specified time period.

**Authentication:** Optional (required for sensitive data)

**Query Parameters:**

| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-------------|-------------|
| `hours` | integer | No | 24 | 1-168 | Number of hours to retrieve data for |

**Request:**
```http
GET /api/sales?hours=24
```

**Successful Response (200 OK):**
```json
{
  "gmv": 52450.75,
  "orders": 183,
  "avgTicket": 286.61,
  "trend": 12.5,
  "lastUpdated": "2026-03-06T10:00:00.000Z",
  "history": [
    {
      "timestamp": "2026-03-05T10:00:00.000Z",
      "value": 45230.50,
      "currency": "BRL"
    }
  ]
}
```

**Validation Error Response (400 Bad Request):**
```json
{
  "error": "Validation failed",
  "details": [
    {
      "field": "hours",
      "message": "hours must be between 1 and 168"
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid parameters
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

### GET /api/tarifas

Retrieve tariff rate information for Mercado Livre categories.

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-------------|-------------|
| `category` | string | No | all | 1-50 chars | Filter by category ID |

**Request:**
```http
GET /api/tarifas?category=MLB123456
Authorization: Bearer <api-key>
```

**Successful Response (200 OK):**
```json
{
  "categories": [
    {
      "id": "MLB123456",
      "name": "Electronics",
      "rate": 0.11,
      "minFee": 5.00,
      "maxFee": null,
      "lastUpdated": "2026-03-06T10:00:00.000Z"
    }
  ],
  "total": 1
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Insufficient permissions
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

### POST /api/csrf-token

Get a CSRF token for state-changing operations.

**Authentication:** None required

**Request:**
```http
POST /api/csrf-token
Content-Type: application/json
```

**Response (200 OK):**
```json
{
  "token": "a1b2c3d4e5f6...",
  "expiresAt": "2026-03-06T11:00:00.000Z"
}
```

**Status Codes:**
- `200 OK` - Token generated successfully

---

## Error Responses

All API errors follow a consistent format:

```json
{
  "error": "Error message",
  "details": [
    {
      "field": "fieldName",
      "message": "Field-specific error"
    }
  ],
  "requestId": "req_abc123"
}
```

### Standard HTTP Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - CSRF or permission error |
| 404 | Not Found - Resource not found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Unexpected error |
| 503 | Service Unavailable - Maintenance mode |

---

## Data Types

### SalesData

| Field | Type | Description |
|-------|------|-------------|
| `gmv` | float | Gross Merchandise Value in BRL |
| `orders` | integer | Total number of orders |
| `avgTicket` | float | Average ticket value in BRL |
| `trend` | float | Percentage change vs previous period |
| `lastUpdated` | ISO 8601 string | Last data update timestamp |
| `history` | array | Historical data points |

### HistoryPoint

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | ISO 8601 string | Data point timestamp |
| `value` | float | GMV value for this period |
| `currency` | string | Currency code (BRL) |

---

## Example Code

### JavaScript/TypeScript

```typescript
const API_URL = 'https://api.yourdomain.com';

// Get CSRF token
async function getCsrfToken(): Promise<string> {
  const response = await fetch(`${API_URL}/api/csrf-token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  const { token } = await response.json();
  return token;
}

// Get sales data
async function getSalesData(hours: number = 24) {
  const response = await fetch(`${API_URL}/api/sales?hours=${hours}`, {
    headers: {
      'Authorization': `Bearer ${process.env.API_KEY}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error);
  }

  return response.json();
}

// Example with error handling
try {
  const salesData = await getSalesData(24);
  console.log('GMV:', salesData.gmv);
} catch (error) {
  console.error('Failed to fetch sales:', error.message);
}
```

### Python

```python
import requests

API_URL = 'https://api.yourdomain.com'
API_KEY = 'your-api-key'

def get_sales_data(hours=24):
    """Fetch sales data for specified hours."""
    response = requests.get(
        f'{API_URL}/api/sales',
        params={'hours': hours},
        headers={
            'Authorization': f'Bearer {API_KEY}',
        }
    )

    if response.status_code == 429:
        retry_after = response.headers.get('Retry-After', 60)
        raise Exception(f'Rate limited. Retry after {retry_after}s')

    response.raise_for_status()
    return response.json()

# Example
data = get_sales_data(24)
print(f"GMV: R$ {data['gmv']:,.2f}")
```

### cURL

```bash
# Get health status
curl https://api.yourdomain.com/api/health

# Get sales data
curl "https://api.yourdomain.com/api/sales?hours=24" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Get tariff data
curl "https://api.yourdomain.com/api/tarifas?category=MLB123456" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## Changelog

### v1.0.0 (2026-03-06)

- Initial API release
- Endpoints: /health, /sales, /tarifas
- CSRF protection on all state-changing operations
- Rate limiting: 100 requests/minute per IP
- Authentication via Bearer tokens
- Input validation on all query parameters
- Comprehensive error responses

---

## Support

For API issues:
- Documentation: https://docs.yourdomain.com/api
- Email: api-support@yourdomain.com
- GitHub: https://github.com/yourorg/mega-brain/issues

---

**API Version:** 1.0.0
**Last Updated:** 2026-03-06
