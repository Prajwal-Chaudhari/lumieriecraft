"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Activity, Book, Users, Image as ImageIcon, Map, Video, Clapperboard, Receipt, Clock, UserSquare2, RefreshCcw, Camera, Wand2 } from "lucide-react";

export default function ProductionIntelligencePage() {
  const params = useParams();
  const projectId = params.id as string;

  const [activeTab, setActiveTab] = useState("character");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);
  const [currency, setCurrency] = useState("INR");

  const exchangeRates: Record<string, number> = {
    INR: 1,
    USD: 0.012,
    EUR: 0.011,
    GBP: 0.0095,
  };
  
  const formatCurrency = (amount: number) => {
    const rate = exchangeRates[currency];
    const converted = amount * rate;
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      maximumFractionDigits: currency === 'INR' ? 0 : 2
    }).format(converted);
  };

  const fetchIntelligence = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/production/intelligence`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
        if (json.dialogues?.length > 0) {
          setSelectedCharacter(json.dialogues[0].character);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntelligence();
  }, [projectId]);

  if (loading) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center h-full">
        <div className="text-gray-400 flex flex-col items-center gap-3">
          <RefreshCcw className="w-6 h-6 animate-spin" />
          <p>Analyzing script & extracting production intelligence...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return <div className="p-8 text-red-400">Failed to load production data.</div>;
  }

  return (
    <div className="flex flex-col h-full bg-[#0B0E14] text-gray-200 overflow-y-auto pb-20">
      {/* Header */}
      <div className="border-b border-gray-800/60 bg-[#0B0E14] sticky top-0 z-10 px-8 py-5">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-4 font-medium tracking-wide">
          <Link href={`/projects/${projectId}`} className="hover:text-gray-300 transition-colors">&larr; Dashboard</Link>
          <span className="text-gray-700">|</span>
          <span className="text-gray-400 font-semibold tracking-widest text-xs uppercase">Production Intelligence</span>
        </div>
        
        <div className="flex justify-between items-end mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white mb-2 tracking-tight">Production Bibles & Analysis</h1>
            <p className="text-sm text-gray-400">AI-extracted characters, locations, and scene breakdowns derived from your script.</p>
          </div>
          <div className="flex gap-4 items-center">
            <button 
              onClick={fetchIntelligence}
              className="px-4 py-2 bg-gray-800/50 hover:bg-gray-800 text-gray-300 border border-gray-700 rounded-lg text-xs font-medium transition-colors flex items-center gap-2"
            >
              <RefreshCcw className="w-3.5 h-3.5" />
              Regenerate Analysis
            </button>
            <Link 
              href={`/projects/${projectId}/cinematography`}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-medium transition-colors flex items-center shadow-lg shadow-emerald-900/20"
            >
              Continue to Cinematography &rarr;
            </Link>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-8 border-b border-gray-800">
          {[
            { id: "character", label: `Character Bible (${data.characters?.length || 0})` },
            { id: "world", label: `World Bible (${data.locations?.length || 0})` },
            { id: "breakdown", label: `Scene Breakdowns (${data.scenes?.length || 0})` },
            { id: "dialogue", label: `Dialogues (${data.dialogues?.length || 0})` },
            { id: "budget", label: "Estimated Budget" },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-3 text-sm font-medium transition-all relative ${
                activeTab === tab.id ? "text-indigo-400" : "text-gray-500 hover:text-gray-300"
              }`}
            >
              {tab.label}
              {activeTab === tab.id && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-500 rounded-t-full shadow-[0_0_8px_rgba(99,102,241,0.5)]" />
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="p-8">
        {/* CHARACTER BIBLE */}
        {activeTab === "character" && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.characters.map((char: any, i: number) => (
              <div key={i} className="bg-[#11141D] border border-gray-800/80 rounded-xl p-6 shadow-xl flex flex-col h-full">
                <h2 className="text-xl font-bold text-white mb-6 tracking-wide">{char.name}</h2>
                
                <div className="mb-6 flex-1">
                  <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3">Established Facts (Canon)</h3>
                  <ul className="list-disc list-outside ml-4 space-y-2 text-sm text-gray-300 leading-relaxed">
                    {char.established_facts.map((fact: string, j: number) => (
                      <li key={j} className="pl-1">{fact}</li>
                    ))}
                  </ul>
                </div>
                
                <div className="mb-6">
                  <h3 className="text-[10px] font-bold text-indigo-500/70 uppercase tracking-widest mb-3">AI Inferred Profile</h3>
                  <ul className="list-disc list-outside ml-4 space-y-2 text-sm text-indigo-200/80 leading-relaxed">
                    {char.ai_inferred_profile.map((prof: string, j: number) => (
                      <li key={j} className="pl-1">{prof}</li>
                    ))}
                  </ul>
                </div>

                <div className="pt-5 border-t border-gray-800/80">
                  <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Established Costume</h3>
                  <p className="text-sm text-gray-400 italic mb-4">{char.established_costume}</p>
                  
                  <div className="flex items-center justify-between">
                    <div className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest leading-tight w-24">Costume<br/>Recommendation</div>
                  </div>
                  <p className="text-sm text-indigo-200 mt-2">{char.costume_recommendation}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* WORLD BIBLE */}
        {activeTab === "world" && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.locations.map((loc: any, i: number) => (
              <div key={i} className="bg-[#11141D] border border-gray-800/80 rounded-xl p-6 shadow-xl flex flex-col">
                <h2 className="text-lg font-bold text-white mb-2">{loc.name}</h2>
                <p className="text-sm text-gray-400 mb-6 h-10 line-clamp-2">{loc.established_facts[0]}</p>
                
                <div className="mb-6">
                  <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3">Established Facts</h3>
                  <ul className="list-disc list-outside ml-4 space-y-2 text-sm text-gray-300">
                    {loc.established_facts.slice(1).map((fact: string, j: number) => (
                      <li key={j} className="pl-1">{fact}</li>
                    ))}
                  </ul>
                </div>

                <div className="mt-auto">
                  <h3 className="text-[10px] font-bold text-indigo-500/70 uppercase tracking-widest mb-3">AI Inferences</h3>
                  <ul className="list-disc list-outside ml-4 space-y-2 text-sm text-indigo-200/80">
                    {loc.ai_inferences.map((inf: string, j: number) => (
                      <li key={j} className="pl-1">{inf}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* SCENE BREAKDOWNS */}
        {activeTab === "breakdown" && (
          <div className="space-y-4 max-w-4xl">
            {data.scenes.map((scene: any, i: number) => (
              <div key={i} className="bg-[#11141D] border border-gray-800/80 rounded-xl p-6 flex gap-6">
                <div className="w-24 flex-shrink-0 flex flex-col items-center justify-center border-r border-gray-800/80 pr-6">
                  <div className="text-xs text-gray-500 font-bold uppercase mb-1">Scene</div>
                  <div className="text-3xl font-black text-gray-200">{scene.scene_name.split(' ')[0]}</div>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-indigo-100 mb-2">{scene.scene_name.split(' - ').slice(1).join(' - ')}</h3>
                  <p className="text-sm text-gray-400 mb-4 leading-relaxed">{scene.summary}</p>
                  <div className="flex gap-4">
                    <div className="flex items-center gap-1.5 text-xs text-gray-500">
                      <Map className="w-3.5 h-3.5" /> {scene.location}
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-gray-500">
                      <Clock className="w-3.5 h-3.5" /> {scene.time}
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-gray-500">
                      <Users className="w-3.5 h-3.5" /> {scene.characters.join(", ")}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* DIALOGUES */}
        {activeTab === "dialogue" && (
          <div className="flex gap-8 items-start">
            <div className="w-64 flex-shrink-0 flex flex-col gap-2 sticky top-24">
              <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2 px-3">Characters</h3>
              {data.dialogues.map((charData: any) => (
                <button
                  key={charData.character}
                  onClick={() => setSelectedCharacter(charData.character)}
                  className={`text-left px-4 py-3 rounded-lg text-sm font-semibold transition-colors flex justify-between items-center ${
                    selectedCharacter === charData.character 
                    ? "bg-indigo-900/40 text-indigo-200 border border-indigo-500/30" 
                    : "bg-transparent text-gray-400 hover:bg-gray-800/50 border border-transparent hover:border-gray-700/50"
                  }`}
                >
                  {charData.character}
                  <span className="text-[10px] opacity-60">({charData.lines.length})</span>
                </button>
              ))}
            </div>
            
            <div className="flex-1 bg-[#11141D] border border-gray-800/80 rounded-xl p-8 shadow-xl min-h-[500px]">
              {selectedCharacter ? (
                <>
                  <h2 className="text-xl font-bold text-white mb-8 tracking-wide">{selectedCharacter}&apos;S DIALOGUE</h2>
                  <div className="space-y-8">
                    {data.dialogues.find((d: any) => d.character === selectedCharacter)?.lines.map((line: any, i: number) => (
                      <div key={i} className="border-l-2 border-indigo-500/30 pl-5">
                        <div className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-2">SCENE {line.scene}</div>
                        <p className="text-gray-200 text-lg leading-relaxed max-w-2xl font-serif">"{line.text}"</p>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="text-gray-500 h-full flex items-center justify-center">Select a character to view their dialogue.</div>
              )}
            </div>
          </div>
        )}

        {/* BUDGET */}
        {activeTab === "budget" && (
          <div className="max-w-5xl">
            <div className="bg-[#11141D] border border-gray-800/80 rounded-xl p-8 shadow-xl mb-8 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none">
                <Receipt className="w-64 h-64" />
              </div>
              
              <div className="flex justify-between items-start mb-8">
                <div>
                  <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Overall Estimated Budget</h3>
                  <div className="text-5xl font-black text-indigo-400 tracking-tight">
                    {formatCurrency(data.budget.total)}
                  </div>
                </div>
                <select
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  className="bg-gray-800/80 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-1.5 focus:ring-indigo-500 focus:border-indigo-500 z-10 relative"
                >
                  <option value="INR">INR (₹)</option>
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                </select>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
                {[
                  { label: "CAST", val: data.budget.cast },
                  { label: "LOCATION", val: data.budget.location },
                  { label: "EQUIPMENT", val: data.budget.equipment },
                  { label: "LIGHTING", val: data.budget.lighting },
                  { label: "COSTUMES", val: data.budget.costumes },
                  { label: "PROPS", val: data.budget.props },
                  { label: "MAKEUP", val: data.budget.makeup },
                  { label: "CREW", val: data.budget.crew },
                  { label: "TRANSPORT", val: data.budget.transport },
                  { label: "MISC", val: data.budget.misc },
                ].map(item => (
                  <div key={item.label} className="bg-gray-900/50 border border-gray-800/60 rounded-lg p-4">
                    <div className="text-[9px] font-bold text-gray-500 uppercase tracking-widest mb-1.5">{item.label}</div>
                    <div className="text-lg font-semibold text-gray-200">{formatCurrency(item.val)}</div>
                  </div>
                ))}
              </div>
              
              <div className="border-t border-gray-800/80 pt-6">
                <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-4">Calculation Basis (Active Rates)</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-y-3 gap-x-6 text-xs text-gray-400">
                  <div>cast per actor: <span className="text-gray-300 font-medium">{formatCurrency(data.rates.cast_per_actor)}</span></div>
                  <div>location per scene: <span className="text-gray-300 font-medium">{formatCurrency(data.rates.location_per_scene)}</span></div>
                  <div>equipment per scene: <span className="text-gray-300 font-medium">{formatCurrency(data.rates.equipment_per_scene)}</span></div>
                  <div>lighting per scene: <span className="text-gray-300 font-medium">{formatCurrency(data.rates.lighting_per_scene)}</span></div>
                  <div>costume per new: <span className="text-gray-300 font-medium">{formatCurrency(data.rates.costume_per_new)}</span></div>
                  <div>prop per item: <span className="text-gray-300 font-medium">{formatCurrency(data.rates.prop_per_item)}</span></div>
                  <div>makeup per scene: <span className="text-gray-300 font-medium">{formatCurrency(data.rates.makeup_per_scene)}</span></div>
                  <div>crew per scene: <span className="text-gray-300 font-medium">{formatCurrency(data.rates.crew_per_scene)}</span></div>
                  <div>transport per scene: <span className="text-gray-300 font-medium">{formatCurrency(data.rates.transport_per_scene)}</span></div>
                  <div>misc per scene: <span className="text-gray-300 font-medium">{formatCurrency(data.rates.misc_per_scene)}</span></div>
                  <div>night lighting multiplier: <span className="text-gray-300 font-medium">{data.rates.night_lighting_multiplier}x multiplier</span></div>
                  <div>exterior location multiplier: <span className="text-gray-300 font-medium">{data.rates.exterior_location_multiplier}x multiplier</span></div>
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              {data.budget.scene_budgets.map((sb: any) => (
                <div key={sb.scene_id} className="bg-[#11141D] border border-gray-800/80 rounded-xl p-6 flex flex-col md:flex-row justify-between md:items-center gap-6">
                  <div>
                    <div className="text-xs text-indigo-400 font-bold uppercase mb-1">Scene {sb.scene_name.split(' - ')[0]}</div>
                    <div className="text-lg font-bold text-gray-100">{sb.scene_name.split(' - ').slice(1).join(' - ')}</div>
                  </div>
                  
                  <div className="grid grid-cols-3 md:grid-cols-5 gap-x-6 gap-y-2 text-xs text-gray-400">
                     <div>Cast: <span className="text-gray-200">{sb.cast.toLocaleString()}</span></div>
                     <div>Location: <span className="text-gray-200">{sb.location.toLocaleString()}</span></div>
                     <div>Equipment: <span className="text-gray-200">{sb.equipment.toLocaleString()}</span></div>
                     <div>Lighting: <span className="text-gray-200">{sb.lighting.toLocaleString()}</span></div>
                     <div>Costumes: <span className="text-gray-200">{sb.costumes.toLocaleString()}</span></div>
                     <div>Props: <span className="text-gray-200">{sb.props.toLocaleString()}</span></div>
                     <div>Makeup: <span className="text-gray-200">{sb.makeup.toLocaleString()}</span></div>
                     <div>Crew: <span className="text-gray-200">{sb.crew.toLocaleString()}</span></div>
                     <div>Transport: <span className="text-gray-200">{sb.transport.toLocaleString()}</span></div>
                     <div>Misc: <span className="text-gray-200">{sb.misc.toLocaleString()}</span></div>
                  </div>
                  
                  <div className="text-right flex-shrink-0">
                    <div className="text-2xl font-black text-indigo-300">{formatCurrency(sb.total)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
