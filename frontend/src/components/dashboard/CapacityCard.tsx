import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Bed, Users } from 'lucide-react';
import type { UnitCapacity, LocationType } from '@/types/hospital';
import { getLocationColor } from '@/lib/display-utils';

interface CapacityCardProps {
  capacity: UnitCapacity;
  className?: string;
}

function getCapacityColor(occupancyRate: number): string {
  if (occupancyRate < 0.5) return 'text-capacity-available';
  if (occupancyRate < 0.7) return 'text-capacity-moderate';
  return 'text-capacity-critical';
}

function getProgressColor(occupancyRate: number): string {
  if (occupancyRate < 0.5) return 'bg-capacity-available';
  if (occupancyRate < 0.7) return 'bg-capacity-moderate';
  return 'bg-capacity-critical';
}

function getUnitLabel(unit: LocationType): string {
  switch (unit) {
    case 'ED':
      return 'Emergency Dept';
    case 'ICU':
      return 'Intensive Care';
    case 'Ward':
      return 'General Ward';
    case 'ED_Obs':
      return 'ED Observation';
    case 'OR':
      return 'Operating Room';
    default:
      return unit;
  }
}

export function CapacityCard({ capacity, className }: CapacityCardProps) {
  const occupancyPercent = Math.round(capacity.occupancy_rate * 100);
  const colorClass = getCapacityColor(capacity.occupancy_rate);
  const progressColor = getProgressColor(capacity.occupancy_rate);

  return (
    <Card className={cn('bg-card border-border', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">
            {getUnitLabel(capacity.unit)}
          </CardTitle>
          <Badge className={cn('text-xs', getLocationColor(capacity.unit), 'text-white')}>
            {capacity.unit}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Occupancy Progress */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Bed Occupancy</span>
            <span className={cn('font-medium', colorClass)}>{occupancyPercent}%</span>
          </div>
          <div className="relative h-2 w-full overflow-hidden rounded-full bg-secondary">
            <div
              className={cn('h-full transition-all', progressColor)}
              style={{ width: `${occupancyPercent}%` }}
            />
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Bed className="h-3 w-3" />
              Available Beds
            </div>
            <p className="text-xl font-bold">
              {capacity.available_beds}
              <span className="text-sm font-normal text-muted-foreground">
                /{capacity.total_beds}
              </span>
            </p>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Users className="h-3 w-3" />
              Patients/Nurse
            </div>
            <p className="text-xl font-bold">
              {capacity.patients_per_nurse.toFixed(1)}
            </p>
          </div>
        </div>

        {/* Capacity Score */}
        <div className="flex items-center justify-between rounded-lg bg-secondary/50 px-3 py-2">
          <span className="text-sm text-muted-foreground">Capacity Score</span>
          <span className={cn('text-lg font-bold', colorClass)}>
            {Math.round(capacity.capacity_score)}%
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

interface CapacityOverviewProps {
  capacities: UnitCapacity[];
  isLoading?: boolean;
}

export function CapacityOverview({ capacities, isLoading }: CapacityOverviewProps) {
  const mainUnits = capacities.filter(c => ['ED', 'ICU', 'Ward'].includes(c.unit));

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse bg-card">
            <CardHeader className="pb-2">
              <div className="h-6 w-32 rounded bg-muted" />
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="h-2 w-full rounded bg-muted" />
              <div className="grid grid-cols-2 gap-4">
                <div className="h-12 rounded bg-muted" />
                <div className="h-12 rounded bg-muted" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {mainUnits.map((capacity) => (
        <CapacityCard key={capacity.unit} capacity={capacity} />
      ))}
    </div>
  );
}
