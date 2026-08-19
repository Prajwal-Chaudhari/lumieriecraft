"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { 
  Project, Script, Scene, 
  fetchProject, fetchScript, analyzeScript, proposeSceneEnhancement, applySceneUpdate 
} from "@/lib/api";

export default function ScriptStudioPage() {
  const params = useParams();
  const id = params.id as string;
  
  const [project, setProject] = useState<Project | null>(null);
  const [script, setScript] = useState<Script | null>(null);
  
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null);
  const [instructions, setInstructions] = useState("");
  const [proposedScene, setProposedScene] = useState<Scene | null>(null);

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

  const handleAnalyzeScript = async () => {
    setGenerating(true);
    setError(null);
    try {
      const newScript = await analyzeScript(id);
      setScript(newScript);
    } catch (err: any) {
      setError(err.message || "Failed to analyze script");
    } finally {
      setGenerating(false);
    }
  };

  const handleProposeEnhancement = async () => {
    if (!selectedSceneId) return;
    setGenerating(true);
    setError(null);
    try {
      const result = await proposeSceneEnhancement(id, selectedSceneId, { instructions });
      setProposedScene(result.proposed_scene);
    } catch (err: any) {
      setError(err.message || "Failed to propose scene enhancement");
    } finally {
      setGenerating(false);
    }
  };

  const handleApplyEnhancement = async () => {
    if (!selectedSceneId || !proposedScene) return;
    setGenerating(true);
    setError(null);
    try {
      const updatedScript = await applySceneUpdate(id, selectedSceneId, proposedScene);
      setScript(updatedScript);
      setProposedScene(null);
      setInstructions(""); // Clear instructions on success
    } catch (err: any) {
      setError(err.message || "Failed to apply enhancement");
    } finally {
      setGenerating(false);
    }
  };

  const handleRejectEnhancement = () => {
    setProposedScene(null);
  };

  if (loadingInitial) {
    return <div className="p-8 text-gray-400">Initializing Script Studio...</div>;
  }

  if (!project) {
    return <div className="p-8 text-red-400">Project not found.</div>;
  }

  const selectedScene = script?.scenes.find(s => s.id === selectedSceneId);

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
      </header>

      {/* Main 3-Pane Layout */}
      <div className="flex flex-1 overflow-hidden">
        
        {/* LEFT PANE: Project Context */}
        <aside className="w-1/5 min-w-[250px] bg-gray-900/50 border-r border-gray-800 overflow-y-auto p-6 hidden md:block">
          <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-6">Project Context</h2>
          
          <div className="space-y-6">
            <div>
              <h3 className="text-xs text-gray-500 mb-1">STORY IDEA</h3>
              <p className="text-sm text-gray-300 leading-relaxed">{project.story_idea}</p>
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
            {!script ? (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <div className="w-16 h-16 mb-4 rounded-full bg-gray-800 flex items-center justify-center border border-gray-700">
                  <svg className="w-8 h-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h2 className="text-xl font-medium text-gray-300 mb-2">Blank Canvas</h2>
                <p className="text-gray-500 max-w-sm mb-6">
                  {project.source_material 
                    ? "Analyze the rough script to begin structuring your screenplay."
                    : "Use the AI Copilot on the right to generate the first draft of your screenplay."}
                </p>
                <button
                  onClick={handleAnalyzeScript}
                  disabled={generating}
                  className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-6 py-2 rounded-md font-medium transition-colors"
                >
                  {generating ? "Analyzing..." : "Analyze & Structure Script"}
                </button>
              </div>
            ) : (
              <div className="space-y-12">
                <div className="text-center mb-16">
                  <h1 className="text-3xl font-bold uppercase tracking-widest text-white">{script.title}</h1>
                  <div className="w-16 h-1 bg-indigo-900 mx-auto mt-6 rounded-full"></div>
                </div>

                {script.scenes.map((scene) => {
                  const isSelected = selectedSceneId === scene.id;
                  
                  return (
                    <div 
                      key={scene.id} 
                      onClick={() => {
                        if (!proposedScene || selectedSceneId === scene.id) {
                          setSelectedSceneId(scene.id);
                        }
                      }}
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
                        {scene.actions.map((act, i) => (
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

        {/* RIGHT PANE: AI Copilot */}
        <aside className="w-1/4 min-w-[320px] bg-gray-900 border-l border-gray-800 flex flex-col">
          <div className="p-4 border-b border-gray-800 flex items-center">
            <svg className="w-5 h-5 text-indigo-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <h2 className="text-sm font-bold text-gray-200 uppercase tracking-wider">AI Copilot</h2>
          </div>

          <div className="p-6 flex-1 overflow-y-auto">
            {error && (
              <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded-md mb-6 text-sm">
                {error}
              </div>
            )}

            {!script ? (
              // Empty State Action
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-5">
                <h3 className="text-white font-medium mb-2">Analyze Script</h3>
                <p className="text-gray-400 text-sm mb-5">
                  Structure your rough script into a professional screenplay format.
                </p>
                <button
                  onClick={handleAnalyzeScript}
                  disabled={generating}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white py-2 rounded font-medium transition-colors flex justify-center items-center"
                >
                  {generating ? "Analyzing..." : "Analyze & Structure"}
                </button>
              </div>
            ) : !selectedScene ? (
              // Script exists, nothing selected
              <div className="text-center py-12">
                <div className="text-gray-600 mb-4">
                  <svg className="w-12 h-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                  </svg>
                </div>
                <p className="text-gray-400 text-sm">
                  Select a scene in the canvas to enhance it professionally.
                </p>
              </div>
            ) : proposedScene ? (
              // Proposed enhancement view
              <div className="space-y-6 animate-fade-in">
                <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
                  <h3 className="text-green-400 font-medium mb-2 flex items-center">
                    <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Enhancement Proposed
                  </h3>
                  <p className="text-xs text-gray-300 mb-4">
                    Review the proposed changes. The original scene remains intact until you click Apply.
                  </p>
                  
                  {/* Miniature diff view */}
                  <div className="space-y-2 mb-4 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                    <div className="text-xs font-bold text-gray-500 uppercase">Proposed Description:</div>
                    <div className="text-sm text-gray-200 italic border-l-2 border-indigo-500 pl-2">
                      {proposedScene.description}
                    </div>
                  </div>

                  <div className="flex space-x-3">
                    <button
                      onClick={handleApplyEnhancement}
                      disabled={generating}
                      className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded text-sm font-medium transition-colors"
                    >
                      {generating ? "Applying..." : "Apply"}
                    </button>
                    <button
                      onClick={handleRejectEnhancement}
                      disabled={generating}
                      className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded text-sm font-medium transition-colors"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              // Scene selected, ready for enhancement
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="text-white font-medium">Selected Scene</h3>
                    <span className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded">Scene {selectedScene.scene_number}</span>
                  </div>
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 text-xs text-gray-300 line-clamp-3">
                    {selectedScene.heading}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    How should we enhance this?
                  </label>
                  <div className="space-y-2 mb-3">
                    {/* Quick suggestion buttons */}
                    {["Make it more cinematic", "Improve pacing", "Enhance dialogue"].map(suggestion => (
                      <button 
                        key={suggestion}
                        onClick={() => setInstructions(suggestion)}
                        className="block w-full text-left text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-2 rounded transition-colors"
                      >
                        ✨ {suggestion}
                      </button>
                    ))}
                  </div>
                  
                  <textarea
                    value={instructions}
                    onChange={(e) => setInstructions(e.target.value)}
                    disabled={generating}
                    rows={3}
                    className="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 placeholder-gray-600 transition-colors"
                    placeholder="Or type custom instructions..."
                  />
                </div>

                <button
                  onClick={handleProposeEnhancement}
                  disabled={generating || !instructions.trim()}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white py-2 rounded font-medium transition-colors flex justify-center items-center shadow-lg shadow-indigo-900/20"
                >
                  {generating ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Thinking...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      Propose Enhancement
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
