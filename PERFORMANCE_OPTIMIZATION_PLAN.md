# ⚡ Performance Optimization Plan

## Current Problem

**Ticket + AI Response takes 60-120 seconds** because:

1. Render cold start: 30-60s
2. Gemini embeddings (KB search): 5-15s
3. Gemini AI response: 5-10s
4. Gmail API send: 2-5s
5. Database queries: 1-3s
6. Kafka overhead (not even used!): 0-5s

## 🎯 Hackathon Demo Solution

### Quick Wins (Implement in 30 minutes)

#### 1. **Pre-warm Backend** (Eliminates 30-60s cold start)

Create a simple uptime monitor:

```javascript
// Use a free service like UptimeRobot
// Ping every 5 minutes to keep backend awake
GET https://crm-digital-fte-factory-final-hackathon.onrender.com/health
```

**Result**: Cold start eliminated ✅

#### 2. **Skip Knowledge Base Search** (Eliminates 5-15s)

Modify `agent/runner.py` to skip KB search for demo:

```python
async def _build_context(self, customer_id: str, message: str, channel: str) -> str:
    # Skip KB search for faster response
    kb_results = "Knowledge base search disabled for demo."
    
    # Just get customer info (fast)
    pool = await get_pool()
    async with pool.acquire() as conn:
        customer = await conn.fetchrow(
            "SELECT email, phone, name FROM customers WHERE id = $1", customer_id
        )
    
    customer_name = customer["name"] or "Customer"
    return f"Customer: {customer_name}\nChannel: {channel}\nMessage: {message}"
```

**Result**: 5-15s faster ✅

#### 3. **Use Simpler AI Model** (Eliminates 5-10s)

Change from `gemini-2.5-flash` to faster model:

```python
# In config.py
gemini_model: str = "gemini-1.5-flash"  # Faster than 2.5-flash-preview
```

**Result**: 3-5s faster ✅

#### 4. **Skip Email Sending** (Eliminates 2-5s)

Just store response in DB, don't send email:

```python
# In agent/runner.py
async def process_message(self, ticket_id: str, ...) -> str:
    # ... AI processing ...
    
    # Just store in DB, skip email
    await self._store_response(ticket_id, response)
    # await self._send_email(ticket_id, response)  # Skip this!
    
    return response
```

**Result**: 2-5s faster ✅

### Total Improvement

| Optimization | Time Saved |
|--------------|------------|
| Pre-warm backend | 30-60s |
| Skip KB search | 5-15s |
| Faster AI model | 3-5s |
| Skip email send | 2-5s |
| **TOTAL** | **40-85 seconds faster!** |

**New Response Time: 10-20 seconds** (vs 60-120s currently)

---

## 🚀 Implementation Steps

### Step 1: Pre-warm Backend (2 minutes)

1. Go to https://uptimerobot.com/
2. Add monitor: `https://crm-digital-fte-factory-final-hackathon.onrender.com/health`
3. Set interval: 5 minutes
4. Done! Backend stays awake

### Step 2: Optimize Agent (10 minutes)

Edit `backend/src/agent/runner.py`:

```python
# Line ~85: Skip KB search
kb_results = "KB search disabled for demo speed."

# Line ~120: Use simpler prompt
prompt = f"Respond briefly to: {message}"
```

### Step 3: Deploy to Render (5 minutes)

```bash
cd backend
git add .
git commit -m "Optimize for demo speed"
git push
# Render auto-deploys
```

### Step 4: Test (2 minutes)

```bash
# Wake up backend
curl https://crm-digital-fte-factory-final-hackathon.onrender.com/health

# Submit ticket
curl -X POST https://.../support/submit \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","subject":"Test","message":"Hello"}'

# Process ticket (should be fast now!)
curl -X POST https://.../agent/process/{id} \
  -H "X-API-Key: dev-api-key"
```

---

## 🎯 Alternative: Async Processing (Proper Architecture)

For production (post-hackathon):

### Architecture Change

```
Frontend → Backend (create ticket) → Return immediately
                    ↓
              Kafka Queue
                    ↓
              Worker (async)
                    ↓
         AI Processing (no timeout)
                    ↓
              Email Send
                    ↓
         Frontend polls for status
```

### Benefits
- No timeout issues
- Better user experience
- Scalable
- Proper separation of concerns

### Implementation Time: 2-3 hours

---

## ✅ Recommended for Hackathon

**Do Option 1 (Quick Wins)** - 20 minutes total:

1. ✅ Set up UptimeRobot (2 min)
2. ✅ Skip KB search (5 min)
3. ✅ Use faster AI model (2 min)
4. ✅ Skip email sending (5 min)
5. ✅ Deploy and test (5 min)

**Result**: 10-20 second response times for demo!

---

## 📊 Performance Comparison

| Scenario | Response Time |
|----------|---------------|
| **Current** | 60-120s |
| **Pre-warmed only** | 30-60s |
| **Pre-warmed + No KB** | 15-30s |
| **All optimizations** | 10-20s |
| **Production (async)** | 2-5s (perceived) |

---

## 🎯 Decision

For hackathon demo, I recommend:
1. **Pre-warm backend** (free, easy)
2. **Skip KB search** (temporary for demo)
3. **Show "AI Processing..." UI** (makes wait feel shorter)

After hackathon:
- Implement async processing
- Add proper job queue
- Use webhooks for real-time updates
