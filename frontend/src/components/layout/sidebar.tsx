"use client";

import Link from "next/link";
import { Film, LayoutDashboard, FileText, Clapperboard, Users, Image as ImageIcon, Video, Bot, Terminal, Camera, Activity, Wand2 } from "lucide-react";
import { usePathname } from "next/navigation";

export function Sidebar() {
  const pathname = usePathname();
  const projectId = pathname.match(/\/projects\/([^/]+)/)?.[1];

  const LinkItem = ({ href, icon: Icon, children }: { href: string, icon: any, children: React.ReactNode }) => {
    const active = pathname === href || pathname.startsWith(href + '/');
    return (
      <Link href={href} className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${active ? 'bg-primary/10 text-primary' : 'hover:bg-accent hover:text-accent-foreground'}`}>
        <Icon className="w-4 h-4 mr-3" />
        {children}
      </Link>
    );
  };

  return (
    <div className="w-64 border-r border-border bg-card flex flex-col h-full">
      <div className="h-16 flex items-center px-6 border-b border-border">
        <Film className="w-6 h-6 mr-3 text-primary" />
        <span className="font-bold text-lg tracking-tight">Lumierecraft</span>
      </div>
      
      <div className="flex-1 py-6 flex flex-col gap-1 px-3 overflow-y-auto">
        <LinkItem href="/projects" icon={LayoutDashboard}>Projects</LinkItem>
        
        {projectId && (
          <div className="mt-2 space-y-1 ml-4 border-l-2 border-border pl-2 pb-4">
            <LinkItem href={`/projects/${projectId}`} icon={Film}>Story</LinkItem>
            <LinkItem href={`/projects/${projectId}/script`} icon={FileText}>Script Studio</LinkItem>
            <LinkItem href={`/projects/${projectId}/scenes`} icon={Clapperboard}>Scenes</LinkItem>
            <LinkItem href={`/projects/${projectId}/characters`} icon={Users}>Characters & World</LinkItem>
            <LinkItem href={`/projects/${projectId}/storyboard`} icon={ImageIcon}>Storyboard</LinkItem>
            <LinkItem href={`/projects/${projectId}/production`} icon={Video}>Production</LinkItem>
          </div>
        )}

        <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mt-6 mb-2 px-3">
          AI AGENTS
        </div>
        <LinkItem href="/agents/writer" icon={Bot}>Script Writer</LinkItem>
        <LinkItem href="/agents/storyboard" icon={Wand2}>Storyboard Agent</LinkItem>
        <LinkItem href="/agents/cinematography" icon={Camera}>Cinematography</LinkItem>
        <LinkItem href="/agents/continuity" icon={Film}>Continuity</LinkItem>

        <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mt-6 mb-2 px-3">
          DEVELOPER
        </div>
        <LinkItem href="/lab" icon={ImageIcon}>Image Generation Lab</LinkItem>
        <LinkItem href="/providers" icon={Terminal}>Provider Monitor</LinkItem>
        <LinkItem href="/developer/system" icon={Activity}>System Status</LinkItem>
      </div>
    </div>
  );
}
