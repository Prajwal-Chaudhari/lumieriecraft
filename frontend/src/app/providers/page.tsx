"use client";

import { useEffect, useState } from "react";
import { fetchProviders, Provider } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle } from "lucide-react";

export default function ProviderMonitor() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProviders().then((data) => {
      setProviders(data);
      setLoading(false);
    }).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Provider Monitor</h1>
        <p className="text-muted-foreground mt-1">Inspect integration status and capabilities of all image generation providers.</p>
      </div>

      {loading ? (
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {[1,2,3].map(i => <div key={i} className="h-64 animate-pulse bg-muted rounded-xl" />)}
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {providers.map((p) => (
            <Card key={p.name} className={`bg-card/50 backdrop-blur ${p.configured ? 'border-primary/30' : 'border-border'}`}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <CardTitle className="uppercase tracking-wider text-lg">{p.name}</CardTitle>
                    <CardDescription>
                      {p.configured ? 'API keys configured' : 'Missing API configuration'}
                    </CardDescription>
                  </div>
                  {p.available ? (
                    <Badge className="bg-green-500/10 text-green-500 hover:bg-green-500/20 border-green-500/20 gap-1"><CheckCircle2 className="w-3 h-3"/> Connected</Badge>
                  ) : (
                    <Badge variant="secondary" className="gap-1"><XCircle className="w-3 h-3"/> Unavailable</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-2">Capabilities</div>
                  <div className="space-y-2">
                    {Object.entries(p.capabilities).map(([key, supported]) => {
                      const label = key.replace('supports_', '').replace(/_/g, ' ');
                      return (
                        <div key={key} className="flex justify-between items-center text-sm">
                          <span className="capitalize">{label}</span>
                          {supported ? (
                            <span className="text-primary flex items-center gap-1"><CheckCircle2 className="w-3 h-3"/> Yes</span>
                          ) : (
                            <span className="text-muted-foreground flex items-center gap-1"><XCircle className="w-3 h-3"/> Unsupported</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
