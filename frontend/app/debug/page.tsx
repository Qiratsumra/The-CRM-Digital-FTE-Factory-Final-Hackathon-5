"use client";

import { useState } from "react";
import { checkHealth, processTicket } from "@/lib/api";

export default function DebugPage() {
  const [logs, setLogs] = useState<string[]>([]);
  const [testing, setTesting] = useState(false);

  const addLog = (message: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`]);
  };

  const testBackend = async () => {
    setTesting(true);
    setLogs([]);
    
    try {
      addLog('Starting backend test...');
      
      // Test 1: Health check
      addLog('Test 1: Checking health endpoint...');
      const health = await checkHealth();
      addLog(`✅ Health: ${JSON.stringify(health)}`);
      
      // Test 2: Process ticket
      const ticketId = prompt('Enter a ticket ID to test:', '');
      if (ticketId) {
        addLog(`Test 2: Processing ticket ${ticketId}...`);
        addLog('⏳ This may take 30-120 seconds (Render cold start + AI processing)...');
        
        const startTime = Date.now();
        const response = await processTicket(ticketId);
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
        
        addLog(`✅ Processed in ${elapsed}s`);
        addLog(`Response: ${JSON.stringify(response)}`);
      }
      
    } catch (error) {
      addLog(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      if (error instanceof Error && error.stack) {
        addLog(`Stack: ${error.stack}`);
      }
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-900 text-zinc-100 p-8 font-mono text-sm">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Backend Debug Console</h1>
        
        <div className="mb-6">
          <button
            onClick={testBackend}
            disabled={testing}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-semibold"
          >
            {testing ? 'Testing...' : 'Test Backend'}
          </button>
        </div>
        
        <div className="bg-zinc-800 rounded-lg p-4 border border-zinc-700">
          <h2 className="font-bold mb-4">Logs:</h2>
          <div className="space-y-2 max-h-96 overflow-auto">
            {logs.length === 0 ? (
              <p className="text-zinc-500">No logs yet. Click &quot;Test Backend&quot; to start.</p>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="text-zinc-300 border-b border-zinc-700 pb-2">
                  {log}
                </div>
              ))
            )}
          </div>
        </div>
        
        <div className="mt-6 p-4 bg-zinc-800 rounded-lg border border-zinc-700">
          <h2 className="font-bold mb-2">Expected Flow:</h2>
          <ol className="list-decimal list-inside space-y-1 text-zinc-400">
            <li>Health check should return immediately (1-2s)</li>
            <li>First API call may take 30-60s (Render cold start)</li>
            <li>AI processing may take 10-30s</li>
            <li>Total time: 40-120 seconds on cold start</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
