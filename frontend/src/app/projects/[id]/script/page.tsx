"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { 
  Project, Script, Scene, ScriptProposal,
  fetchProject, fetchScript, proposeScriptStandardization, 
  proposeSceneFix, applyScriptProposal, rejectScriptProposal
} from "@/lib/api";

export default function ScriptStudioPage() {
  const params = useParams();
  const id = params.id as string;
  
  const [project, setProject] = useState<Project | null>(null);
  const [script, setScript] = useState<Script | null>(null);
  const [proposal, setProposal] = useState<ScriptProposal | null>(null);
  
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null);
  const [instructions, setInstructions] = useState("");

  useEffect(() => {
    if (!id) return;
    Promise.all([
      fetchProject(id),
      fetchScript(id).catch(e => null) // Returns null if 404
    ])
      .then(([pData, sData]) => {
        setProject(pData);
        setScript(sData);
      })
      .catch(err => setError("Failed to load project details"))
      .finally(() => setLoadingInitial(false));
  }, [id]);

  const handleProposeStandardization = async () => {
    setGenerating(true);
    setError(null);
    try {
      const newProposal = await proposeScriptStandardization(id);
      setProposal(newProposal);
    } catch (err: any) {
      setError(err.message || "Failed to propose standardization");
    } finally {
      setGenerating(false);
    }
  };

  const handleProposeSceneFix = async () => {
    if (!selectedSceneId || !script) return;
    setGenerating(true);
    setError(null);
    try {
      const newProposal = await proposeSceneFix(id, selectedSceneId, { 
        base_version: script.version, 
        instructions 
      });
      setProposal(newProposal);
    } catch (err: any) {
      setError(err.message || "Failed to propose scene fix");
    } finally {
      setGenerating(false);
    }
  };

  const handleApplyProposal = async () => {
    if (!proposal) return;
    setGenerating(true);
    setError(null);
    try {
      const updatedScript = await applyScriptProposal(id, proposal.id);
      setScript(updatedScript);
      setProposal(null);
      setInstructions(""); // Clear instructions on success
    } catch (err: any) {
      setError(err.message || "Failed to apply script proposal");
    } finally {
      setGenerating(false);
    }
  };

  const handleRejectProposal = async () => {
    if (!proposal) return;
    setGenerating(true);
    try {
      await rejectScriptProposal(id, proposal.id);
      setProposal(null);
    } catch (err: any) {
      setError(err.message || "Failed to reject proposal");
    } finally {
      setGenerating(false);
    }
  };

  if (loadingInitial) {
    return <div className="p-8 text-gray-400">Initializing Script Studio...</div>;
  }

  if (!project) {
    return <div className="p-8 text-red-400">Project not found.</div>;
  }

  // Which script to display in the main canvas?
  // If we have a pending proposal, show it! 
  // We can show it side-by-side or just replace the main view for now.
  const displayScript = proposal ? proposal.proposed_script : script;
  const isProposalView = !!proposal;
  const selectedScene = displayScript?.scenes?.find(s => s.id === selectedSceneId);

  return (
    <div className="flex flex-col h-screen bg-gray-950 text-gray-200 overflow-hidden font-sans">
      {/* Top Navbar */}
      <header className="h-16 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-6 flex-shrink-0">
        <div className="flex items-center space-x-4">
          <Link href={`/projects/${project.id}`} className="text-gray-400 hover:text-white transition-colors">
            &larr; Dashboard
          </Link>
          <div className="h-6 w-px bg-gray-700"></div>
          <h1 className="text-xl font-bold tracking-tight text-white">{project.name} <span className="text-gray-500 font-normal">/ Script Studio</span></h1>
        </div>
        {script && (
          <div className="text-sm text-gray-400 bg-gray-800 px-3 py-1 rounded-full border border-gray-700">
            Approved Version: <span className="text-indigo-400 font-bold">v{script.version}</span>
          </div>
        )}
      </header>

      {/* Main 3-Pane Layout */}
      <div className="flex flex-1 overflow-hidden">
        
        {/* LEFT PANE: Project Context */}
        <aside className="w-1/5 min-w-[250px] bg-gray-900/50 border-r border-gray-800 overflow-y-auto p-6 hidden md:block">
          <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-6">Project Context</h2>
          
          <div className="space-y-6">
            <div>
              <h3 className="text-xs text-gray-500 mb-1">RAW SOURCE MATERIAL</h3>
              <p className="text-sm text-gray-300 leading-relaxed max-h-[300px] overflow-y-auto custom-scrollbar pr-2 whitespace-pre-wrap">
                {project.source_material || project.story_idea}
              </p>
            </div>
            <div>
              <h3 className="text-xs text-gray-500 mb-1">GENRE</h3>
              <p className="text-sm font-medium text-indigo-300">{project.genre}</p>
            </div>
            <div>
              <h3 className="text-xs text-gray-500 mb-1">TONE</h3>
              <p className="text-sm font-medium text-gray-300">{project.tone}</p>
            </div>
            <div>
              <h3 className="text-xs text-gray-500 mb-1">VISUAL STYLE</h3>
              <p className="text-sm font-medium text-gray-300">{project.visual_style}</p>
            </div>
          </div>
        </aside>

        {/* CENTER PANE: Script Canvas */}
        <main className="flex-1 bg-[#1a1c23] overflow-y-auto relative shadow-inner">
          <div className="max-w-3xl mx-auto py-12 px-8 pb-32">
            
            {isProposalView && (
              <div className="mb-8 p-4 bg-indigo-900/30 border border-indigo-500/50 rounded-lg flex items-center justify-between shadow-[0_0_20px_rgba(99,102,241,0.1)]">
                <div className="flex items-center">
                  <span className="w-3 h-3 rounded-full bg-indigo-500 animate-pulse mr-3"></span>
                  <span className="text-indigo-200 font-medium">Viewing Script Doctor Proposal</span>
                </div>
                <div className="text-xs text-indigo-400">Based on v{proposal.base_script_version}</div>
              </div>
            )}

            {!displayScript ? (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <div className="w-16 h-16 mb-4 rounded-full bg-gray-800 flex items-center justify-center border border-gray-700">
                  <svg className="w-8 h-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h2 className="text-xl font-medium text-gray-300 mb-2">Unstandardized Raw Material</h2>
                <p className="text-gray-500 max-w-sm mb-6">
                  {project.source_material 
                    ? "The raw script needs to be standardized into a professional format."
                    : "Use the Script Doctor to structure the screenplay."}
                </p>
                <button
                  onClick={handleProposeStandardization}
                  disabled={generating}
                  className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-6 py-2 rounded-md font-medium transition-colors"
                >
                  {generating ? "Standardizing..." : "Standardize Screenplay"}
                </button>
              </div>
            ) : (
              <div className="space-y-12">
                <div className="text-center mb-16">
                  <h1 className="text-3xl font-bold uppercase tracking-widest text-white">{displayScript.title || "Untitled Screenplay"}</h1>
                  <div className="w-16 h-1 bg-indigo-900 mx-auto mt-6 rounded-full"></div>
                </div>

                {displayScript.scenes?.map((scene: Scene) => {
                  const isSelected = selectedSceneId === scene.id;
                  
                  return (
                    <div 
                      key={scene.id} 
                      onClick={() => setSelectedSceneId(scene.id)}
                      className={`
                        p-6 rounded-lg border transition-all cursor-pointer relative group
                        ${isSelected 
                          ? 'bg-gray-800/80 border-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.1)]' 
                          : 'bg-transparent border-transparent hover:bg-gray-800/40 hover:border-gray-700'
                        }
                      `}
                    >
                      {/* Scene Heading */}
                      <div className="font-bold text-gray-100 uppercase tracking-wide mb-4 flex items-center">
                        <span className="text-indigo-400 mr-2">{scene.scene_number}.</span>
                        {scene.heading} - {scene.time_of_day}
                      </div>

                      {/* Scene Description / Actions */}
                      <div className="text-gray-300 leading-relaxed mb-6 space-y-3 font-serif text-lg">
                        <p>{scene.description}</p>
                        {scene.actions?.map((act, i) => (
                          <p key={i}>{act.text}</p>
                        ))}
                      </div>

                      {/* Dialogue */}
                      {scene.dialogue && scene.dialogue.length > 0 && (
                        <div className="space-y-4 my-6">
                          {scene.dialogue.map((line, i) => (
                            <div key={i} className="flex flex-col items-center">
                              <div className="text-gray-200 uppercase font-semibold tracking-wider text-sm">
                                {line.character}
                              </div>
                              {line.parenthetical && (
                                <div className="text-gray-500 text-sm italic">
                                  ({line.parenthetical})
                                </div>
                              )}
                              <div className="text-gray-300 font-serif text-lg max-w-md text-center mt-1">
                                {line.text}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                      
                      {/* Selection Indicator */}
                      {isSelected && (
                        <div className="absolute top-4 right-4 flex items-center text-xs font-bold text-indigo-400 bg-indigo-900/30 px-3 py-1 rounded-full">
                          <span className="w-2 h-2 rounded-full bg-indigo-500 mr-2 animate-pulse"></span>
                          SELECTED
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </main>

        {/* RIGHT PANE: Script Doctor Controls */}
        <aside className="w-1/4 min-w-[320px] bg-gray-900 border-l border-gray-800 flex flex-col">
          <div className="p-4 border-b border-gray-800 flex items-center">
            <svg className="w-5 h-5 text-indigo-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <h2 className="text-sm font-bold text-gray-200 uppercase tracking-wider">Script Doctor</h2>
          </div>

          <div className="p-6 flex-1 overflow-y-auto">
            {error && (
              <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded-md mb-6 text-sm break-words">
                {error}
              </div>
            )}

            {isProposalView ? (
              // PROPOSAL REVIEW MODE
              <div className="space-y-6 animate-fade-in">
                <div className="bg-indigo-900/20 border border-indigo-500/30 rounded-lg p-5">
                  <h3 className="text-indigo-300 font-medium mb-3 flex items-center text-lg">
                    <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Review Proposal
                  </h3>
                  <p className="text-sm text-gray-300 mb-6 leading-relaxed">
                    The Script Doctor has standardized the script based on your raw material. Please review the changes in the center canvas.
                  </p>
                  
                  <div className="space-y-3">
                    <button
                      onClick={handleApplyProposal}
                      disabled={generating}
                      className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-md text-sm font-medium transition-colors shadow-lg shadow-green-900/20 flex justify-center items-center"
                    >
                      {generating ? "Applying..." : "Apply Changes (Create v" + ((script?.version || 0) + 1) + ")"}
                    </button>
                    <button
                      onClick={handleRejectProposal}
                      disabled={generating}
                      className="w-full bg-gray-700 hover:bg-gray-600 text-white py-3 rounded-md text-sm font-medium transition-colors"
                    >
                      Reject Proposal
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              // REGULAR CONTROLS (NO PENDING PROPOSAL)
              <div className="space-y-8">
                {/* Full Script Standardization */}
                <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-5">
                  <h3 className="text-white font-medium mb-2">Standardize Script</h3>
                  <p className="text-gray-400 text-sm mb-5">
                    Process the raw material into a professional screenplay format.
                  </p>
                  <button
                    onClick={handleProposeStandardization}
                    disabled={generating}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white py-2 rounded font-medium transition-colors flex justify-center items-center"
                  >
                    {generating ? "Standardizing..." : "Standardize Script"}
                  </button>
                </div>

                {/* Scene-Level Fixes */}
                <div className="border-t border-gray-800 pt-6">
                  <h3 className="text-gray-300 font-medium mb-4 text-sm uppercase tracking-wider">Scene Standardization</h3>
                  
                  {!selectedScene ? (
                    <div className="text-center py-6 bg-gray-900 rounded border border-gray-800 border-dashed">
                      <p className="text-gray-500 text-sm">
                        Select a scene to apply specific fixes.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="bg-gray-800 rounded p-3 text-xs text-gray-300">
                        Selected: <span className="font-medium text-white">{selectedScene.heading}</span>
                      </div>
                      
                      <textarea
                        value={instructions}
                        onChange={(e) => setInstructions(e.target.value)}
                        disabled={generating}
                        rows={3}
                        className="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 placeholder-gray-600 transition-colors"
                        placeholder="e.g., Fix the formatting of the action block..."
                      />

                      <div className="flex flex-wrap gap-2 mb-2">
                        {["Fix dialogue", "Standardize slugline", "Improve grammar"].map(sugg => (
                          <button
                            key={sugg}
                            onClick={() => setInstructions(sugg)}
                            className="bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs px-2 py-1 rounded"
                          >
                            {sugg}
                          </button>
                        ))}
                      </div>

                      <button
                        onClick={handleProposeSceneFix}
                        disabled={generating || !instructions.trim()}
                        className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white py-2 rounded text-sm font-medium transition-colors"
                      >
                        {generating ? "Fixing..." : "Propose Scene Fix"}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
