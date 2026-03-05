# ✅ API Key Authentication Fix

## Problem

Ticket submission worked, but clicking "Get AI Response" failed with:
```
Error: Request timed out. The backend may be starting up (cold start). Please try again.
```

**Root Cause**: The `/agent/process/{ticket_id}` endpoint requires API key authentication, but the frontend wasn't sending it.

## ✅ Solution Applied

### 1. Added API Key to Frontend Requests
**File**: `frontend/lib/api.ts`

```typescript
export async function processTicket(ticketId: string): Promise<AgentProcessResponse> {
  return apiFetch<AgentProcessResponse>(`/agent/process/${encodeURIComponent(ticketId)}`, {
    method: "POST",
    headers: {
      "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "dev-api-key",
    },
  });
}
```

### 2. Created Environment Variable
**File**: `frontend/.env.local`

```env
NEXT_PUBLIC_API_KEY=dev-api-key
```

---

## 🔑 API Key Configuration

### Backend (Render)
Check your Render environment variables:
1. Go to Render Dashboard
2. Select your web service
3. Click "Environment" tab
4. Find `API_KEY` variable

**Default**: `dev-api-key` (if not set, backend uses this default)

### Frontend (Local)
Already configured in `.env.local`:
```env
NEXT_PUBLIC_API_KEY=dev-api-key
```

### Frontend (Production Deployment)
When deploying to Vercel/Netlify, add environment variable:
- **Name**: `NEXT_PUBLIC_API_KEY`
- **Value**: Must match backend's `API_KEY`

---

## 🧪 Test Now

### Step 1: Restart Frontend
```bash
cd frontend
# Stop dev server (Ctrl+C)
npm run dev
```

### Step 2: Submit Ticket
1. Go to `http://localhost:3000/support/webform`
2. Fill out form
3. Submit

### Step 3: Get AI Response
1. Click "Get AI Response" button
2. Wait 30-60 seconds (cold start)
3. Should see AI response!

---

## 🔍 Debugging

### Check Console Logs
```
[API Client] Fetching: https://.../agent/process/{id}
[API Client] Response: 200 OK  ← Success!
[API Client] Data: {ticket_id, status, response}
```

### If Still Failing

**Check Render Logs**:
1. Render Dashboard → Your service → Logs
2. Look for `/agent/process` requests
3. Check for 401 errors (auth failure)

**Verify API Key Matches**:
```bash
# Backend (Render) - Check environment variable
API_KEY=dev-api-key

# Frontend (.env.local)
NEXT_PUBLIC_API_KEY=dev-api-key
```

**Test with curl**:
```bash
curl -X POST https://crm-digital-fte-factory-final-hackathon.onrender.com/agent/process/{ticket_id} \
  -H "X-API-Key: dev-api-key"
```

---

## 📊 Protected Endpoints

These endpoints require `X-API-Key` header:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/agent/process/{id}` | POST | Process ticket with AI |
| `/agent/process-batch` | POST | Process all pending tickets |
| `/customers/lookup` | GET | Find customer by email/phone |
| `/metrics/channels` | GET | Get channel metrics |

---

## ✅ What's Fixed

- ✅ API key sent with protected requests
- ✅ Environment variable configured
- ✅ Example file updated
- ✅ Clear error messages for auth failures

---

## 🚀 Production Deployment

When deploying frontend to Vercel/Netlify:

1. **Add Environment Variables**:
   - `NEXT_PUBLIC_API_URL=https://crm-digital-fte-factory-final-hackathon.onrender.com`
   - `NEXT_PUBLIC_API_KEY=your-production-api-key`

2. **Redeploy** after adding variables

3. **Test** the deployment

---

## 📝 Related Files

| File | Change |
|------|--------|
| `frontend/lib/api.ts` | Added X-API-Key header to processTicket |
| `frontend/.env.local` | Added NEXT_PUBLIC_API_KEY |
| `frontend/.env.local.example` | Updated with API key example |
