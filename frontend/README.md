# Customer Success FTE - Frontend

A Next.js 16 application providing AI-powered customer support across multiple channels (Email, WhatsApp, Web Form).

## Backend API Integration

This frontend is integrated with the backend API deployed on Render:

**Base URL:** `https://crm-digital-fte-factory-final-hackathon.onrender.com`

**API Documentation:** `https://crm-digital-fte-factory-final-hackathon.onrender.com/docs`

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint |
| `/health` | GET | Health check |
| `/support/submit` | POST | Submit support ticket |
| `/support/ticket/{id}` | GET | Get ticket status |
| `/agent/process/{id}` | POST | Process ticket with AI |
| `/agent/process-batch` | POST | Process all pending tickets |
| `/metrics/channels` | GET | Get channel metrics |
| `/customers/lookup` | GET | Look up customer |
| `/webhooks/gmail` | POST | Gmail webhook |
| `/webhooks/whatsapp/rep` | POST | WhatsApp MCP webhook |
| `/webhooks/whatsapp/rep/status` | GET | WhatsApp MCP status |
| `/webhooks/whatsapp/mcp` | POST | WhatsApp MCP (alternative) |
| `/webhooks/whatsapp/status` | GET | WhatsApp MCP status (alternative) |

### Environment Variables

1. Copy `.env.example` to `.env.local`:
   ```bash
   cp .env.example .env.local
   ```

2. Update the values in `.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=https://crm-digital-fte-factory-final-hackathon.onrender.com
   ```

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
