"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Project, fetchProjects } from "@/lib/api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProjects()
      .then(setProjects)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-100">Your Projects</h1>
        <Link 
          href="/projects/new" 
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
        >
          New Project
        </Link>
      </div>

      {loading ? (
        <div className="text-gray-400">Loading projects...</div>
      ) : projects.length === 0 ? (
        <div className="bg-gray-800 rounded-lg p-12 text-center border border-gray-700">
          <h2 className="text-xl font-semibold text-gray-300 mb-2">No projects yet</h2>
          <p className="text-gray-500 mb-6">Create your first cinematic project to get started.</p>
          <Link 
            href="/projects/new" 
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
          >
            Create New Project
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((p) => (
            <Link key={p.id} href={`/projects/${p.id}/script`} className="block group">
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 hover:border-indigo-500 hover:shadow-lg transition-all h-full flex flex-col">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-bold text-gray-100 group-hover:text-indigo-400 transition-colors">{p.name}</h3>
                  <span className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded-full uppercase tracking-wider">{p.genre}</span>
                </div>
                <p className="text-gray-400 text-sm mb-4 line-clamp-3 flex-grow">{p.story_idea}</p>
                <div className="flex text-xs text-gray-500 justify-between items-center mt-auto pt-4 border-t border-gray-700">
                  <span>{p.duration}</span>
                  <span>{p.created_at ? new Date(p.created_at).toLocaleDateString() : "Created recently"}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
