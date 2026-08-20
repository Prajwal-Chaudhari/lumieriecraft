"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

export default function CinematographyPage() {
  const params = useParams();
  const projectId = params.id as string;

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [proposing, setProposing] = useState(false);
  const [applying, setApplying] = useState(false);
  const [selectedSceneIdx, setSelectedSceneIdx] = useState(0);

  const fetchData = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/projects/${projectId}/cinematography`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch (err) {
      console.error("Failed to fetch cinematography data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const handlePropose = async () => {
    setProposing(true);
    try {
      await fetch(`http://localhost:8000/api/projects/${projectId}/cinematography/propose`, {
        method: "POST"
      });
      fetchData();
    } catch (err) {
      console.error(err);
    } finally {
      setProposing(false);
    }
  };

  const handleApply = async (proposalId: string) => {
    setApplying(true);
    try {
      await fetch(`http://localhost:8000/api/projects/${projectId}/cinematography/proposals/${proposalId}/apply`, {
        method: "POST"
      });
      fetchData();
    } catch (err) {
      console.error(err);
    } finally {
      setApplying(false);
    }
  };

  const handleReject = async (proposalId: string) => {
    try {
      await fetch(`http://localhost:8000/api/projects/${projectId}/cinematography/proposals/${proposalId}/reject`, {
        method: "POST"
      });
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <div className="p-8">Loading Cinematography...</div>;

  const { plan, proposal, shots } = data || {};

  if (!plan && !proposal) {
    return (
      <div className="p-8 flex flex-col items-center justify-center h-full">
        <h2 className="text-2xl font-semibold mb-4">Cinematography & Color</h2>
        <p className="text-gray-400 mb-8">No cinematography plan exists for this screenplay yet.</p>
        <button 
          onClick={handlePropose} 
          disabled={proposing}
          className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded font-medium disabled:opacity-50"
        >
          {proposing ? "Generating Proposal..." : "Generate Cinematography Proposal"}
        </button>
      </div>
    );
  }

  // Display either the pending proposal or the approved plan
  const isPending = !!proposal;
  const activePlanData = isPending ? proposal.proposed_plan : plan?.scenes_data;
  const scenes = activePlanData?.scenes || [];
  const activeScene = scenes[selectedSceneIdx];

  // For shots, if pending, they are in the proposal JSON. If approved, they are in the `shots` array
  const activeSceneShots = isPending 
    ? activeScene?.shots || [] 
    : shots?.filter((s: any) => s.scene_id === activeScene?.scene_id) || [];

  return (
    <div className="flex h-full overflow-hidden bg-black text-gray-200">
      {/* Left Sidebar - Scene Selector */}
      <div className="w-64 border-r border-gray-800 bg-gray-950 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h2 className="font-bold text-lg">Scenes</h2>
        </div>
        <div className="flex-1 overflow-y-auto">
          {scenes.map((scene: any, idx: number) => (
            <button
              key={scene.scene_id}
              onClick={() => setSelectedSceneIdx(idx)}
              className={`w-full text-left px-4 py-3 border-b border-gray-800/50 hover:bg-gray-900 transition-colors ${selectedSceneIdx === idx ? 'bg-gray-900 border-l-4 border-l-indigo-500' : ''}`}
            >
              <div className="font-medium truncate">{scene.scene_id.replace('_', ' ')}</div>
              <div className="text-xs text-gray-500 mt-1 truncate">{scene.visual_goal}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto flex flex-col">
        {/* Header */}
        <header className="p-6 border-b border-gray-800 bg-gray-900 flex justify-between items-center sticky top-0 z-10">
          <div>
            <h1 className="text-2xl font-bold">Director Review: Cinematography</h1>
            {isPending ? (
              <p className="text-yellow-500 text-sm font-semibold mt-1 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse"></span>
                PENDING PROPOSAL (Script v{proposal.script_version})
              </p>
            ) : (
              <p className="text-emerald-500 text-sm font-semibold mt-1">
                APPROVED PLAN (Script v{plan.script_version})
              </p>
            )}
          </div>
          
          <div className="flex gap-3">
            {isPending && (
              <>
                <button 
                  onClick={() => handleReject(proposal.id)}
                  className="px-4 py-2 border border-red-500/50 text-red-400 hover:bg-red-500/10 rounded font-medium"
                >
                  Reject
                </button>
                <button 
                  onClick={() => handleApply(proposal.id)}
                  disabled={applying}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded font-medium disabled:opacity-50"
                >
                  {applying ? "Applying..." : "Approve & Apply"}
                </button>
              </>
            )}
            {!isPending && (
              <button 
                onClick={handlePropose}
                disabled={proposing}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded text-sm disabled:opacity-50"
              >
                {proposing ? "Generating..." : "Generate New Proposal"}
              </button>
            )}
          </div>
        </header>

        {activeScene && (
          <div className="p-6 space-y-8">
            {/* Color Panel */}
            <section>
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" /></svg>
                Color & Lighting Plan
              </h2>
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  <div>
                    <div className="text-sm text-gray-500 mb-1">Temperature</div>
                    <div className="text-xl font-semibold text-gray-200">{activeScene.color_plan.temperature_kelvin}K</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500 mb-1">Contrast</div>
                    <div className="text-xl font-semibold text-gray-200">{activeScene.color_plan.contrast}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500 mb-1">Saturation</div>
                    <div className="text-xl font-semibold text-gray-200">{activeScene.color_plan.saturation}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500 mb-1">Mood</div>
                    <div className="text-xl font-semibold text-gray-200">{activeScene.color_plan.mood || activeScene.overall_mood}</div>
                  </div>
                </div>

                <div className="mb-8">
                  <div className="text-sm text-gray-500 mb-3">Color Palette</div>
                  <div className="flex flex-wrap gap-4">
                    {activeScene.color_plan.palette?.map((color: any, i: number) => (
                      <div key={i} className="flex flex-col items-center group">
                        <div 
                          className="w-16 h-16 rounded-full border-2 border-gray-700 shadow-lg mb-2"
                          style={{ backgroundColor: color.hex }}
                          title={color.description}
                        />
                        <span className="text-xs font-mono text-gray-400">{color.hex}</span>
                        <span className="text-xs font-medium text-gray-300 mt-1">{color.role}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {activeScene.color_plan.lut && (
                  <div className="bg-gray-950 rounded p-4 border border-gray-800/50">
                    <div className="flex justify-between items-start mb-2">
                      <div className="font-semibold text-indigo-300">LUT Recommendation</div>
                      <div className="text-xs bg-gray-800 px-2 py-1 rounded text-gray-300">{activeScene.color_plan.lut.type}</div>
                    </div>
                    <div className="text-lg mb-1">{activeScene.color_plan.lut.name}</div>
                    <div className="text-sm text-gray-500">{activeScene.color_plan.lut.reason}</div>
                  </div>
                )}
              </div>
            </section>

            {/* Shot Planner */}
            <section>
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                Shot Blueprint
              </h2>
              <div className="space-y-4">
                {activeSceneShots.map((shot: any) => (
                  <div key={shot.shot_id} className="bg-gray-900 border border-gray-800 rounded-lg p-5">
                    <div className="flex gap-4">
                      <div className="w-20 h-20 bg-gray-950 border border-gray-800 rounded flex flex-col items-center justify-center shrink-0">
                        <div className="text-sm text-gray-500">SHOT</div>
                        <div className="font-bold text-lg text-gray-300">{shot.shot_id.split('_').pop()}</div>
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex flex-wrap items-center gap-2 mb-2">
                          <span className="font-bold text-indigo-300 text-lg">{shot.shot_size || 'MEDIUM'}</span>
                          <span className="text-gray-600">•</span>
                          <span className="text-gray-300 font-medium">{shot.camera?.angle || 'EYE LEVEL'}</span>
                          {shot.camera?.focal_length_mm && (
                            <>
                              <span className="text-gray-600">•</span>
                              <span className="text-gray-400">{shot.camera.focal_length_mm}mm</span>
                            </>
                          )}
                          {shot.camera?.movement && shot.camera.movement !== "STATIC" && (
                            <>
                              <span className="text-gray-600">•</span>
                              <span className="text-emerald-400/80 text-sm font-semibold">{shot.camera.movement}</span>
                            </>
                          )}
                        </div>

                        <div className="text-sm font-medium text-gray-200 mb-1">{shot.purpose}</div>
                        <div className="text-xs text-gray-500 italic mb-4">Beat: {shot.story_beat}</div>

                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                          {shot.lighting?.setup && (
                            <div>
                              <div className="text-gray-500 text-xs mb-1">Lighting</div>
                              <div className="text-gray-300">{shot.lighting.setup}</div>
                            </div>
                          )}
                          {shot.composition?.rule_of_thirds !== undefined && (
                            <div>
                              <div className="text-gray-500 text-xs mb-1">Composition</div>
                              <div className="text-gray-300">{shot.composition.rule_of_thirds ? 'Rule of Thirds' : 'Centered'} {shot.composition.symmetry ? '+ Symmetrical' : ''}</div>
                            </div>
                          )}
                          {shot.blocking?.subject_position && (
                            <div>
                              <div className="text-gray-500 text-xs mb-1">Blocking</div>
                              <div className="text-gray-300">{shot.blocking.subject_position}</div>
                            </div>
                          )}
                          {shot.emotion && (
                            <div className="col-span-full md:col-span-1">
                              <div className="text-gray-500 text-xs mb-1">Emotion Focus</div>
                              <div className="text-gray-300">{shot.emotion}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

          </div>
        )}
      </div>
    </div>
  );
}
