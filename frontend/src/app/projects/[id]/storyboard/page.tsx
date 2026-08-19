"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Film, ImageIcon, Wand2, Edit, Save, RefreshCw, ChevronRight, X, Loader2, Camera, MapPin, Users, Lightbulb, Activity, MonitorPlay, Terminal } from "lucide-react";
import {
  Project,
  fetchProject,
  ProductionPlan,
  ProductionScene,
  ShotBlueprint,
  StoryboardFrame,
  getProduction,
  getProductionScenes,
  getProductionShots,
  updateShotBlueprint,
  generateStoryboard,
  regenerateStoryboard,
  getStoryboardShot
} from "@/lib/api";

export default function StoryboardWorkspace() {
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [production, setProduction] = useState<ProductionPlan | null>(null);
  const [scenes, setScenes] = useState<ProductionScene[]>([]);
  
  const [selectedScene, setSelectedScene] = useState<ProductionScene | null>(null);
  const [shots, setShots] = useState<ShotBlueprint[]>([]);
  const [selectedShot, setSelectedShot] = useState<ShotBlueprint | null>(null);
  
  const [frames, setFrames] = useState<StoryboardFrame[]>([]);
  const [selectedFrame, setSelectedFrame] = useState<StoryboardFrame | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [isEditingShot, setIsEditingShot] = useState(false);
  const [editedShot, setEditedShot] = useState<Partial<ShotBlueprint>>({});

  useEffect(() => {
    if (!projectId) return;
    async function loadData() {
      try {
        const [proj, prod] = await Promise.all([
          fetchProject(projectId),
          getProduction(projectId)
        ]);
        setProject(proj);
        setProduction(prod);
        
        if (prod) {
          const scns = await getProductionScenes(projectId);
          // Sort by scene number
          scns.sort((a, b) => a.scene_number - b.scene_number);
          setScenes(scns);
          if (scns.length > 0) {
            handleSelectScene(scns[0]);
          }
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [projectId]);

  const handleSelectScene = async (scene: ProductionScene) => {
    setSelectedScene(scene);
    setSelectedShot(null);
    setFrames([]);
    setSelectedFrame(null);
    try {
      const sceneShots = await getProductionShots(projectId, scene.id);
      sceneShots.sort((a, b) => a.shot_number - b.shot_number);
      setShots(sceneShots);
      if (sceneShots.length > 0) {
        handleSelectShot(sceneShots[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSelectShot = async (shot: ShotBlueprint) => {
    setSelectedShot(shot);
    setIsEditingShot(false);
    setEditedShot({});
    try {
      const shotFrames = await getStoryboardShot(projectId, shot.id);
      // Sort newest first
      shotFrames.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setFrames(shotFrames);
      if (shotFrames.length > 0) {
        setSelectedFrame(shotFrames[0]);
      } else {
        setSelectedFrame(null);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveShotEdit = async () => {
    if (!selectedShot) return;
    try {
      const updated = await updateShotBlueprint(projectId, selectedShot.id, editedShot);
      setSelectedShot(updated);
      setShots(shots.map(s => s.id === updated.id ? updated : s));
      setIsEditingShot(false);
    } catch (err) {
      console.error(err);
    }
  };

  const handleGenerate = async () => {
    if (!selectedShot) return;
    setGenerating(true);
    try {
      const newFrame = await generateStoryboard(projectId, selectedShot.id);
      setFrames([newFrame, ...frames]);
      setSelectedFrame(newFrame);
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const handleRegenerate = async () => {
    if (!selectedShot) return;
    setGenerating(true);
    try {
      const newFrame = await regenerateStoryboard(projectId, selectedShot.id);
      setFrames([newFrame, ...frames]);
      setSelectedFrame(newFrame);
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-gray-400">Loading workspace...</div>;
  }

  if (!production) {
    return (
      <div className="p-8 text-center text-gray-400">
        <h2 className="text-xl font-semibold mb-2">No Production Plan Found</h2>
        <p>Please complete Script Studio and generate a Production Plan first.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-theme(spacing.16))] bg-[#0a0a0c] text-gray-200">
      {/* Top Header */}
      <header className="h-14 border-b border-gray-800/60 bg-gray-900/40 flex items-center px-6 justify-between flex-shrink-0">
        <div className="flex items-center space-x-4">
          <h1 className="font-bold text-lg text-gray-100 flex items-center">
            <Film className="w-5 h-5 mr-2 text-indigo-400" />
            {project?.name}
          </h1>
          <div className="h-4 w-px bg-gray-700" />
          <span className="text-sm text-gray-400">Storyboard Workspace</span>
        </div>
        <div className="flex items-center space-x-6 text-xs text-gray-500 font-mono">
          <span>Script v{production.script_version}</span>
          <span>ProdPlan v{production.version}</span>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel: Scene Navigator */}
        <aside className="w-72 border-r border-gray-800/60 bg-gray-900/20 flex flex-col overflow-y-auto">
          <div className="p-4 border-b border-gray-800/60 sticky top-0 bg-gray-900/90 backdrop-blur z-10">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Scene Navigator</h2>
          </div>
          <div className="flex flex-col p-2 space-y-1">
            {scenes.map(scene => (
              <div key={scene.id}>
                <button
                  onClick={() => handleSelectScene(scene)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    selectedScene?.id === scene.id ? 'bg-indigo-500/10 text-indigo-300' : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'
                  }`}
                >
                  <div className="truncate">Scene {scene.scene_number} — {scene.heading}</div>
                </button>
                {selectedScene?.id === scene.id && (
                  <div className="ml-4 pl-2 border-l border-gray-700 mt-1 space-y-1">
                    {shots.map(shot => (
                      <button
                        key={shot.id}
                        onClick={() => handleSelectShot(shot)}
                        className={`w-full text-left px-2 py-1.5 rounded text-xs transition-colors flex items-center ${
                          selectedShot?.id === shot.id ? 'bg-gray-800 text-gray-200 font-semibold' : 'text-gray-500 hover:text-gray-300'
                        }`}
                      >
                        <Camera className="w-3 h-3 mr-2" />
                        Shot {shot.shot_number} — {shot.shot_size}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </aside>

        {/* Center Panel: Visual Canvas */}
        <main className="flex-1 flex flex-col bg-black relative">
          <div className="flex-1 flex items-center justify-center p-8 overflow-hidden relative">
            {!selectedShot ? (
              <div className="text-gray-600 flex flex-col items-center">
                <ImageIcon className="w-12 h-12 mb-4 opacity-20" />
                <p>Select a shot from the scene navigator</p>
              </div>
            ) : generating ? (
              <div className="text-indigo-400 flex flex-col items-center animate-pulse">
                <Loader2 className="w-12 h-12 mb-4 animate-spin" />
                <p className="text-lg font-medium">Generating Storyboard...</p>
                <p className="text-sm text-gray-500 mt-2">Connecting to ImageGenerationService</p>
              </div>
            ) : !selectedFrame ? (
              <div className="border border-dashed border-gray-700 rounded-xl p-12 text-center max-w-md w-full bg-gray-900/30">
                <Wand2 className="w-12 h-12 mb-4 text-gray-600 mx-auto" />
                <h3 className="text-xl font-semibold text-gray-300 mb-2">NO STORYBOARD GENERATED</h3>
                <p className="text-gray-500 text-sm mb-6">Review the shot plan on the right and generate a frame.</p>
                <button
                  onClick={handleGenerate}
                  className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-md shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center w-full"
                >
                  <Wand2 className="w-4 h-4 mr-2" />
                  Generate Frame
                </button>
              </div>
            ) : (
              <div className="relative w-full h-full flex flex-col items-center justify-center">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={selectedFrame.image_url}
                  alt={`Storyboard variant`}
                  className="max-w-full max-h-full object-contain rounded-lg shadow-2xl ring-1 ring-gray-800"
                />
                
                {/* Generation Prompt Overlay (Expandable) */}
                <div className="absolute bottom-6 left-6 max-w-xl group">
                  <div className="bg-black/60 backdrop-blur-md border border-gray-700/50 rounded-lg p-3 overflow-hidden opacity-40 hover:opacity-100 transition-opacity">
                    <div className="text-xs font-mono text-gray-400 mb-1 flex items-center">
                      <Terminal className="w-3 h-3 mr-1" />
                      Compiled Generation Prompt
                    </div>
                    <div className="text-xs text-gray-300 max-h-10 group-hover:max-h-64 overflow-y-auto pr-2 custom-scrollbar transition-all duration-300 whitespace-pre-wrap">
                      {selectedFrame.prompt}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>

        {/* Right Panel: Shot Editor & Variants */}
        <aside className="w-96 border-l border-gray-800/60 bg-gray-900/30 flex flex-col overflow-y-auto">
          {selectedShot ? (
            <>
              {/* Shot Blueprint Header */}
              <div className="p-5 border-b border-gray-800/60">
                <div className="flex justify-between items-start mb-4">
                  <h2 className="text-lg font-bold text-gray-200 flex items-center">
                    <Camera className="w-4 h-4 mr-2 text-gray-400" />
                    Shot {selectedShot.shot_number}
                  </h2>
                  <div className="flex space-x-2">
                    {!isEditingShot ? (
                      <button onClick={() => { setEditedShot(selectedShot); setIsEditingShot(true); }} className="p-1.5 text-gray-500 hover:text-gray-300 hover:bg-gray-800 rounded">
                        <Edit className="w-4 h-4" />
                      </button>
                    ) : (
                      <>
                        <button onClick={handleSaveShotEdit} className="p-1.5 text-green-400 hover:bg-green-400/10 rounded flex items-center text-xs font-medium">
                          <Save className="w-3 h-3 mr-1" /> Save
                        </button>
                        <button onClick={() => setIsEditingShot(false)} className="p-1.5 text-gray-500 hover:bg-gray-800 rounded">
                          <X className="w-4 h-4" />
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {isEditingShot ? (
                  <div className="space-y-3 text-sm">
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">Shot Size</label>
                      <input type="text" value={editedShot.shot_size || ''} onChange={e => setEditedShot({...editedShot, shot_size: e.target.value})} className="w-full bg-gray-950 border border-gray-700 rounded px-2 py-1" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">Camera Angle</label>
                      <input type="text" value={editedShot.camera_angle || ''} onChange={e => setEditedShot({...editedShot, camera_angle: e.target.value})} className="w-full bg-gray-950 border border-gray-700 rounded px-2 py-1" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">Lens</label>
                      <input type="text" value={editedShot.lens || ''} onChange={e => setEditedShot({...editedShot, lens: e.target.value})} className="w-full bg-gray-950 border border-gray-700 rounded px-2 py-1" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">Lighting</label>
                      <textarea value={editedShot.lighting || ''} onChange={e => setEditedShot({...editedShot, lighting: e.target.value})} className="w-full bg-gray-950 border border-gray-700 rounded px-2 py-1 text-xs h-16" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">Purpose</label>
                      <textarea value={editedShot.purpose || ''} onChange={e => setEditedShot({...editedShot, purpose: e.target.value})} className="w-full bg-gray-950 border border-gray-700 rounded px-2 py-1 text-xs h-16" />
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex gap-2">
                      <span className="px-2 py-1 bg-gray-800 text-gray-300 text-xs font-semibold rounded">{selectedShot.shot_size}</span>
                      <span className="px-2 py-1 bg-gray-800 text-gray-300 text-xs font-semibold rounded">{selectedShot.camera_angle}</span>
                      <span className="px-2 py-1 bg-gray-800 text-gray-300 text-xs font-semibold rounded">{selectedShot.lens}</span>
                    </div>
                    
                    <div>
                      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1 flex items-center">
                        <MonitorPlay className="w-3 h-3 mr-1" /> Action & Subject
                      </h4>
                      <p className="text-sm text-gray-300">{selectedShot.subject}</p>
                      <p className="text-xs text-gray-400 mt-1 italic">{selectedShot.character_actions}</p>
                    </div>

                    <div>
                      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1 flex items-center">
                        <Lightbulb className="w-3 h-3 mr-1" /> Lighting & Composition
                      </h4>
                      <p className="text-sm text-gray-300">{selectedShot.lighting}</p>
                      <p className="text-xs text-gray-400 mt-1">{selectedShot.composition}</p>
                    </div>

                    <div className="bg-gray-800/30 p-3 rounded-md border border-gray-800">
                      <h4 className="text-xs font-semibold text-indigo-400/80 uppercase tracking-wider mb-1">Director's Purpose</h4>
                      <p className="text-sm text-gray-300 italic">"{selectedShot.purpose}"</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Variants Section */}
              <div className="p-5 flex-1 flex flex-col overflow-hidden">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Variants</h3>
                  {frames.length > 0 && (
                    <button
                      onClick={handleRegenerate}
                      disabled={generating}
                      className="text-xs flex items-center px-2 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded transition-colors disabled:opacity-50"
                    >
                      <RefreshCw className={`w-3 h-3 mr-1 ${generating ? 'animate-spin' : ''}`} />
                      Regenerate
                    </button>
                  )}
                </div>

                <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                  {frames.length === 0 && !generating && (
                    <div className="text-xs text-gray-500 text-center py-4 italic">No variants yet.</div>
                  )}
                  {frames.map((frame, idx) => (
                    <div
                      key={frame.id}
                      onClick={() => setSelectedFrame(frame)}
                      className={`relative p-3 rounded-lg border transition-all cursor-pointer overflow-hidden ${
                        selectedFrame?.id === frame.id 
                          ? 'border-indigo-500 bg-indigo-500/10' 
                          : 'border-gray-800 bg-gray-900/50 hover:border-gray-600'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-semibold text-gray-200">Variant {frames.length - idx}</span>
                          {selectedFrame?.id === frame.id && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-400">SELECTED</span>
                          )}
                        </div>
                        <span className="text-[10px] text-gray-500">
                          {new Date(frame.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-2 text-[10px] text-gray-400 font-mono mb-2">
                        <div><span className="text-gray-500">Provider:</span> {frame.provider}</div>
                        <div><span className="text-gray-500">Model:</span> {frame.model}</div>
                        <div className="col-span-2 truncate"><span className="text-gray-500">ID:</span> {frame.generation_id}</div>
                      </div>
                      
                      {/* Mini thumbnail */}
                      <div className="h-24 w-full bg-black rounded overflow-hidden">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={frame.image_url} className="w-full h-full object-cover opacity-80" alt="Thumbnail" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="p-8 text-center text-gray-500">
              <Camera className="w-8 h-8 mx-auto mb-3 opacity-20" />
              <p className="text-sm">Select a shot to view its blueprint and variants.</p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
