import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog.tsx';
import { ScrollArea } from '@/components/ui/scroll-area.tsx';
import { Card } from '@/components/ui/card.tsx';
import { Smile, Frown, AlertTriangle, Heart, Shield } from 'lucide-react';
import { cn } from '@/lib/utils.js';

export function ResultsDialog({ open, onOpenChange, title, results, filterType }) {
  // Filter results based on type
  const filteredResults = results.filter(r => {
    if (filterType === 'smile') return r.smile === 'Smiling';
    if (filterType === 'mask') return r.mask === 'Mask';
    if (filterType === 'emotion') return r.emotion;
    return true;
  });

  const getEmotionIcon = (emotion) => {
    switch (emotion) {
      case 'happy': return <Smile className="h-4 w-4 text-success" />;
      case 'sad': return <Frown className="h-4 w-4 text-primary" />;
      case 'anger': return <AlertTriangle className="h-4 w-4 text-warning" />;
      case 'fear': return <Heart className="h-4 w-4 text-destructive" />;
      default: return <Smile className="h-4 w-4" />;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <ScrollArea className="h-[60vh] pr-4">
          {filteredResults.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <p>No results yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredResults.map((result) => (
                <Card key={result.id} variant="glass" className="p-4">
                  <div className="flex gap-4">
                    {result.image_base64 && (
                      <img 
                        src={`data:image/jpeg;base64,${result.image_base64}`}
                        alt="Capture"
                        className="w-20 h-20 object-cover rounded-lg shrink-0"
                      />
                    )}
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getEmotionIcon(result.emotion)}
                          <span className="font-medium capitalize">{result.emotion}</span>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {new Date(result.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-sm">
                        <div className={cn(
                          "px-2 py-1 rounded text-center",
                          result.smile === 'Smiling' ? 'bg-success/10 text-success' : 'bg-muted'
                        )}>
                          {result.smile}
                        </div>
                        <div className="px-2 py-1 rounded bg-muted text-center">
                          Age: {result.age}
                        </div>
                        <div className={cn(
                          "px-2 py-1 rounded text-center flex items-center justify-center gap-1",
                          result.mask === 'Mask' ? 'bg-warning/10 text-warning' : 'bg-muted'
                        )}>
                          {result.mask === 'Mask' && <Shield className="h-3 w-3" />}
                          {result.mask}
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
