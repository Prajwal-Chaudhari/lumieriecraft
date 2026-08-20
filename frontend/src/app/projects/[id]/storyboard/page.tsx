"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Film, ImageIcon, Wand2, RefreshCw, Loader2, Camera, Palette, Users, MonitorPlay, Terminal, AlertCircle } from "lucide-react";
import {
  Project,
  fetchProject,
  ProductionPlan,
  ProductionScene,
  ShotBlueprint,
  StoryboardFrame,
  CharacterAsset,
  getProduction,
  getProductionScenes,
  getProductionShots,
  generateStoryboard,
  regenerateStoryboard,
  getStoryboardShot,
  fetchCharacterAssets
} from "@/lib/api";

export default function StoryboardWorkspace() {
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [production, setProduction] = useState<ProductionPlan | null>(null);
  const [scenes, setScenes] = useState<ProductionScene[]>([]);
  const [characters, setCharacters] = useState<CharacterAsset[]>([]);
  
  const [selectedScene, setSelectedScene] = useState<ProductionScene | null>(null);
  const [shots, setShots] = useState<ShotBlueprint[]>([]);
  const [selectedShot, setSelectedShot] = useState<ShotBlueprint | null>(null);
  
  const [frames, setFrames] = useState<StoryboardFrame[]>([]);
  const [selectedFrame, setSelectedFrame] = useState<StoryboardFrame | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    async function loadData() {
      try {
        const [proj, prod, chars] = await Promise.all([
          fetchProject(projectId),
          getProduction(projectId),
          fetchCharacterAssets(projectId)
        ]);
        setProject(proj);
        setProduction(prod);
        setCharacters(chars);
        
        if (prod) {
          const scns = await getProductionScenes(projectId);
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
      sceneShots.sort((a, b) => parseInt(a.shot_id.replace('shot_', '')) - parseInt(b.shot_id.replace('shot_', '')));
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
    try {
      const shotFrames = await getStoryboardShot(projectId, shot.id);
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
  
  const getSceneColorPlan = () => {
    if (!production?.scenes_data?.scenes || !selectedScene) return null;
    const sData = production.scenes_data.scenes.find(s => s.scene_id === selectedScene.id);
    return sData?.color_plan;
  };
  
  const colorPlan = getSceneColorPlan();

  // Find character references for the current shot subject
  const getShotCharacterAssets = () => {
    if (!selectedShot?.subject) return [];
    return characters.filter(c => selectedShot.subject.toLowerCase().includes(c.character_name.toLowerCase()));
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
        {/* Left Panel: Scene Navigator & Color Panel */}
        <aside className="w-72 border-r border-gray-800/60 bg-gray-900/20 flex flex-col overflow-y-auto custom-scrollbar">
          <div className="p-4 border-b border-gray-800/60 sticky top-0 bg-gray-900/90 backdrop-blur z-10">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Scene Navigator</h2>
          </div>
          <div className="flex flex-col p-2 space-y-1 border-b border-gray-800/60 pb-4">
            {scenes.map(scene => (
              <div key={scene.id}>
                <button
                  onClick={() => handleSelectScene(scene)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    selectedScene?.id === scene.id ? 'bg-indigo-500/10 text-indigo-300' : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'
                  }`}
                >
                  <div className="truncate">SC {scene.scene_number} — {scene.heading}</div>
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
                        Shot {shot.shot_id.replace('shot_', '')}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
          
          {/* Color & LUT Panel */}
          {colorPlan && (
            <div className="p-4">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center mb-3">
                <Palette className="w-4 h-4 mr-2" /> COLOR / LUT
              </h3>
              <div className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  {colorPlan.palette.map((color: any, idx: number) => (
                    <div key={idx} className="flex flex-col items-center group relative cursor-help">
                      <div className="w-8 h-8 rounded border border-gray-700 shadow-inner" style={{backgroundColor: color.hex}}></div>
                      <span className="text-[10px] text-gray-500 mt-1 font-mono uppercase">{color.hex}</span>
                    </div>
                  ))}
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs text-gray-400 font-mono bg-black/40 p-2 rounded">
                  {colorPlan.temperature_kelvin && <div>{colorPlan.temperature_kelvin}K</div>}
                  {colorPlan.contrast && <div>Contrast {colorPlan.contrast}</div>}
                  {colorPlan.saturation && <div>Saturation {colorPlan.saturation}</div>}
                </div>
                {colorPlan.lut && (
                  <div className="text-xs bg-indigo-500/10 text-indigo-300 p-2 rounded border border-indigo-500/20">
                    <span className="font-semibold block mb-0.5">LUT: {colorPlan.lut.name}</span>
                    <span className="text-[10px] text-indigo-400/80 leading-tight block">{colorPlan.lut.reason}</span>
                  </div>
                )}
              </div>
            </div>
          )}
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
                {/* Scene/Shot Overlay */}
                <div className="absolute top-6 left-6 bg-black/80 backdrop-blur-md px-4 py-2 rounded text-white font-mono border border-gray-800 z-10 shadow-2xl">
                  <div className="text-sm font-bold text-gray-300">SC {selectedScene?.scene_number.toString().padStart(2, '0')}</div>
                  <div className="text-xl font-black tracking-widest text-white">SHOT {selectedShot.shot_id.replace('shot_', '').padStart(2, '0')}</div>
                </div>

                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={selectedFrame.image_url}
                  alt={`Storyboard variant`}
                  className="max-w-full max-h-full object-contain rounded-lg shadow-2xl ring-1 ring-gray-800 relative z-0"
                />
                
                {/* Generation Prompt Overlay (Expandable) */}
                <div className="absolute bottom-6 left-6 max-w-2xl group z-10">
                  <div className="bg-black/80 backdrop-blur-xl border border-gray-700/50 rounded-lg p-3 overflow-hidden opacity-40 hover:opacity-100 transition-opacity shadow-2xl">
                    <div className="text-xs font-mono text-gray-400 mb-1 flex items-center">
                      <Terminal className="w-3 h-3 mr-1" />
                      Compiled Generation Prompt
                    </div>
                    <div className="text-[11px] text-gray-300 max-h-8 group-hover:max-h-96 overflow-y-auto pr-2 custom-scrollbar transition-all duration-300 whitespace-pre-wrap font-mono">
                      {selectedFrame.prompt}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>

        {/* Right Panel: Shot Blueprint & References */}
        <aside className="w-96 border-l border-gray-800/60 bg-gray-900/30 flex flex-col overflow-y-auto custom-scrollbar">
          {selectedShot ? (
            <>
              {/* Cinematography Panel */}
              <div className="p-5 border-b border-gray-800/60">
                <h2 className="text-lg font-bold text-gray-200 flex items-center mb-4">
                  <Camera className="w-4 h-4 mr-2 text-indigo-400" />
                  Cinematography
                </h2>

                <div className="space-y-4">
                  <div className="flex gap-2 flex-wrap">
                    <span className="px-2 py-1 bg-gray-800 text-gray-300 text-xs font-semibold rounded border border-gray-700">{selectedShot.shot_size}</span>
                    <span className="px-2 py-1 bg-gray-800 text-gray-300 text-xs font-semibold rounded border border-gray-700">{selectedShot.camera?.angle}</span>
                    {selectedShot.camera?.focal_length_mm && (
                      <span className="px-2 py-1 bg-gray-800 text-gray-300 text-xs font-semibold rounded border border-gray-700">{selectedShot.camera.focal_length_mm}mm</span>
                    )}
                  </div>
                  
                  <div>
                    <h4 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1 flex items-center">
                      <MonitorPlay className="w-3 h-3 mr-1" /> Action & Blocking
                    </h4>
                    <p className="text-sm text-gray-300">{selectedShot.subject}</p>
                    {selectedShot.character_actions && <p className="text-xs text-gray-400 mt-1 italic">{selectedShot.character_actions}</p>}
                    {selectedShot.blocking?.subject_position && <p className="text-[11px] text-gray-500 mt-1 font-mono">Pos: {selectedShot.blocking.subject_position}</p>}
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">Lighting</h4>
                      <p className="text-xs text-gray-300">{selectedShot.lighting?.setup}</p>
                      <p className="text-[10px] text-gray-400 mt-0.5">{selectedShot.lighting?.direction}</p>
                    </div>
                    <div>
                      <h4 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">Composition</h4>
                      <p className="text-xs text-gray-300">{selectedShot.composition?.rule_of_thirds ? "Rule of Thirds" : "Center"}</p>
                      {selectedShot.composition?.negative_space && <p className="text-[10px] text-gray-400 mt-0.5">Space: {selectedShot.composition.negative_space}</p>}
                    </div>
                  </div>

                  <div className="bg-gray-800/30 p-3 rounded-md border border-gray-800">
                    <h4 className="text-[10px] font-semibold text-indigo-400/80 uppercase tracking-wider mb-1">Director's Purpose</h4>
                    <p className="text-xs text-gray-300 italic leading-relaxed">"{selectedShot.purpose}"</p>
                    <p className="text-[10px] font-mono text-gray-500 mt-2">BEAT: {selectedShot.story_beat}</p>
                  </div>
                </div>
              </div>

              {/* Character References Panel */}
              <div className="p-5 border-b border-gray-800/60">
                <h3 className="text-sm font-semibold text-gray-300 flex items-center mb-4">
                  <Users className="w-4 h-4 mr-2 text-indigo-400" />
                  Character References
                </h3>
                
                {getShotCharacterAssets().length > 0 ? (
                  <div className="space-y-4">
                    {getShotCharacterAssets().map(asset => (
                      <div key={asset.id} className="bg-gray-900 border border-gray-800 rounded-lg p-3">
                        <div className="flex items-center space-x-3 mb-2">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img src={asset.file_path} alt={asset.character_name} className="w-10 h-10 rounded object-cover border border-gray-700" />
                          <div>
                            <div className="text-sm font-bold text-gray-200">{asset.character_name}</div>
                            <div className="text-[10px] text-gray-500 uppercase">Resolved</div>
                          </div>
                        </div>
                        <div className="bg-orange-900/20 border border-orange-900/50 rounded p-2 flex items-start">
                          <AlertCircle className="w-3 h-3 text-orange-500 mr-1.5 mt-0.5 flex-shrink-0" />
                          <p className="text-[10px] text-orange-200/80 leading-tight">
                            Conditioning: Not supported by current provider in V1
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-gray-500 italic">No character references found for the subject in this shot.</div>
                )}
              </div>

              {/* Variants Section */}
              <div className="p-5 flex-1 flex flex-col min-h-[300px]">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-sm font-semibold text-gray-300 flex items-center">
                    <RefreshCw className="w-4 h-4 mr-2 text-indigo-400" />
                    Variants
                  </h3>
                  {frames.length > 0 && (
                    <button
                      onClick={handleRegenerate}
                      disabled={generating}
                      className="text-xs flex items-center px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded transition-colors disabled:opacity-50"
                    >
                      <RefreshCw className={`w-3 h-3 mr-1.5 ${generating ? 'animate-spin' : ''}`} />
                      Regenerate
                    </button>
                  )}
                </div>

                <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                  {frames.length === 0 && !generating && (
                    <div className="text-xs text-gray-500 text-center py-4 italic border border-dashed border-gray-800 rounded-lg">No variants yet. Click Generate Frame.</div>
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
                      <div className="h-28 w-full bg-black rounded border border-gray-800 overflow-hidden">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={frame.image_url} className="w-full h-full object-cover opacity-80 hover:opacity-100 transition-opacity" alt="Thumbnail" />
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
