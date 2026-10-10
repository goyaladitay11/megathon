'use client';
import { useState } from 'react';
import { Activity, LoaderCircle } from 'lucide-react';
import { getHealth } from '@/lib/api';

export function HealthCheck() {
  const [result, setResult] = useState('Not checked');
  const [loading, setLoading] = useState(false);
  async function check() {
    setLoading(true);
    try {
      const health = await getHealth();
      setResult(`${health.status} · ${health.service}`);
    } catch (error) {
      setResult(error instanceof Error ? error.message : 'Unable to connect');
    } finally { setLoading(false); }
  }
  return <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
    <div className="mb-3 flex items-center gap-2"><Activity size={18} /> Backend connection</div>
    <p className="mb-4 text-sm text-slate-400" role="status">{result}</p>
    <button onClick={check} disabled={loading} className="rounded-lg bg-cyan-400 px-4 py-2 font-semibold text-slate-950 disabled:opacity-60">
      {loading ? <span className="flex items-center gap-2"><LoaderCircle className="animate-spin" size={16}/> Checking</span> : 'Test API connection'}
    </button>
  </div>;
}
