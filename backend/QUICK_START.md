# Quick Start Guide - Customer Success FTE

## 🚀 Start All Services (Recommended)

**Double-click this file:** `start_all.bat`

This will automatically start:
1. ✅ WhatsApp Bridge (Port 8080)
2. ✅ Backend API (Port 8000)
3. ✅ Frontend (Port 3000)

---

## 📋 Manual Start (If Needed)

### 1. WhatsApp Bridge
```bash
cd D:\Hackathon_05\backend\whatsapp-mcp\whatsapp-bridge
go run main.go
```
**Keep this terminal open!**

### 2. Backend API
```bash
cd D:\Hackathon_05\backend
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend
```bash
cd D:\Hackathon_05\frontend
npm run dev
```

---

## 🌐 Access URLs

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **API Docs** | http://localhost:8000/docs |
| **WhatsApp Form** | http://localhost:3000/support/whatsapp |
| **Email Form** | http://localhost:3000/support/email |
| **Track Ticket** | http://localhost:3000/process |

---

## ✅ Quick Test

1. Open: http://localhost:3000/support/whatsapp
2. Fill in: Name, Phone (+923082931005), Message
3. Click: "Send via WhatsApp"
4. Check your WhatsApp - you'll get a response!

---

## 🛑 Stop All Services

Close all terminal windows or press `Ctrl+C` in each terminal.

---

## 📞 Support

If anything doesn't work:
1. Check if WhatsApp bridge shows "Connected to WhatsApp"
2. Check backend logs for errors
3. Verify database connection in `.env`

---

**Made with ❤️ for Customer Success FTE**
