"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

export default function ProductionPage() {
  const params = useParams();
  const projectId = params.id as string;

  const [productionData, setProductionData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [generatingShots, setGeneratingShots] = useState<string | null>(null);

  const fetchProductionData = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/projects/${projectId}/production`);
      if (res.ok) {
        const data = await res.json();
        setProductionData(data);
      }
    } catch (err) {
      console.error("Failed to fetch production data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProductionData();
    const interval = setInterval(fetchProductionData, 5000);
    return () => clearInterval(interval);
  }, [projectId]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      await fetch(`http://localhost:8000/api/projects/${projectId}/production/analyze`, {
        method: "POST"
      });
      fetchProductionData();
    } catch (err) {
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleGenerateShots = async (sceneId: string) => {
    setGeneratingShots(sceneId);
    try {
      await fetch(`http://localhost:8000/api/projects/${projectId}/cinematography/generate?scene_id=${sceneId}`, {
        method: "POST"
      });
    } catch (err) {
      console.error(err);
    } finally {
      setGeneratingShots(null);
    }
  };

  if (loading) return <div className="p-8">Loading Production Intelligence...</div>;

  if (!productionData || productionData.status === "not_analyzed") {
    return (
      <div className="p-8 flex flex-col items-center justify-center h-full">
        <h2 className="text-2xl font-semibold mb-4">Production Intelligence</h2>
        <p className="text-gray-400 mb-8">This script has not been analyzed for production yet.</p>
        <button 
          onClick={handleAnalyze} 
          disabled={analyzing}
          className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded font-medium disabled:opacity-50"
        >
          {analyzing ? "Analyzing (Pass A & B)..." : "Run Global Extraction & Scene Breakdown"}
        </button>
      </div>
    );
  }

  const { plan, characters, worlds, scene_breakdowns } = productionData;

  return (
    <div className="p-8 h-full overflow-y-auto">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Production Plan</h1>
          <p className="text-gray-400">Status: <span className="uppercase text-indigo-400 font-semibold">{plan.status}</span> | Script v{plan.script_version}</p>
        </div>
        <button 
          onClick={handleAnalyze} 
          disabled={analyzing || plan.status === "analyzing"}
          className="px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-600 rounded disabled:opacity-50"
        >
          {plan.status === "analyzing" ? "Analyzing in background..." : "Re-Analyze Script"}
        </button>
      </header>

      <div className="grid grid-cols-2 gap-8 mb-8">
        {/* Character Bible */}
        <section className="bg-gray-900 border border-gray-800 rounded p-6">
          <h2 className="text-xl font-semibold mb-4 text-indigo-300">Character Bible (Global)</h2>
          {characters?.length === 0 && <p className="text-gray-500">No characters extracted.</p>}
          <div className="space-y-6">
            {characters?.map((char: any) => (
              <div key={char.id} className="border-l-2 border-indigo-500 pl-4">
                <h3 className="font-bold text-lg">{char.name}</h3>
                <p className="text-sm text-gray-400 mt-1">{char.appearance} {char.clothing && `| Wearing: ${char.clothing}`}</p>
                
                {char.established_facts?.length > 0 && (
                  <div className="mt-2 text-sm">
                    <span className="font-semibold text-green-400">Established Facts:</span>
                    <ul className="list-disc ml-5 text-gray-300">
                      {char.established_facts.map((f: string, i: number) => <li key={i}>{f}</li>)}
                    </ul>
                  </div>
                )}
                {char.proposed_facts?.length > 0 && (
                  <div className="mt-2 text-sm">
                    <span className="font-semibold text-yellow-400">Proposed Facts:</span>
                    <ul className="list-disc ml-5 text-gray-400">
                      {char.proposed_facts.map((f: string, i: number) => <li key={i}>{f}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* World Bible */}
        <section className="bg-gray-900 border border-gray-800 rounded p-6">
          <h2 className="text-xl font-semibold mb-4 text-emerald-300">World Bible (Global)</h2>
          {worlds?.length === 0 && <p className="text-gray-500">No locations extracted.</p>}
          <div className="space-y-6">
            {worlds?.map((world: any) => (
              <div key={world.id} className="border-l-2 border-emerald-500 pl-4">
                <h3 className="font-bold text-lg">{world.name}</h3>
                <p className="text-sm text-gray-400 mt-1">{world.description}</p>
                <p className="text-sm text-gray-400 mt-1">Lighting: {world.lighting_characteristics}</p>

                {world.established_facts?.length > 0 && (
                  <div className="mt-2 text-sm">
                    <span className="font-semibold text-green-400">Established Facts:</span>
                    <ul className="list-disc ml-5 text-gray-300">
                      {world.established_facts.map((f: string, i: number) => <li key={i}>{f}</li>)}
                    </ul>
                  </div>
                )}
                {world.proposed_facts?.length > 0 && (
                  <div className="mt-2 text-sm">
                    <span className="font-semibold text-yellow-400">Proposed Facts:</span>
                    <ul className="list-disc ml-5 text-gray-400">
                      {world.proposed_facts.map((f: string, i: number) => <li key={i}>{f}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Scene Breakdowns & Shot Blueprints */}
      <h2 className="text-2xl font-bold mb-4 border-b border-gray-800 pb-2">Scenes & Cinematography</h2>
      <div className="space-y-8">
        {scene_breakdowns?.map((breakdown: any) => (
          <SceneProductionCard 
            key={breakdown.id} 
            breakdown={breakdown} 
            projectId={projectId}
            generating={generatingShots === breakdown.scene_id}
            onGenerateShots={() => handleGenerateShots(breakdown.scene_id)}
          />
        ))}
      </div>
    </div>
  );
}

function SceneProductionCard({ breakdown, projectId, generating, onGenerateShots }: { breakdown: any, projectId: string, generating: boolean, onGenerateShots: () => void }) {
  const [shots, setShots] = useState<any[]>([]);

  useEffect(() => {
    const fetchShots = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/projects/${projectId}/production/scenes/${breakdown.scene_id}`);
        if (res.ok) {
          const data = await res.json();
          setShots(data.shots || []);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchShots();
    const int = setInterval(fetchShots, 5000);
    return () => clearInterval(int);
  }, [breakdown.scene_id, projectId]);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-bold text-gray-200">Scene {breakdown.scene_number}</h3>
          <p className="text-gray-400 mt-1">
            <span className="font-medium text-white">{breakdown.location}</span> • {breakdown.time_of_day}
          </p>
        </div>
        <button 
          onClick={onGenerateShots}
          disabled={generating}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded font-medium disabled:opacity-50"
        >
          {generating ? "Generating Shots..." : "Generate Cinematography"}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm text-gray-300 mb-6 bg-gray-950 p-4 rounded">
        <div>
          <span className="text-gray-500 block mb-1">Characters</span>
          {breakdown.characters?.join(", ") || "None"}
        </div>
        <div>
          <span className="text-gray-500 block mb-1">Props</span>
          {breakdown.props?.join(", ") || "None"}
        </div>
        <div>
          <span className="text-gray-500 block mb-1">Emotional Beat</span>
          <span className="text-pink-400">{breakdown.emotional_beat}</span>
        </div>
        <div>
          <span className="text-gray-500 block mb-1">Narrative Purpose</span>
          {breakdown.narrative_purpose}
        </div>
      </div>

      {shots.length > 0 && (
        <div className="mt-6 border-t border-gray-800 pt-6">
          <h4 className="font-bold text-gray-300 mb-4">Shot Blueprint</h4>
          <div className="grid grid-cols-1 gap-4">
            {shots.map(shot => (
              <div key={shot.id} className="bg-gray-950 border border-gray-800 p-4 rounded-lg flex gap-4">
                <div className="w-16 h-16 bg-gray-800 rounded flex items-center justify-center text-gray-500 font-bold shrink-0">
                  {shot.shot_id.split('_').pop()?.toUpperCase() || 'SHOT'}
                </div>
                <div className="flex-1">
                  <div className="flex gap-2 items-center mb-1">
                    <span className="font-bold text-white">{shot.shot_size}</span>
                    <span className="text-gray-600">•</span>
                    <span className="text-gray-400">{shot.camera_angle}</span>
                    <span className="text-gray-600">•</span>
                    <span className="text-gray-400">{shot.lens}</span>
                  </div>
                  <p className="text-sm text-gray-300 mb-2 font-semibold italic">"{shot.purpose}"</p>
                  <p className="text-xs text-gray-500 mb-2">Beat: {shot.story_beat}</p>
                  
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-400 mt-2">
                    <div><span className="text-gray-600">Lighting:</span> {shot.lighting}</div>
                    <div><span className="text-gray-600">Movement:</span> {shot.camera_movement}</div>
                    <div><span className="text-gray-600">Emotion:</span> {shot.emotion}</div>
                    <div><span className="text-gray-600">Subject:</span> {shot.subject}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
