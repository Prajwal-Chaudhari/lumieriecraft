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

        {/* Future modules placeholders */}
        <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 p-6 opacity-60">
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-gray-400">Storyboard Agent</h2>
          </div>
          <p className="text-gray-500 text-sm mb-6">
            Generate visual storyboards for your script scenes. (Coming soon)
          </p>
        </div>
        
        <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 p-6 opacity-60">
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-gray-400">Cinematography Agent</h2>
          </div>
          <p className="text-gray-500 text-sm mb-6">
            Define exact camera angles and shots. (Coming soon)
          </p>
        </div>
      </div>
    </div>
  );
}
