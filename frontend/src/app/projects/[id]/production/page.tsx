"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Project, Script, ProductionAnalysisResponse, CharacterBibleResponse, WorldBibleResponse, SceneBreakdownResponse,
  fetchProject, fetchScript, getProductionBibles, extractProductionBibles
} from "@/lib/api";

export default function ProductionIntelligencePage() {
  const params = useParams();
  const id = params.id as string;
  
  const [project, setProject] = useState<Project | null>(null);
  const [script, setScript] = useState<Script | null>(null);
  const [bibles, setBibles] = useState<ProductionAnalysisResponse | null>(null);
  
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<"characters" | "worlds" | "scenes">("characters");

  useEffect(() => {
    if (!id) return;
    
    const loadData = async () => {
      try {
        const [pData, sData] = await Promise.all([
          fetchProject(id),
          fetchScript(id).catch(() => null)
        ]);
        setProject(pData);
        setScript(sData);
        
        if (sData?.id) {
          const bData = await getProductionBibles(id, sData.id).catch(() => null);
          setBibles(bData);
        }
      } catch (err: any) {
        setError("Failed to load project details.");
      } finally {
        setLoadingInitial(false);
      }
    };
    
    loadData();
  }, [id]);

  const handleExtract = async () => {
    if (!script?.id) return;
    setExtracting(true);
    setError(null);
    try {
      const result = await extractProductionBibles(id, script.id);
      setBibles(result);
    } catch (err: any) {
      setError(err.message || "Failed to extract production bibles");
    } finally {
      setExtracting(false);
    }
  };

  if (loadingInitial) {
    return <div className="p-8 text-gray-400">Loading Production Intelligence...</div>;
  }

  if (!project) {
    return <div className="p-8 text-red-400">Project not found.</div>;
  }

  if (!script) {
    return (
      <div className="p-8 text-gray-300">
        <h2 className="text-xl mb-4">No Script Found</h2>
        <p>You need an approved script before you can generate production bibles.</p>
        <Link href={`/projects/${id}/script`} className="text-indigo-400 mt-4 inline-block">Go to Script Studio</Link>
      </div>
    );
  }

  const hasData = bibles && (bibles.characters.length > 0 || bibles.world_locations.length > 0 || bibles.scene_breakdowns.length > 0);

  return (
    <div className="flex flex-col h-screen bg-gray-950 text-gray-200 overflow-hidden font-sans">
      {/* Top Navbar */}
      <header className="h-16 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-6 flex-shrink-0">
        <div className="flex items-center space-x-4">
          <Link href={`/projects/${project.id}`} className="text-gray-400 hover:text-white transition-colors">
            &larr; Dashboard
          </Link>
          <div className="h-6 w-px bg-gray-700"></div>
          <h1 className="text-xl font-bold tracking-tight text-white">{project.name} <span className="text-gray-500 font-normal">/ Production Intelligence</span></h1>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-8 relative">
        <div className="max-w-6xl mx-auto space-y-8">
          
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Production Bibles & Analysis</h2>
              <p className="text-gray-400">AI-extracted characters, locations, and scene breakdowns derived from your script.</p>
            </div>
            {!hasData && (
              <button
                onClick={handleExtract}
                disabled={extracting}
                className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-6 py-2 rounded-md font-medium transition-colors shadow-lg shadow-indigo-900/20"
              >
                {extracting ? "Extracting from Script..." : "Extract Production Intelligence"}
              </button>
            )}
            {hasData && (
              <button
                onClick={handleExtract}
                disabled={extracting}
                className="bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-gray-300 px-4 py-2 rounded-md font-medium transition-colors border border-gray-700 text-sm"
              >
                {extracting ? "Regenerating..." : "Regenerate Analysis"}
              </button>
            )}
          </div>

          {error && (
            <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded-md">
              {error}
            </div>
          )}

          {hasData ? (
            <div className="space-y-6">
              <div className="flex space-x-1 border-b border-gray-800">
                <button
                  onClick={() => setActiveTab("characters")}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === "characters" ? "border-indigo-500 text-indigo-400" : "border-transparent text-gray-500 hover:text-gray-300 hover:border-gray-700"
                  }`}
                >
                  Character Bible ({bibles.characters.length})
                </button>
                <button
                  onClick={() => setActiveTab("worlds")}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === "worlds" ? "border-indigo-500 text-indigo-400" : "border-transparent text-gray-500 hover:text-gray-300 hover:border-gray-700"
                  }`}
                >
                  World Bible ({bibles.world_locations.length})
                </button>
                <button
                  onClick={() => setActiveTab("scenes")}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === "scenes" ? "border-indigo-500 text-indigo-400" : "border-transparent text-gray-500 hover:text-gray-300 hover:border-gray-700"
                  }`}
                >
                  Scene Breakdowns ({bibles.scene_breakdowns.length})
                </button>
              </div>

              <div className="py-4">
                {activeTab === "characters" && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {bibles.characters.map((char) => (
                      <div key={char.id} className="bg-gray-900 border border-gray-800 rounded-lg p-6 shadow-sm">
                        <h3 className="text-xl font-bold text-gray-100 uppercase mb-2">{char.name}</h3>
                        {char.description && <p className="text-gray-400 text-sm mb-4">{char.description}</p>}
                        
                        <div className="space-y-3 mt-4 text-sm">
                          {char.appearance && <div><span className="text-gray-500">Appearance:</span> <span className="text-gray-300">{char.appearance}</span></div>}
                          {char.personality && <div><span className="text-gray-500">Personality:</span> <span className="text-gray-300">{char.personality}</span></div>}
                          
                          {char.established_facts.length > 0 && (
                            <div className="mt-4">
                              <h4 className="text-xs uppercase tracking-wider text-gray-500 mb-2">Established Facts (Canon)</h4>
                              <ul className="list-disc list-inside text-gray-300 space-y-1">
                                {char.established_facts.map((fact, i) => <li key={i}>{fact}</li>)}
                              </ul>
                            </div>
                          )}
                          
                          {char.inferred_facts.length > 0 && (
                            <div className="mt-4">
                              <h4 className="text-xs uppercase tracking-wider text-indigo-500/70 mb-2">AI Inferred Profile</h4>
                              <ul className="list-disc list-inside text-indigo-200/70 space-y-1">
                                {char.inferred_facts.map((fact, i) => <li key={i}>{fact}</li>)}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === "worlds" && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {bibles.world_locations.map((loc) => (
                      <div key={loc.id} className="bg-gray-900 border border-gray-800 rounded-lg p-6 shadow-sm">
                        <h3 className="text-xl font-bold text-gray-100 uppercase mb-2">{loc.name}</h3>
                        {loc.description && <p className="text-gray-400 text-sm mb-4">{loc.description}</p>}
                        
                        <div className="space-y-3 mt-4 text-sm">
                          {loc.architecture && <div><span className="text-gray-500">Architecture:</span> <span className="text-gray-300">{loc.architecture}</span></div>}
                          {loc.lighting_characteristics && <div><span className="text-gray-500">Lighting:</span> <span className="text-gray-300">{loc.lighting_characteristics}</span></div>}
                          
                          {loc.established_facts.length > 0 && (
                            <div className="mt-4">
                              <h4 className="text-xs uppercase tracking-wider text-gray-500 mb-2">Established Facts</h4>
                              <ul className="list-disc list-inside text-gray-300 space-y-1">
                                {loc.established_facts.map((fact, i) => <li key={i}>{fact}</li>)}
                              </ul>
                            </div>
                          )}
                          
                          {loc.inferred_facts.length > 0 && (
                            <div className="mt-4">
                              <h4 className="text-xs uppercase tracking-wider text-indigo-500/70 mb-2">AI Inferences</h4>
                              <ul className="list-disc list-inside text-indigo-200/70 space-y-1">
                                {loc.inferred_facts.map((fact, i) => <li key={i}>{fact}</li>)}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === "scenes" && (
                  <div className="space-y-6">
                    {bibles.scene_breakdowns.map((scene) => (
                      <div key={scene.id} className="bg-gray-900 border border-gray-800 rounded-lg p-6 shadow-sm flex flex-col md:flex-row gap-6">
                        <div className="md:w-1/3 border-r border-gray-800 pr-6">
                          <h3 className="text-lg font-bold text-gray-100 uppercase">{scene.location || "Unknown Location"}</h3>
                          <div className="text-indigo-400 text-sm mb-4">{scene.time_of_day || "Unknown Time"}</div>
                          
                          <div className="space-y-2 text-sm">
                            {scene.story_beat && <div><span className="text-gray-500 block text-xs uppercase mb-1">Story Beat</span> <span className="text-gray-300">{scene.story_beat}</span></div>}
                            {scene.emotional_beat && <div className="mt-3"><span className="text-gray-500 block text-xs uppercase mb-1">Emotional Beat</span> <span className="text-gray-300">{scene.emotional_beat}</span></div>}
                          </div>
                        </div>
                        
                        <div className="md:w-2/3 space-y-4 text-sm">
                          {scene.narrative_purpose && (
                            <div>
                              <h4 className="text-xs uppercase tracking-wider text-gray-500 mb-1">Narrative Purpose</h4>
                              <p className="text-gray-300">{scene.narrative_purpose}</p>
                            </div>
                          )}
                          {scene.visual_context && (
                            <div>
                              <h4 className="text-xs uppercase tracking-wider text-gray-500 mb-1">Visual Context</h4>
                              <p className="text-gray-300">{scene.visual_context}</p>
                            </div>
                          )}
                          {scene.props && scene.props.length > 0 && (
                            <div>
                              <h4 className="text-xs uppercase tracking-wider text-gray-500 mb-1">Props Needed</h4>
                              <div className="flex flex-wrap gap-2 mt-1">
                                {scene.props.map((prop, i) => (
                                  <span key={i} className="bg-gray-800 border border-gray-700 text-gray-300 px-2 py-1 rounded text-xs">{prop}</span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            !extracting && (
              <div className="flex flex-col items-center justify-center py-20 bg-gray-900/50 border border-gray-800 border-dashed rounded-xl">
                <svg className="w-16 h-16 text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <h3 className="text-xl font-medium text-gray-300 mb-2">No Intelligence Extracted Yet</h3>
                <p className="text-gray-500 text-center max-w-md">
                  Click the extract button above to let AI analyze your script and build production bibles for characters, worlds, and scenes.
                </p>
              </div>
            )
          )}
        </div>
      </main>
    </div>
  );
}
