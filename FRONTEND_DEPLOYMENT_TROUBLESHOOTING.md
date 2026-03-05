# Frontend-Backend Connection Troubleshooting Guide

## Issue: Frontend Not Getting Response from Render Backend

### ✅ Backend Status
- **Backend URL**: https://crm-digital-fte-factory-final-hackathon.onrender.com
- **Health Check**: ✅ Working (as of 2026-02-24 06:18 UTC)
- **Status**: `{"status":"healthy","channels":{"email":"active","web_form":"active"}}`

---

## 🔧 Fixes Applied

### 1. **next.config.ts Updated**
Added API rewrites and CORS headers:
```typescript
- API rewrites: `/api/:path*` → Render backend
- CORS headers for all origins
- Environment variable configuration
```

### 2. **Environment Variables**
Created `.env.local` with:
```
NEXT_PUBLIC_API_URL=https://crm-digital-fte-factory-final-hackathon.onrender.com
```

### 3. **API Client Enhanced**
- Added 30-second timeout
- Debug logging in development mode
- Better error messages

### 4. **Form Error Logging**
Added console logging for debugging submission errors

---

## 🚀 How to Deploy Frontend

### Option 1: Vercel (Recommended)

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

3. **Deploy**:
   ```bash
   vercel --prod
   ```

4. **Set Environment Variable** (in Vercel dashboard):
   - Go to Project Settings → Environment Variables
   - Add: `NEXT_PUBLIC_API_URL=https://crm-digital-fte-factory-final-hackathon.onrender.com`
   - Redeploy after adding

### Option 2: Netlify

1. **Build Command**: `npm run build`
2. **Publish Directory**: `.next` or `out` (for static export)
3. **Environment Variables**:
   - Add `NEXT_PUBLIC_API_URL` in Netlify dashboard

### Option 3: Local Testing

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Run development server**:
   ```bash
   npm run dev
   ```

3. **Access**: http://localhost:3000

---

## 🐛 Common Issues & Solutions

### Issue 1: CORS Error
**Error**: `Access to fetch at '...' from origin '...' has been blocked by CORS policy`

**Solution**:
- Backend already has `allow_origins=["*"]` configured
- Check if you're using the correct backend URL
- Clear browser cache and try again

### Issue 2: Render Backend Sleeping
**Symptom**: First request times out or takes 30+ seconds

**Solution**:
- Render free tier sleeps after 15 minutes of inactivity
- First request wakes up the backend (cold start)
- Wait 30-60 seconds for cold start, then retry
- Consider upgrading to Render paid tier for always-on service

**Test Backend**:
```bash
curl https://crm-digital-fte-factory-final-hackathon.onrender.com/health
```

### Issue 3: Mixed Content Error
**Error**: `Mixed Content: The page at 'https://...' was loaded over HTTPS, but requested an insecure resource 'http://...'`

**Solution**:
- Ensure `NEXT_PUBLIC_API_URL` uses `https://`
- Check all API calls use HTTPS

### Issue 4: 401 Unauthorized
**Error**: `Invalid or missing API key`

**Solution**:
- Backend is in `development` mode (auth skipped)
- If in production, add `X-API-Key` header to requests
- Check backend `environment` setting in Render dashboard

### Issue 5: Network Timeout
**Error**: `Network request failed` or timeout

**Solution**:
- Backend might be sleeping (see Issue 2)
- Increase timeout in `api.ts` (currently 30s)
- Check Render logs for errors

---

## 📊 Debugging Steps

### 1. Check Browser Console
Open DevTools (F12) → Console tab
Look for:
- `[API Client] Using BASE_URL: ...`
- `[API Client] Fetching: ...`
- `[WebForm] Submitting ticket...`
- Error messages

### 2. Check Network Tab
Open DevTools → Network tab
- Look for failed requests (red)
- Check request URL, headers, response
- Look for CORS errors

### 3. Test Backend Directly
```bash
# Health check
curl https://crm-digital-fte-factory-final-hackathon.onrender.com/health

# Submit test ticket
curl -X POST https://crm-digital-fte-factory-final-hackathon.onrender.com/support/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "subject": "Test Ticket",
    "category": "general",
    "priority": "medium",
    "message": "This is a test message"
  }'
```

### 4. Check Render Logs
1. Go to Render Dashboard
2. Select your web service
3. Click "Logs" tab
4. Look for errors during request time

---

## 📝 Quick Reference

| Endpoint | URL | Auth Required |
|----------|-----|---------------|
| Health | `/health` | No |
| Submit Ticket | `/support/submit` | No |
| Get Ticket | `/support/ticket/{id}` | No |
| Process Ticket | `/agent/process/{id}` | Yes (dev: skipped) |
| Metrics | `/metrics/channels` | Yes |
| Customer Lookup | `/customers/lookup` | Yes |

**API Key** (for protected endpoints): `dev-api-key` (development only)

---

## 🎯 Next Steps

1. **Deploy Frontend**: Use Vercel for easiest deployment
2. **Test Submission**: Submit a test ticket via web form
3. **Monitor Logs**: Check both frontend (Vercel) and backend (Render) logs
4. **Verify Email**: Ensure Gmail integration is working for response delivery

---

## 📞 Support

If issues persist:
1. Check all console logs (browser + server)
2. Verify environment variables are set correctly
3. Test backend endpoints directly with curl
4. Check Render service status (no outages)
