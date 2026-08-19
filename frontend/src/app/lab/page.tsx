"use client";

import { useState, useEffect } from "react";
import { fetchProviders, generateImage, Provider, GenerationResult } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, Image as ImageIcon, Download, Settings2 } from "lucide-react";

export default function ImageGenerationLab() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState("mock");
  const [prompt, setPrompt] = useState("A cinematic shot of a cyberpunk city at night, neon lights reflecting in puddles");
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<GenerationResult[]>([]);

  useEffect(() => {
    fetchProviders().then(data => {
      setProviders(data);
      if (data.length > 0 && !data.find(p => p.name === selectedProvider)) {
        setSelectedProvider(data[0].name);
      }
    }).catch(console.error);
    
    // Load history
    const saved = localStorage.getItem("lumierecraft_history");
    if (saved) {
      try { setHistory(JSON.parse(saved)); } catch (e) {}
    }
  }, []);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setIsGenerating(true);
    setError(null);
    try {
      const res = await generateImage({
        project_id: "lab_project",
        scene_id: "lab_scene",
        shot_id: "lab_shot",
        prompt,
        mode: "storyboard_sketch",
      });
      // The FastAPI backend selects provider based on os.environ currently, 
      // but assuming the backend gets the provider from request eventually.
      // For now we just hit the endpoint. If we wanted to force provider, 
      // we'd need to send it in the request and have backend support it,
      // but for this lab, we assume the backend handles it or we'll add provider to req.
      
      setResult(res);
      const newHistory = [res, ...history].slice(0, 10);
      setHistory(newHistory);
      localStorage.setItem("lumierecraft_history", JSON.stringify(newHistory));
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Image Generation Lab</h1>
        <p className="text-muted-foreground mt-1">Directly test the provider registry and generation pipeline.</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6 flex-1">
        {/* Controls */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="bg-card/50 backdrop-blur">
            <CardContent className="p-6 space-y-6">
              <div className="space-y-2">
                <Label>Provider</Label>
                <Select value={selectedProvider} onValueChange={setSelectedProvider}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select provider" />
                  </SelectTrigger>
                  <SelectContent>
                    {providers.map(p => (
                      <SelectItem key={p.name} value={p.name} disabled={!p.available}>
                        {p.name.toUpperCase()} {!p.available && "(Unavailable)"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Prompt</Label>
                  <Button variant="link" className="h-auto p-0 text-xs text-muted-foreground">Enhance</Button>
                </div>
                <Textarea 
                  rows={5} 
                  placeholder="Describe the shot..." 
                  value={prompt}
                  onChange={e => setPrompt(e.target.value)}
                  className="resize-none bg-muted/50"
                />
              </div>

              <div className="space-y-2">
                <Label className="flex items-center text-muted-foreground"><Settings2 className="w-3 h-3 mr-2"/> Advanced Settings (Disabled)</Label>
                <div className="grid grid-cols-2 gap-2 opacity-50 pointer-events-none">
                  <Select disabled><SelectTrigger><SelectValue placeholder="Seed: Random" /></SelectTrigger></Select>
                  <Select disabled><SelectTrigger><SelectValue placeholder="Aspect: 16:9" /></SelectTrigger></Select>
                </div>
              </div>

              <Button 
                className="w-full font-semibold shadow-lg shadow-primary/20" 
                size="lg"
                onClick={handleGenerate}
                disabled={isGenerating || !prompt.trim()}
              >
                {isGenerating ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Generating...</> : 'Generate Shot'}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Output */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <Card className="flex-1 bg-card/50 backdrop-blur min-h-[400px] overflow-hidden flex flex-col relative border-primary/10">
            {isGenerating && (
              <div className="absolute inset-0 z-10 bg-background/80 backdrop-blur-sm flex flex-col items-center justify-center">
                <Loader2 className="w-12 h-12 animate-spin text-primary mb-4" />
                <p className="text-sm font-medium animate-pulse text-muted-foreground">Synthesizing pixels through {selectedProvider}...</p>
              </div>
            )}
            
            {error && (
              <div className="absolute inset-0 z-10 bg-destructive/10 flex items-center justify-center p-6">
                <div className="text-destructive font-medium text-center bg-background/90 p-4 rounded-md border border-destructive/20 shadow-xl">
                  {error}
                </div>
              </div>
            )}

            {!result && !isGenerating && !error && (
              <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
                <ImageIcon className="w-16 h-16 mb-4 opacity-20" />
                <p>Output will appear here</p>
              </div>
            )}

            {result && !isGenerating && (
              <div className="flex-1 flex flex-col">
                <div className="flex-1 p-6 flex items-center justify-center bg-black/40">
                  <img 
                    src={result.image_urls[0]} 
                    alt="Generated" 
                    className="max-w-full max-h-[500px] object-contain shadow-2xl ring-1 ring-white/10 rounded-sm"
                  />
                </div>
                <div className="p-4 border-t border-border/50 bg-muted/20 flex justify-between items-center text-xs text-muted-foreground">
                  <div className="flex gap-4">
                    <span>Provider: <strong className="text-foreground">{result.provider}</strong></span>
                    <span>Model: <strong className="text-foreground">{result.model}</strong></span>
                    <span>Seed: <strong className="text-foreground">{result.seed}</strong></span>
                  </div>
                  <Button variant="ghost" size="sm" className="h-8 gap-2">
                    <Download className="w-3 h-3" /> Save
                  </Button>
                </div>
              </div>
            )}
          </Card>

          {/* History */}
          {history.length > 0 && (
            <div>
              <h3 className="text-sm font-medium mb-3 text-muted-foreground">Recent Generations</h3>
              <div className="flex gap-4 overflow-x-auto pb-4 snap-x">
                {history.map(h => (
                  <div key={h.generation_id} className="relative group shrink-0 w-32 aspect-video rounded-md overflow-hidden ring-1 ring-border snap-start cursor-pointer hover:ring-primary/50 transition-all" onClick={() => setResult(h)}>
                    <img src={h.image_urls[0]} alt="History" className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex items-center justify-center text-[10px] font-medium transition-opacity">
                      {h.provider}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
