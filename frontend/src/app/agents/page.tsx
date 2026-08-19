"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Cpu, Terminal, Bot } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export default function AgentPlayground() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Agent Playground</h1>
        <p className="text-muted-foreground mt-1">Interact directly with specialized AI agents.</p>
      </div>

      <div className="h-[600px] border border-dashed border-border rounded-xl flex items-center justify-center bg-card/30">
        <div className="text-center max-w-md">
          <div className="flex justify-center gap-4 mb-6 text-muted-foreground opacity-50">
            <Bot className="w-12 h-12" />
            <Cpu className="w-12 h-12" />
            <Terminal className="w-12 h-12" />
          </div>
          <h2 className="text-xl font-bold mb-2">Agent Framework Pending</h2>
          <p className="text-muted-foreground mb-6">
            The Multi-Agent Orchestration layer (Storyboard Agent, Script Agent) will be implemented here in Phase 6.
          </p>
          <Badge variant="outline" className="text-xs uppercase tracking-widest px-3 py-1">Future Scope</Badge>
        </div>
      </div>
    </div>
  );
}
