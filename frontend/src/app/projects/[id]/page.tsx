"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Project, fetchProject } from "@/lib/api";

export default function ProjectDashboardPage() {
  const params = useParams();
  const id = params.id as string;
  
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    fetchProject(id)
      .then(setProject)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <div className="container mx-auto px-4 py-8 text-gray-400">Loading dashboard...</div>;
  }

  if (!project) {
    return <div className="container mx-auto px-4 py-8 text-red-400">Project not found.</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <Link href="/projects" className="text-indigo-400 hover:text-indigo-300 text-sm font-medium mb-4 inline-block">
          &larr; Back to Projects
        </Link>
        <h1 className="text-3xl font-bold text-gray-100">{project.name}</h1>
        <p className="text-gray-400 mt-2">Project Dashboard</p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 mb-8 text-sm">
        <h3 className="text-gray-500 font-semibold uppercase tracking-wider mb-3">Project Details</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div><span className="text-gray-500">Genre:</span> <span className="text-gray-300">{project.genre}</span></div>
          <div><span className="text-gray-500">Tone:</span> <span className="text-gray-300">{project.tone}</span></div>
          <div><span className="text-gray-500">Duration:</span> <span className="text-gray-300">{project.duration}</span></div>
          <div><span className="text-gray-500">Style:</span> <span className="text-gray-300">{project.visual_style}</span></div>
        </div>
        {project.source_material && (
          <div className="mt-4">
            <span className="text-gray-500">Source Material Attached:</span>
            <div className="text-gray-400 italic truncate mt-1">{project.source_material}</div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Script Studio Card */}
        <Link href={`/projects/${project.id}/script`} className="block group">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 hover:border-indigo-500 hover:shadow-lg transition-all h-full flex flex-col">
            <div className="mb-4">
              <h2 className="text-2xl font-bold text-gray-100 group-hover:text-indigo-400 transition-colors">Script Studio</h2>
            </div>
            <p className="text-gray-400 text-sm mb-6 flex-grow">
              Orchestrate your script with the AI Copilot. Generate screenplays, regenerate scenes, and perfect your story before storyboarding.
            </p>
            <div className="mt-auto flex justify-end">
              <span className="text-indigo-400 text-sm font-medium group-hover:translate-x-1 transition-transform">
                Enter Studio &rarr;
              </span>
            </div>
          </div>
        </Link>

        {/* Cinematography Card */}
        <Link href={`/projects/${project.id}/cinematography`} className="block group">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 hover:border-indigo-500 hover:shadow-lg transition-all h-full flex flex-col">
            <div className="mb-4">
              <h2 className="text-2xl font-bold text-gray-100 group-hover:text-indigo-400 transition-colors">Cinematography & Color</h2>
            </div>
            <p className="text-gray-400 text-sm mb-6 flex-grow">
              Review Scene Visual Plans, Color Palettes, and Cinematography Shot Blueprints generated from your approved script.
            </p>
            <div className="mt-auto flex justify-end">
              <span className="text-indigo-400 text-sm font-medium group-hover:translate-x-1 transition-transform">
                View Plan &rarr;
              </span>
            </div>
          </div>
        </Link>
        
        {/* Storyboard Card */}
        <Link href={`/projects/${project.id}/storyboard`} className="block group">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 hover:border-indigo-500 hover:shadow-lg transition-all h-full flex flex-col">
            <div className="mb-4">
              <h2 className="text-2xl font-bold text-gray-100 group-hover:text-indigo-400 transition-colors">Storyboard</h2>
            </div>
            <p className="text-gray-400 text-sm mb-6 flex-grow">
              Visualize your script. Generate, review, and approve storyboard frames for each shot blueprint in your production plan.
            </p>
            <div className="mt-auto flex justify-end">
              <span className="text-indigo-400 text-sm font-medium group-hover:translate-x-1 transition-transform">
                Open Storyboard &rarr;
              </span>
            </div>
          </div>
        </Link>
      </div>
    </div>
  );
}
