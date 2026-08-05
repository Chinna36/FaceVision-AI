import { Card } from '@/components/ui/card.tsx';
import { cn } from '@/lib/utils.js';

export function AnalyticsCard({
  title,
  value,
  icon: Icon,
  description,
  color = 'primary',
  delay = 0,
  onClick,
}) {
  const colorClasses = {
    primary: 'bg-primary/10 text-primary border-primary/20',
    success: 'bg-success/10 text-success border-success/20',
    warning: 'bg-warning/10 text-warning border-warning/20',
    destructive: 'bg-destructive/10 text-destructive border-destructive/20',
  };

  const iconBgClasses = {
    primary: 'bg-primary/10',
    success: 'bg-success/10',
    warning: 'bg-warning/10',
    destructive: 'bg-destructive/10',
  };

  const iconTextClasses = {
    primary: 'text-primary',
    success: 'text-success',
    warning: 'text-warning',
    destructive: 'text-destructive',
  };

  return (
    <Card 
      variant="glass" 
      className={cn(
        "p-6 animate-slide-up hover:-translate-y-1 cursor-pointer",
        colorClasses[color]
      )}
      style={{ animationDelay: `${delay}ms` }}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-4xl font-bold tracking-tight">{value.toLocaleString()}</p>
          {description && (
            <p className="text-xs text-muted-foreground">{description}</p>
          )}
        </div>
        <div className={cn(
          "flex h-12 w-12 items-center justify-center rounded-xl",
          iconBgClasses[color]
        )}>
          <Icon className={cn("h-6 w-6", iconTextClasses[color])} />
        </div>
      </div>
    </Card>
  );
}
