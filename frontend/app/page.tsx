import { ArrowUpRight, Code2, Database, Rocket } from 'lucide-react';
import Link from 'next/link';
import { HealthCheck } from '@/components/health-check';

const features = [
  { icon: Code2, name: 'Next.js + Tailwind', text: 'Ship a responsive interface quickly.' },
  { icon: Database, name: 'Supabase ready', text: 'Add auth, PostgreSQL, and file storage when needed.' },
  { icon: Rocket, name: 'FastAPI backend', text: 'Build integrations and AI workflows in Python.' },
];

export default function Home() {
  return <main className="mx-auto max-w-5xl px-6 py-14 sm:py-24">
    <div className="mb-10 inline-flex items-center rounded-full border border-cyan-500/30 bg-cyan-500/10 px-4 py-2 text-xs font-semibold tracking-wider text-cyan-300">HACKATHON READY · STARTER KIT</div>
    <h1 className="max-w-3xl text-5xl font-bold tracking-tight sm:text-7xl">Build the idea. <span className="text-cyan-300">Not the boilerplate.</span></h1>
    <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-400">A clean starting point for Megathon. Customize after the challenge is revealed, then build, test, and deploy.</p>
    <Link href="/advisor" className="mt-8 inline-flex items-center gap-2 rounded-xl bg-emerald-400 px-5 py-3 font-semibold text-[#0A2417] hover:bg-emerald-300">Open Green Home AI Advisor <ArrowUpRight size={18}/></Link><div className="mt-12 grid gap-4 md:grid-cols-3">{features.map(({icon: Icon,name,text}) => <div key={name} className="rounded-2xl border border-white/10 bg-white/5 p-6"><Icon className="mb-5 text-cyan-300" /><h2 className="font-semibold">{name}</h2><p className="mt-2 text-sm leading-6 text-slate-400">{text}</p></div>)}</div>
    <div className="mt-10 grid gap-4 md:grid-cols-2"><HealthCheck/><div className="rounded-2xl border border-white/10 bg-white/5 p-5"><h2 className="font-semibold">Next steps <ArrowUpRight className="inline" size={18}/></h2><p className="mt-3 text-sm leading-6 text-slate-400">Run both services locally, connect the API, then deploy. Follow README.md for setup and security notes.</p></div></div>
  </main>;
}
