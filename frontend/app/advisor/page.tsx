'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, ArrowRight, Bot, Check, ChevronDown, Flame, House, Leaf, Loader2, MessageCircle, Send, ShieldCheck, Sparkles, Sun, Thermometer, Waves, Zap } from 'lucide-react';
import { analyze, chat, getProperties, type Analysis, type ChatResponse, type Property } from '@/lib/green-home-api';

type ChatItem = { id: number; kind: 'user' | 'assistant'; text: string; response?: ChatResponse };
const suggestions = [
  { label: 'Upgrade my insulation', query: 'What if I install roof insulation?', upgrades: ['roof_insulation'] },
  { label: 'Solar + heat pump', query: 'What if I install solar panels and a heat pump?', upgrades: ['solar_pv', 'heat_pump'] },
  { label: 'Compare window upgrades', query: 'What if I install double glazing?', upgrades: ['double_glazing'] },
  { label: 'Current home overview', query: 'Explain my current home energy usage and main weaknesses.' },
];
const upgrades = [
  { id: 'roof_insulation', name: 'Roof insulation', icon: House },
  { id: 'heat_pump', name: 'Heat pump', icon: Thermometer },
  { id: 'solar_pv', name: 'Solar panels', icon: Sun },
  { id: 'double_glazing', name: 'Double glazing', icon: Waves },
  { id: 'smart_thermostat', name: 'Smart thermostat', icon: Zap },
];
const fmt = (n: number | null | undefined) => typeof n === 'number' ? Math.round(n).toLocaleString('en-GB') : 'Unavailable';

export default function AdvisorPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [propertyId, setPropertyId] = useState('P10001');
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loadingProperties, setLoadingProperties] = useState(true);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [chosen, setChosen] = useState<string[]>([]);
  const [history, setHistory] = useState<ChatItem[]>([]);
  const [error, setError] = useState('');
  const end = useRef<HTMLDivElement>(null);
  const nextId = useRef(0);

  useEffect(() => {
    let live = true;
    getProperties().then(data => { if (live) { setProperties(data); setPropertyId(current => data.some(p => p.property_id === current) ? current : (data[0]?.property_id || current)); } })
      .catch(e => { if (live) setError(e instanceof Error ? e.message : 'Cannot connect to the backend'); })
      .finally(() => { if (live) setLoadingProperties(false); });
    return () => { live = false; };
  }, []);

  const selected = properties.find(p => p.property_id === propertyId);
  useEffect(() => {
    if (!selected) return;
    let live = true;
    setAnalysis(null); setHistory([]); setChosen([]); setError(''); setLoadingAnalysis(true);
    analyze(selected).then(result => { if (live) setAnalysis(result); })
      .catch(e => { if (live) setError(`Property analysis: ${e instanceof Error ? e.message : 'Unexpected error'}`); })
      .finally(() => { if (live) setLoadingAnalysis(false); });
    return () => { live = false; };
  }, [selected]);

  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }, [history, busy]);

  async function ask(text: string, ids?: string[]) {
    const cleaned = text.trim();
    if (!cleaned || busy || !selected) return;
    const active = ids === undefined ? chosen : ids;
    setError(''); setMessage(''); setBusy(true);
    const id = ++nextId.current;
    setHistory(prev => [...prev, { id, kind: 'user', text: cleaned }]);
    try {
      const reply = await chat(selected.property_id, cleaned, active);
      setHistory(prev => [...prev, { id: ++nextId.current, kind: 'assistant', text: reply.explanation.summary, response: reply }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to get a response');
    } finally { setBusy(false); }
  }

  function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); void ask(message); }
  function toggle(id: string) { setChosen(old => old.includes(id) ? old.filter(x => x !== id) : [...old, id]); }
  const score = analysis?.score_details;

  return (
    <main className="min-h-screen bg-[#091310] text-[#EAF7EF]">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_80%_0%,rgba(30,114,75,0.15),transparent_44%)]" />
      <div className="relative mx-auto max-w-[1440px] px-4 py-6 sm:px-8 lg:px-12">
        <header className="mb-8 flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-6">
          <div className="flex items-center gap-3"><span className="rounded-2xl bg-emerald-400/15 p-3 text-emerald-300"><Leaf size={22}/></span><div><p className="text-sm font-semibold tracking-[0.22em] text-emerald-300">GREEN HOME TWIN</p><p className="text-xs text-[#91A79B]">Lloyds PS2 · AI energy advisor</p></div></div>
          <Link href="/" className="flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2 text-sm text-[#B8CEC1] hover:border-emerald-400/40 hover:text-white"><ArrowLeft size={15}/> Back to project</Link>
        </header>

        <section className="mb-7 flex flex-wrap items-end justify-between gap-5">
          <div><p className="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-emerald-300">Home intelligence</p><h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">Your home, explained.</h1><p className="mt-2 max-w-xl text-sm text-[#9EB3A7]">Ask what to improve. Explore trade-offs. See modelled savings calculated by the backend, not invented by AI.</p></div>
          <label className="relative flex min-w-60 flex-col gap-2 text-xs text-[#AAC2B2]">Select demonstration property
            <select disabled={loadingProperties || busy} value={propertyId} onChange={e=>setPropertyId(e.target.value)} className="w-full appearance-none rounded-xl border border-white/15 bg-[#15261E] px-4 py-3 pr-9 text-sm font-semibold text-white outline-none focus:border-emerald-400 disabled:opacity-60">
              {properties.map(p=><option key={p.property_id} value={p.property_id}>{p.property_id} · {p.property_type.replaceAll('_',' ')}</option>)}
              {!properties.length && <option>Connecting to API…</option>}
            </select><ChevronDown size={15} className="pointer-events-none absolute bottom-3.5 right-3 text-[#AAC2B2]"/>
          </label>
        </section>
        {error && <div role="alert" className="mb-5 rounded-xl border border-rose-400/30 bg-rose-500/10 p-4 text-sm text-rose-200">{error}<p className="mt-1 text-xs text-rose-200/70">Check that FastAPI is running at the URL in frontend/.env.local. An unreachable API cannot produce real results.</p></div>}

        <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)] xl:grid-cols-[345px_minmax(0,1fr)]">
          <aside className="space-y-5">
            <div className="rounded-[24px] border border-white/10 bg-[#112018] p-5 shadow-xl shadow-black/10">
              <div className="flex items-center justify-between"><p className="text-sm font-semibold">Property snapshot</p><House className="text-emerald-300" size={19}/></div>
              <p className="mt-2 text-xs text-[#97AE9E]">{selected ? `${selected.property_type.replaceAll('_',' ')} · ${selected.floor_area_m2} m² · EPC ${selected.energy_rating}` : 'Waiting for property data'}</p>
              <div className="mt-5 flex items-center justify-between gap-4">
                <div><p className="text-xs text-[#A0B7A9]">Green Home Score</p><div className="mt-1 flex items-baseline gap-1"><strong className="text-5xl font-semibold tracking-tight">{loadingAnalysis ? '…' : (score?.final_score ?? '—')}</strong><span className="text-sm text-[#8EAC9B]">/ 100</span></div><p className="mt-2 text-sm text-emerald-300">{score?.classification ?? 'Analysis pending'}</p></div>
                <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-full border-[9px] border-emerald-400/25 bg-[#1D3627] text-emerald-300"><Leaf size={32}/></div>
              </div>
              {selected && <div className="mt-5 space-y-2 border-t border-white/10 pt-4 text-xs text-[#AAC0B2]"><div className="flex justify-between"><span>Annual electricity</span><span className="text-white">{fmt(selected.annual_electricity_kwh)} kWh</span></div><div className="flex justify-between"><span>Annual gas</span><span className="text-white">{fmt(selected.annual_gas_kwh)} kWh</span></div><div className="flex justify-between"><span>Built</span><span className="text-white">{selected.age}</span></div></div>}
            </div>
            <div className="rounded-[24px] border border-white/10 bg-[#112018] p-5">
              <h2 className="mb-3 text-sm font-semibold">Efficiency insights</h2>
              {loadingAnalysis ? <p className="text-sm text-[#8FA99A]">Analysing property…</p> : !analysis ? <p className="text-sm text-[#8FA99A]">Available when the backend responds.</p> : <>
                <div className="space-y-3">{score?.components.map(c=><div key={c.component_name}><div className="mb-1 flex justify-between gap-2 text-xs text-[#C4D8CB]"><span>{c.component_name}</span><span>{c.contribution.toFixed(1)} / {(c.weight*100).toFixed(0)}</span></div><div className="h-1.5 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-emerald-400" style={{width:`${Math.max(0,Math.min(100,c.contribution/(c.weight*100)*100))}%`}}/></div></div>)}</div>
                {analysis.key_issue_flags.length > 0 && <div className="mt-4 border-t border-white/10 pt-3"><p className="mb-2 text-xs text-amber-200">Key weaknesses</p>{analysis.key_issue_flags.slice(0,4).map((x,i)=><p className="mb-2 text-xs leading-relaxed text-[#B7C6B9]" key={i}>• {x}</p>)}</div>}
                {analysis.data_quality_warnings.length > 0 && <p className="mt-3 text-xs text-amber-200">Data warnings: {analysis.data_quality_warnings.join('; ')}</p>}
              </>}
            </div>
            <div className="rounded-[24px] border border-emerald-400/15 bg-[#123324] p-5 text-xs leading-relaxed text-[#B9D3C1]"><div className="mb-2 flex items-center gap-2 font-semibold text-emerald-300"><ShieldCheck size={17}/> Calculations first, AI second</div>All energy, emissions and valuation numbers shown in the advisor come from your FastAPI result. They are modelled estimates, not guarantees. Demo properties are examples.</div>
          </aside>

          <section className="flex min-h-[710px] flex-col overflow-hidden rounded-[24px] border border-white/10 bg-[#102018] shadow-2xl shadow-black/20">
            <div className="flex items-center justify-between gap-3 border-b border-white/10 px-5 py-5 sm:px-7"><div className="flex items-center gap-3"><span className="rounded-xl bg-emerald-400/15 p-2.5 text-emerald-300"><Bot size={21}/></span><div><h2 className="font-semibold">AI Home Advisor</h2><p className="text-xs text-[#99B3A2]">Grounded what-if analysis</p></div></div><span className="flex items-center gap-2 text-xs text-[#A5C2AE]"><span className="h-2 w-2 rounded-full bg-emerald-400"/> Live API</span></div>
            <div className="flex-1 space-y-6 overflow-y-auto px-4 py-7 sm:px-7">
              <div className="max-w-[590px] rounded-2xl border border-white/10 bg-[#1A3024] p-5"><div className="mb-3 flex items-center gap-2 text-sm font-semibold text-emerald-300"><Sparkles size={16}/> Welcome to your home advisor</div><p className="text-sm leading-7 text-[#D1DED3]">I can help you explore home energy improvements. Choose a suggested question below, or write your own. I’ll show the backend’s actual scenario results, including trade-offs and limitations.</p></div>
              {!history.length && <div><p className="mb-3 text-xs uppercase tracking-[0.16em] text-[#8CA497]">Try asking</p><div className="grid gap-2 sm:grid-cols-2">{suggestions.map(s=><button key={s.label} type="button" disabled={busy || !selected} onClick={()=>void ask(s.query,s.upgrades || [])} className="group flex items-center justify-between gap-2 rounded-xl border border-white/10 bg-white/[0.035] px-4 py-3 text-left text-sm text-[#DAE8DB] hover:border-emerald-400/40 hover:bg-emerald-400/5 disabled:opacity-50"><span>{s.label}</span><ArrowRight size={15} className="text-emerald-300 transition-transform group-hover:translate-x-0.5"/></button>)}</div></div>}
              {history.map(item=><div key={item.id} className={item.kind==='user'?'flex justify-end':'flex justify-start'}>{item.kind==='user' ? <p className="max-w-[85%] rounded-2xl rounded-tr-sm bg-emerald-400 px-4 py-3 text-sm font-medium leading-6 text-[#092017]">{item.text}</p> : <div className="w-full max-w-[740px] rounded-2xl rounded-tl-sm border border-white/10 bg-[#1A3024] p-5"><div className="mb-3 flex items-center gap-2 text-xs font-semibold text-emerald-300"><Bot size={16}/> Scenario response</div><p className="text-sm leading-7 text-[#E2EDE4]">{item.text}</p>{item.response && <ScenarioDetails data={item.response}/>}</div>}</div>)}
              {busy && <div className="flex items-center gap-2 text-sm text-[#A9C1B0]"><Loader2 size={17} className="animate-spin"/> Recalculating with the backend…</div>}
              <div ref={end}/>
            </div>
            <div className="border-t border-white/10 bg-[#0D1B14] p-4 sm:p-6">
              <p className="mb-3 text-xs text-[#A8C1B1]">Apply selected upgrades when you send a question (optional)</p>
              <div className="mb-4 flex flex-wrap gap-2">{upgrades.map(up=>{const Icon=up.icon;const active=chosen.includes(up.id);return <button type="button" key={up.id} aria-pressed={active} disabled={busy} onClick={()=>toggle(up.id)} className={`flex items-center gap-1.5 rounded-full border px-3 py-2 text-xs transition-colors disabled:opacity-50 ${active?'border-emerald-300 bg-emerald-400/20 text-emerald-200':'border-white/15 bg-white/5 text-[#A8BEAE] hover:border-emerald-300/50'}`}>{active?<Check size={13}/>:<Icon size={13}/>} {up.name}</button>})}</div>
              <form onSubmit={submit} className="flex items-center gap-2 rounded-2xl border border-white/15 bg-[#1D3125] p-2 focus-within:border-emerald-400/60"><input value={message} onChange={e=>setMessage(e.target.value)} maxLength={1000} aria-label="Ask the AI home advisor" disabled={busy || !selected} placeholder={chosen.length ? 'Ask about the selected upgrade package…' : 'Ask a what-if question…'} className="min-w-0 flex-1 bg-transparent px-3 py-3 text-sm text-white outline-none placeholder:text-[#839E8C] disabled:opacity-50"/><button disabled={!message.trim() || busy || !selected} aria-label="Send question" type="submit" className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-400 text-[#082016] hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-40"><Send size={17}/></button></form>
              <p className="mt-3 text-center text-[11px] text-[#7C9B86]">Prototype · Estimates only · No certified energy or property valuation</p>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

function ScenarioDetails({data}:{data:ChatResponse}) {
  const energy=data.simulated_energy,carbon=data.simulated_carbon,value=data.simulated_valuation;
  return <div className="mt-5 space-y-4 border-t border-white/10 pt-4">
    <div className="flex flex-wrap items-center gap-2 text-xs"><span className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2.5 py-1 text-emerald-200">{data.grounding_verified ? 'Grounding flag: verified' : 'Grounding not verified'}</span><span className="text-[#8EA998]">{data.engine_used}</span></div>
    <p className="text-xs font-semibold text-[#D5E6D7]">{data.scenario_recognized}</p>
    {data.unsupported_requested_items.length>0&&<div className="rounded-xl border border-amber-400/20 bg-amber-400/5 p-3 text-xs text-amber-100"><p className="font-semibold">Unavailable or infeasible requests</p>{data.unsupported_requested_items.map((x,i)=><p key={i} className="mt-1">• {x}</p>)}</div>}
    {energy&&<div className="grid gap-2 sm:grid-cols-3">{[
      ['Net energy change',`${fmt(energy.total_purchased_energy_savings_kwh)} kWh/yr`],
      ['Improvement potential',energy.improvement_potential_percent==null?'Unavailable':`${energy.improvement_potential_percent.toFixed(1)}%`],
      ['Carbon reduction',carbon?`${carbon.net_carbon_saving_tonnes.toFixed(2)} t CO₂e/yr`:'Unavailable'],
    ].map(([label,number])=><div key={label} className="rounded-xl border border-white/10 bg-[#0F2418] p-3"><p className="text-[11px] text-[#91B19B]">{label}</p><p className="mt-2 text-base font-semibold text-emerald-200">{number}</p></div>)}</div>}
    {energy&&<div className="rounded-xl border border-white/10 p-3"><h3 className="mb-3 text-xs font-semibold">Per-fuel comparison · kWh/year</h3><div className="grid grid-cols-3 gap-2 text-xs text-[#96B2A0]"><span>Fuel</span><span>Before</span><span>After</span></div><div className="mt-2 grid grid-cols-3 gap-2 text-sm"><span>Electricity</span><span>{fmt(energy.baseline_electricity_kwh)}</span><span>{fmt(energy.after_electricity_kwh)}</span></div><div className="mt-2 grid grid-cols-3 gap-2 text-sm"><span>Gas</span><span>{fmt(energy.baseline_gas_kwh)}</span><span>{fmt(energy.after_gas_kwh)}</span></div></div>}
    {value&&<div className="rounded-xl border border-white/10 p-3"><p className="text-xs text-[#96B2A0]">Indicative property-value impact</p><p className="mt-1 font-semibold">{value.is_available?value.uplift_range_label:'Unavailable'}</p>{value.is_available&&<p className="mt-1 text-xs text-[#C2D7C8]">{fmt(value.indicative_value_min_gbp)} – {fmt(value.indicative_value_max_gbp)} GBP</p>}<p className="mt-2 text-xs leading-5 text-[#98B29D]">{value.unavailable_reason || value.caveat}</p></div>}
    {([
      ['Why this scenario?',data.explanation.reasons],
      ['Trade-offs',data.explanation.tradeoffs],
      ['Limitations',data.explanation.limitations],
    ] as const).map(([title,items])=>items.length?<div key={title}><h3 className="mb-2 text-xs font-semibold text-emerald-200">{title}</h3>{items.map((x,i)=><p key={i} className="mb-1.5 text-xs leading-5 text-[#B8CABB]">• {x}</p>)}</div>:null)}
  </div>
}
