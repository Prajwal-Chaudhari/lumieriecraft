"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createProject, ProjectCreate } from "@/lib/api";

type WorkflowType = 'concept' | 'rough_script' | 'scratch';

export default function NewProjectPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [workflow, setWorkflow] = useState<WorkflowType>('rough_script');
  
  const [formData, setFormData] = useState<ProjectCreate>({
    name: "",
    story_idea: "",
    source_material: "",
    genre: "Sci-Fi",
    duration: "Feature",
    tone: "Dark",
    visual_style: "Cinematic"
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    // Auto-fill story_idea based on workflow if empty
    const dataToSubmit = { ...formData };
    if (workflow === 'rough_script' && dataToSubmit.source_material && !dataToSubmit.story_idea) {
      dataToSubmit.story_idea = "Enhanced from rough script.";
    } else if (workflow === 'scratch') {
      dataToSubmit.story_idea = "Writing from scratch.";
    }

    try {
      const project = await createProject(dataToSubmit);
      router.push(`/projects/${project.id}/script`);
    } catch (err: any) {
      setError(err.message || "Failed to create project");
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <div className="mb-8">
        <Link href="/projects" className="text-indigo-400 hover:text-indigo-300 text-sm font-medium mb-4 inline-block">
          &larr; Back to Projects
        </Link>
        <h1 className="text-3xl font-bold text-gray-100">Create New Project</h1>
        <p className="text-gray-400 mt-2">Start your collaborative cinematic journey.</p>
      </div>

      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 sm:p-8">
        {error && (
          <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Project Name</label>
            <input
              type="text"
              name="name"
              required
              value={formData.name}
              onChange={handleChange}
              className="w-full bg-gray-900 border border-gray-700 rounded-md px-4 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g. The Last Light"
            />
          </div>

          <div className="pt-4 pb-2">
            <h3 className="text-sm font-medium text-gray-300 mb-3">How do you want to begin?</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setWorkflow('rough_script')}
                className={`p-3 border rounded-md text-left transition-colors ${
                  workflow === 'rough_script' 
                    ? 'bg-indigo-900/40 border-indigo-500 text-indigo-100' 
                    : 'bg-gray-900 border-gray-700 text-gray-400 hover:bg-gray-800'
                }`}
              >
                <div className="font-semibold mb-1 text-sm">Enhance Rough Script</div>
                <div className="text-xs opacity-70">Paste raw text or screenplay draft (⭐ Primary Workflow)</div>
              </button>
              
              <button
                type="button"
                onClick={() => setWorkflow('concept')}
                className={`p-3 border rounded-md text-left transition-colors ${
                  workflow === 'concept' 
                    ? 'bg-indigo-900/40 border-indigo-500 text-indigo-100' 
                    : 'bg-gray-900 border-gray-700 text-gray-400 hover:bg-gray-800'
                }`}
              >
                <div className="font-semibold mb-1 text-sm">Start with a Concept</div>
                <div className="text-xs opacity-70">Provide a short treatment or story idea</div>
              </button>

              <button
                type="button"
                onClick={() => setWorkflow('scratch')}
                className={`p-3 border rounded-md text-left transition-colors ${
                  workflow === 'scratch' 
                    ? 'bg-indigo-900/40 border-indigo-500 text-indigo-100' 
                    : 'bg-gray-900 border-gray-700 text-gray-400 hover:bg-gray-800'
                }`}
              >
                <div className="font-semibold mb-1 text-sm">Write from Scratch</div>
                <div className="text-xs opacity-70">Start with a blank canvas and AI assistance</div>
              </button>
            </div>
          </div>

          {workflow === 'concept' && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Story Idea / Treatment</label>
              <textarea
                name="story_idea"
                required
                rows={6}
                value={formData.story_idea}
                onChange={handleChange}
                className="w-full bg-gray-900 border border-gray-700 rounded-md px-4 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="A brief summary of your story..."
              />
            </div>
          )}

          {workflow === 'rough_script' && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Rough Script / Source Material</label>
              <textarea
                name="source_material"
                required
                rows={10}
                value={formData.source_material}
                onChange={handleChange}
                className="w-full bg-gray-900 border border-gray-700 rounded-md px-4 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
                placeholder="Paste your rough script, dialogue ideas, or scene notes here. Lumierecraft will structure and enhance it cinematically..."
              />
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Genre</label>
              <input
                type="text"
                name="genre"
                required
                value={formData.genre}
                onChange={handleChange}
                className="w-full bg-gray-900 border border-gray-700 rounded-md px-4 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Duration</label>
              <input
                type="text"
                name="duration"
                required
                value={formData.duration}
                onChange={handleChange}
                className="w-full bg-gray-900 border border-gray-700 rounded-md px-4 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Feature, Short, TV Pilot"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Tone</label>
              <input
                type="text"
                name="tone"
                required
                value={formData.tone}
                onChange={handleChange}
                className="w-full bg-gray-900 border border-gray-700 rounded-md px-4 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Visual Style</label>
              <input
                type="text"
                name="visual_style"
                required
                value={formData.visual_style}
                onChange={handleChange}
                className="w-full bg-gray-900 border border-gray-700 rounded-md px-4 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="pt-6 flex justify-end">
            <button
              type="button"
              onClick={() => router.push('/projects')}
              className="px-4 py-2 text-gray-300 hover:text-white mr-4"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-8 py-2 rounded-md font-medium transition-colors"
            >
              {loading ? "Creating..." : "Create Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
