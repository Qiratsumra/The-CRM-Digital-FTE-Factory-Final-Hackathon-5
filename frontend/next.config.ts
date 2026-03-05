import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow environment variable to be used in browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "https://crm-digital-fte-factory-final-hackathon.onrender.com",
  },
  
  // For Vercel/Netlify deployment - ensure API calls work
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://crm-digital-fte-factory-final-hackathon.onrender.com/:path*',
      },
    ];
  },
  
  // Add headers for CORS preflight
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,DELETE,PATCH,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, X-API-Key' },
        ],
      },
    ];
  },
};

export default nextConfig;
