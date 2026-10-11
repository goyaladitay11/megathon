import type { Property, Scenario, Upgrade, StructuredDraft } from "./model";
export const live = true;
const BASE = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8766").replace(/\/$/, "");
const ids: Record<Upgrade,string> = {insulation:"roof_insulation",glazing:"double_glazing",heat_pump:"heat_pump",solar:"solar_pv",thermostat:"smart_thermostat"};
const rev = Object.fromEntries(Object.entries(ids).map(([a,b])=>[b,a])) as Record<string,Upgrade>;
export type PortfolioRow = {property:Property;baseline:Scenario;package:Scenario;selected:Upgrade[]};
async function call<T>(route:string,payload?:unknown,signal?:AbortSignal):Promise<T>{
  let r:Response;
  try {
    r=await fetch(BASE+route,{method:payload===undefined?"GET":"POST",headers:payload===undefined?undefined:{"Content-Type":"application/json"},body:payload===undefined?undefined:JSON.stringify(payload),signal});
  } catch(e) {if(signal?.aborted) throw e; throw Error("Cannot reach FastAPI at "+BASE+". Start the app with python3 scripts/dev.py from the repository root, and open the URL it prints.");}
  if(!r.ok)throw Error("FastAPI "+r.status+" "+(await r.text()).slice(0,500));
  return r.json() as Promise<T>;
}
function toBackend(p:Property){
  return {property_id:p.id,customer_id:p.customerId || null,property_type:p.type==="semi-detached"?"semi_detached":p.type,age:p.yearBuilt,
    floor_area_m2:p.floorArea,region:p.region,bedrooms:p.bedrooms,energy_rating:p.epcRating,
    insulation:p.insulation||"average",heating:p.heating||"gas_boiler",glazing:p.glazing||"double",
    solar:p.solar||"none",smart_controls:p.smartControls??false,current_property_value_gbp:p.currentValue,
    annual_electricity_kwh:p.electricityKwh,annual_gas_kwh:p.gasKwh};
}
const prose=(x:any)=>[x?.summary,...(x?.reasons||[]),...(x?.tradeoffs||[]),...(x?.limitations||[])].filter(Boolean).join("\n\n");
const draft=(id:string,x:any):StructuredDraft | undefined => x ? ({scenarioId:id,summary:x.summary||"",
  sections:[...(x.reasons||[]).map((s:string,i:number)=>({id:"reason-"+i,title:"Why this recommendation",body:s})),...(x.tradeoffs||[]).map((s:string,i:number)=>({id:"tradeoff-"+i,title:"Trade-off",body:s}))],
  why:(x.reasons||[]).map((s:string)=>({title:"Evidence",body:s})),limitations:x.limitations||[]}) : undefined;
function map(p:Property,a:any,e:any,c:any,v:any,selected:Upgrade[],ex:any):Scenario{
  const id=p.id+":"+selected.slice().sort().join("-")+"-live";
  const recs:Scenario["recommendations"]=(a.feasible_retrofits||[]).flatMap((r:any)=>rev[r.retrofit_id]?[{
    id:rev[r.retrofit_id],feasible:r.is_feasible,suitability:r.suitability,reason:r.reason,
    priority:r.priority_order,electricitySavingKwh:r.estimated_annual_electricity_delta_kwh,
    gasSavingKwh:r.estimated_annual_gas_delta_kwh,cost:r.estimated_cost_gbp_avg,
    costLow:r.estimated_cost_gbp_min,costHigh:r.estimated_cost_gbp_max,notes:r.dependencies_or_notes
  }]:[]);
  return {id,propertyId:p.id,mode:"live",selectedRetrofits:selected,score:a.score_details.final_score,
    classification:a.score_details.classification,components:(a.score_details.components||[]).map((x:any)=>({
      id:x.component_name,label:x.component_name,weight:x.weight,score:x.raw_sub_score,reason:x.explanation,contribution:x.contribution})),
    baselineElectricityKwh:e.baseline_electricity_kwh,baselineGasKwh:e.baseline_gas_kwh,
    baselinePurchasedEnergyKwh:e.baseline_purchased_kwh,electricityKwh:e.after_electricity_kwh,
    gasKwh:e.after_gas_kwh,purchasedEnergyKwh:e.after_purchased_kwh,
    electricitySavingKwh:e.electricity_savings_kwh,gasSavingKwh:e.gas_savings_kwh,
    energySavingKwh:e.total_purchased_energy_savings_kwh,
    energyIntensityKwhM2:a.property.energy_intensity_kwh_m2,
    improvementPotentialPct:e.improvement_potential_percent,
    annualEmissionsKg:e.after_electricity_kwh*c.electricity_factor_kg_kwh+e.after_gas_kwh*c.gas_factor_kg_kwh,
    carbonReductionKg:c.net_carbon_saving_kg,carbonSource:c.factor_source,
    baselineValue:v.baseline_value_gbp,valueLow:v.indicative_value_min_gbp,valueHigh:v.indicative_value_max_gbp,
    valueUpliftLowPct:v.indicative_uplift_pct_min,valueUpliftHighPct:v.indicative_uplift_pct_max,
    valueCaveat:v.caveat,cost:selected.reduce((sum,x)=>sum+(recs.find(r=>r.id===x)?.cost??0),0),
    explanation:prose(ex),draft:draft(id,ex),draftSource:"backend",
    currentScoreOnly:true,projectedEpcRating:null,recommendations:recs,
    warnings:a.data_quality_warnings||[],keyIssues:a.key_issue_flags||[],assumptions:a.assumptions_summary||[]};
}
export async function assessProperty(p:Property,_profile?:unknown,signal?:AbortSignal):Promise<Scenario>{
  const a=await call<any>("/api/v1/analyze",toBackend(p),signal);
  const s=await call<any>("/api/v1/simulate",{property_input:toBackend(p),selected_retrofit_ids:[]},signal);
  return map(p,a,s.energy,s.carbon,s.valuation,[],{
    summary:"Your current home assessment was calculated by FastAPI.",
    reasons:a.key_issue_flags||[],tradeoffs:[],limitations:a.assumptions_summary||[]});
}
export async function runScenario(p:Property,selected:Upgrade[],_assessment:Scenario,_question?:string,signal?:AbortSignal):Promise<Scenario>{
  const a=await call<any>("/api/v1/analyze",toBackend(p),signal);
  const s=await call<any>("/api/v1/simulate",{property_input:toBackend(p),selected_retrofit_ids:selected.map(x=>ids[x])},signal);
  return map(p,a,s.energy,s.carbon,s.valuation,selected,{
    summary:"FastAPI calculated your selected renovation scenario.",
    reasons:["Energy and carbon savings are recalculated for your entered property."],
    tradeoffs:[],limitations:[s.energy.disclaimer,s.valuation.caveat]});
}
export async function explainScenario(p:Property,_scenario:Scenario,query:string,signal?:AbortSignal):Promise<{message:string;scenario?:Scenario}>{
  const r=await call<any>("/api/v1/chat",{property_input:toBackend(p),query},signal);
  return {message:prose(r.explanation)};
}
export async function loadPortfolio(signal?:AbortSignal):Promise<{rows:PortfolioRow[];warnings:string[]}>{
  const all=await call<any[]>("/api/v1/properties",undefined,signal);
  const rows=await Promise.all(all.map(async x=>{
    const p:Property={id:x.property_id,name:"Property "+x.property_id,customerId:x.customer_id,
      region:x.region,type:x.property_type,yearBuilt:x.age,floorArea:x.floor_area_m2,bedrooms:x.bedrooms,
      epcRating:x.energy_rating,insulation:x.insulation,heating:x.heating,glazing:x.glazing,solar:x.solar,
      smartControls:x.smart_controls,roofAccess:true,electricityKwh:x.annual_electricity_kwh??0,
      gasKwh:x.annual_gas_kwh??0,currentValue:x.current_property_value_gbp??0,budget:0};
    const a=await call<any>("/api/v1/analyze",toBackend(p),signal);
    const s=await call<any>("/api/v1/simulate",{property_input:toBackend(p),selected_retrofit_ids:[]},signal);
    const baseline=map(p,a,s.energy,s.carbon,s.valuation,[],a.grounded_explanation);
    const selected:Upgrade[]=(a.recommended_package.included_retrofit_ids||[]).map((x:string)=>rev[x]).filter(Boolean);
    const pack=map(p,a,a.energy_simulation,a.carbon_impact,a.valuation_impact,selected,a.grounded_explanation);
    return {property:p,baseline,package:pack,selected};
  }));
  return {rows,warnings:["Only the seven backend demo properties are included."]};
}
