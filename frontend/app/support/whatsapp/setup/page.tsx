"use client";

import Link from "next/link";

export default function WhatsAppSetupPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-50 to-zinc-100 dark:from-zinc-950 dark:to-zinc-900">
      <header className="bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm border-b border-zinc-200 dark:border-zinc-800 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <Link href="/" className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100">
            ← Back to Home
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-white dark:bg-zinc-900 rounded-3xl p-8 border-2 border-green-200 dark:border-green-900">
          <div className="text-center mb-8">
            <div className="w-20 h-20 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100 mb-4">
              WhatsApp MCP Setup Guide
            </h1>
            <p className="text-zinc-600 dark:text-zinc-400">
              Set up WhatsApp MCP to receive AI responses directly on WhatsApp
            </p>
          </div>

          {/* What is WhatsApp MCP */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6 mb-8">
            <h2 className="text-xl font-bold text-blue-900 dark:text-blue-100 mb-3">
              What is WhatsApp MCP?
            </h2>
            <p className="text-blue-700 dark:text-blue-300 mb-3">
              WhatsApp MCP is a bridge that connects your personal WhatsApp account to AI applications. It allows the Customer Success FTE system to send and receive WhatsApp messages.
            </p>
            <div className="flex items-start gap-3 mt-4">
              <svg className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="font-medium text-blue-900 dark:text-blue-100">Important Notes:</p>
                <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1 mt-2">
                  <li>• Uses WhatsApp Web API (unofficial)</li>
                  <li>• For development/testing only</li>
                  <li>• Requires Go programming language</li>
                  <li>• Session expires every ~20 days</li>
                  <li>• For production, use Twilio WhatsApp Business API</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Prerequisites */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 mb-4">
              Prerequisites
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-zinc-50 dark:bg-zinc-800 rounded-xl p-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 bg-zinc-200 dark:bg-zinc-700 rounded-lg flex items-center justify-center">
                    <span className="font-bold text-zinc-700 dark:text-zinc-300">1</span>
                  </div>
                  <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">Go Programming Language</h3>
                </div>
                <p className="text-sm text-zinc-600 dark:text-zinc-400 ml-11">
                  Version 1.21 or higher required
                </p>
              </div>

              <div className="bg-zinc-50 dark:bg-zinc-800 rounded-xl p-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 bg-zinc-200 dark:bg-zinc-700 rounded-lg flex items-center justify-center">
                    <span className="font-bold text-zinc-700 dark:text-zinc-300">2</span>
                  </div>
                  <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">WhatsApp Mobile App</h3>
                </div>
                <p className="text-sm text-zinc-600 dark:text-zinc-400 ml-11">
                  For QR code authentication
                </p>
              </div>

              <div className="bg-zinc-50 dark:bg-zinc-800 rounded-xl p-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 bg-zinc-200 dark:bg-zinc-700 rounded-lg flex items-center justify-center">
                    <span className="font-bold text-zinc-700 dark:text-zinc-300">3</span>
                  </div>
                  <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">Git</h3>
                </div>
                <p className="text-sm text-zinc-600 dark:text-zinc-400 ml-11">
                  To clone the repository
                </p>
              </div>

              <div className="bg-zinc-50 dark:bg-zinc-800 rounded-xl p-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 bg-zinc-200 dark:bg-zinc-700 rounded-lg flex items-center justify-center">
                    <span className="font-bold text-zinc-700 dark:text-zinc-300">4</span>
                  </div>
                  <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">Windows (MSYS2)</h3>
                </div>
                <p className="text-sm text-zinc-600 dark:text-zinc-400 ml-11">
                  For C compiler (Windows only)
                </p>
              </div>
            </div>
          </div>

          {/* Setup Steps */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 mb-6">
              Setup Steps
            </h2>

            {/* Step 1 */}
            <div className="mb-6">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-10 h-10 bg-green-600 text-white rounded-xl flex items-center justify-center flex-shrink-0 font-bold">
                  1
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100 mb-2">
                    Install Go
                  </h3>
                  <p className="text-zinc-600 dark:text-zinc-400 mb-4">
                    Download and install Go from <a href="https://go.dev/dl/" target="_blank" className="text-green-600 hover:underline">go.dev/dl</a>
                  </p>
                  <div className="bg-zinc-900 dark:bg-zinc-800 rounded-xl p-4 font-mono text-sm text-green-400">
                    <p># Verify installation</p>
                    <p>go version</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 2 */}
            <div className="mb-6">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-10 h-10 bg-green-600 text-white rounded-xl flex items-center justify-center flex-shrink-0 font-bold">
                  2
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100 mb-2">
                    Clone WhatsApp MCP Repository
                  </h3>
                  <p className="text-zinc-600 dark:text-zinc-400 mb-4">
                    Clone the repository into your backend directory:
                  </p>
                  <div className="bg-zinc-900 dark:bg-zinc-800 rounded-xl p-4 font-mono text-sm text-green-400">
                    <p>cd D:\Hackathon_05\backend</p>
                    <p className="mt-2">git clone https://github.com/lharries/whatsapp-mcp.git</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 3 */}
            <div className="mb-6">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-10 h-10 bg-green-600 text-white rounded-xl flex items-center justify-center flex-shrink-0 font-bold">
                  3
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100 mb-2">
                    Build the Go Bridge
                  </h3>
                  <p className="text-zinc-600 dark:text-zinc-400 mb-4">
                    Navigate to the bridge directory and build:
                  </p>
                  <div className="bg-zinc-900 dark:bg-zinc-800 rounded-xl p-4 font-mono text-sm text-green-400">
                    <p>cd whatsapp-mcp/whatsapp-bridge</p>
                    <p className="mt-2">go build -o whatsapp-bridge.exe main.go</p>
                  </div>
                  <div className="mt-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                    <p className="text-sm text-yellow-800 dark:text-yellow-200">
                      <strong>Windows Users:</strong> You may need to install MSYS2 with ucrt64 C compiler. Download from <a href="https://www.msys2.org/" target="_blank" className="underline">msys2.org</a>
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 4 */}
            <div className="mb-6">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-10 h-10 bg-green-600 text-white rounded-xl flex items-center justify-center flex-shrink-0 font-bold">
                  4
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100 mb-2">
                    Authenticate with QR Code
                  </h3>
                  <p className="text-zinc-600 dark:text-zinc-400 mb-4">
                    Run the bridge and scan the QR code with your WhatsApp mobile app:
                  </p>
                  <div className="bg-zinc-900 dark:bg-zinc-800 rounded-xl p-4 font-mono text-sm text-green-400">
                    <p>go run main.go</p>
                  </div>
                  <div className="mt-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                    <p className="text-sm text-green-800 dark:text-green-200 mb-2">
                      <strong>To scan QR code:</strong>
                    </p>
                    <ol className="text-sm text-green-700 dark:text-green-300 space-y-1">
                      <li>1. Open WhatsApp on your phone</li>
                      <li>2. Go to Settings → Linked Devices</li>
                      <li>3. Tap &quot;Link a Device&quot;</li>
                      <li>4. Scan the QR code shown in terminal</li>
                    </ol>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 5 */}
            <div className="mb-6">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-10 h-10 bg-green-600 text-white rounded-xl flex items-center justify-center flex-shrink-0 font-bold">
                  5
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100 mb-2">
                    Configure Environment
                  </h3>
                  <p className="text-zinc-600 dark:text-zinc-400 mb-4">
                    Update your backend `.env` file:
                  </p>
                  <div className="bg-zinc-900 dark:bg-zinc-800 rounded-xl p-4 font-mono text-sm text-green-400">
                    <p>WHATSAPP_MCP_BRIDGE_PATH=./whatsapp-mcp/whatsapp-bridge</p>
                    <p>WHATSAPP_MCP_ENABLED=true</p>
                    <p>WHATSAPP_POLL_INTERVAL=30</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 6 */}
            <div className="mb-6">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-10 h-10 bg-green-600 text-white rounded-xl flex items-center justify-center flex-shrink-0 font-bold">
                  6
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100 mb-2">
                    Start the Bridge
                  </h3>
                  <p className="text-zinc-600 dark:text-zinc-400 mb-4">
                    Keep the bridge running in a separate terminal:
                  </p>
                  <div className="bg-zinc-900 dark:bg-zinc-800 rounded-xl p-4 font-mono text-sm text-green-400">
                    <p>cd D:\Hackathon_05\backend\whatsapp-mcp\whatsapp-bridge</p>
                    <p className="mt-2">go run main.go</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Verification */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 mb-4">
              Verify Setup
            </h2>
            <div className="bg-zinc-50 dark:bg-zinc-800 rounded-xl p-6">
              <p className="text-zinc-600 dark:text-zinc-400 mb-4">
                Check if the bridge is running:
              </p>
              <div className="bg-zinc-900 dark:bg-zinc-800 rounded-xl p-4 font-mono text-sm text-blue-400 mb-4">
                <p>curl http://localhost:8000/webhooks/whatsapp/status</p>
              </div>
              <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-2">Expected response:</p>
              <div className="bg-zinc-900 dark:bg-zinc-800 rounded-xl p-4 font-mono text-xs text-green-400">
                <p>{`{`}</p>
                <p className="pl-4">&quot;whatsapp_mcp_enabled&quot;: true,</p>
                <p className="pl-4">&quot;bridge_exists&quot;: true,</p>
                <p className="pl-4">&quot;poll_interval&quot;: 30</p>
                <p>{`}`}</p>
              </div>
            </div>
          </div>

          {/* Troubleshooting */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 mb-4">
              Troubleshooting
            </h2>
            <div className="space-y-4">
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
                <h3 className="font-bold text-red-900 dark:text-red-100 mb-2">
                  &quot;WhatsApp database not found&quot;
                </h3>
                <p className="text-sm text-red-700 dark:text-red-300">
                  Run the Go bridge and authenticate with QR code. The database will be created automatically.
                </p>
              </div>

              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
                <h3 className="font-bold text-red-900 dark:text-red-100 mb-2">
                  &quot;Authentication expired&quot;
                </h3>
                <p className="text-sm text-red-700 dark:text-red-300">
                  Re-run <code className="bg-red-100 dark:bg-red-900/30 px-2 py-1 rounded">go run main.go</code> and scan the QR code again. Sessions last ~20 days.
                </p>
              </div>

              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
                <h3 className="font-bold text-red-900 dark:text-red-100 mb-2">
                  &quot;C compiler not found&quot; (Windows)
                </h3>
                <p className="text-sm text-red-700 dark:text-red-300">
                  Install MSYS2 from <a href="https://www.msys2.org/" target="_blank" className="underline">msys2.org</a> and run: <code className="bg-red-100 dark:bg-red-900/30 px-2 py-1 rounded">pacman -S mingw-w64-ucrt-x86_64-gcc</code>
                </p>
              </div>
            </div>
          </div>

          {/* Alternative */}
          <div className="bg-zinc-50 dark:bg-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100 mb-4">
              Alternative: Use Without WhatsApp MCP
            </h2>
            <p className="text-zinc-600 dark:text-zinc-400 mb-4">
              You can still use the WhatsApp support form without setting up WhatsApp MCP. The system will:
            </p>
            <ul className="space-y-2 text-zinc-600 dark:text-zinc-400 mb-4">
              <li className="flex items-start gap-2">
                <svg className="w-5 h-5 text-green-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Create tickets from WhatsApp form submissions
              </li>
              <li className="flex items-start gap-2">
                <svg className="w-5 h-5 text-green-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Process messages with AI
              </li>
              <li className="flex items-start gap-2">
                <svg className="w-5 h-5 text-green-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Display responses on the website
              </li>
              <li className="flex items-start gap-2">
                <svg className="w-5 h-5 text-yellow-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span className="text-yellow-700 dark:text-yellow-300">Won&apos;t send to actual WhatsApp (requires MCP bridge)</span>
              </li>
            </ul>
            <Link
              href="/support/whatsapp"
              className="inline-flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 transition-all"
            >
              Use WhatsApp Form
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
