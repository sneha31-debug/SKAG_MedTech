import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { TrendingUp, TrendingDown, Minus, Clock } from 'lucide-react';
import type { Patient, RiskAssessment, Trajectory, PatientWithRisk } from '@/types/hospital';
import {
  getRiskColor,
  getRiskBgColor,
  getTrajectoryInfo,
  getLocationColor,
  formatWaitTime,
} from '@/lib/display-utils';

interface PatientCardProps {
  patient: Patient;
  riskAssessment?: RiskAssessment;
  onClick?: () => void;
  isSelected?: boolean;
}

function TrajectoryIcon({ trajectory }: { trajectory: Trajectory }) {
  const info = getTrajectoryInfo(trajectory);
  
  switch (info.icon) {
    case 'up':
      return <TrendingUp className={cn('h-4 w-4', info.color)} />;
    case 'down':
      return <TrendingDown className={cn('h-4 w-4', info.color)} />;
    default:
      return <Minus className={cn('h-4 w-4', info.color)} />;
  }
}

export function PatientCard({ patient, riskAssessment, onClick, isSelected }: PatientCardProps) {
  const riskScore = riskAssessment?.risk_score ?? 0;
  const trajectory = riskAssessment?.trajectory ?? 'stable';
  const isCritical = trajectory === 'critical' || riskScore >= 90;

  return (
    <Card
      className={cn(
        'cursor-pointer border-border bg-card p-4 transition-all hover:bg-accent',
        isSelected && 'ring-2 ring-primary',
        isCritical && 'animate-glow-critical border-risk-high'
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-3">
        {/* Patient Info */}
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-foreground">{patient.name}</h3>
            <span className="text-sm text-muted-foreground">{patient.age}y</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge
              className={cn(
                'text-xs',
                getLocationColor(patient.current_location),
                'text-white border-0'
              )}
            >
              {patient.current_location}
            </Badge>
            <span className="text-xs text-muted-foreground line-clamp-1">
              {patient.chief_complaint}
            </span>
          </div>
        </div>

        {/* Risk Score & Trajectory */}
        <div className="flex flex-col items-end gap-2">
          <div
            className={cn(
              'flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold text-white',
              getRiskBgColor(riskScore)
            )}
          >
            {riskScore}
          </div>
          <div className="flex items-center gap-1">
            <TrajectoryIcon trajectory={trajectory} />
            <span className={cn('text-xs', getTrajectoryInfo(trajectory).color)}>
              {getTrajectoryInfo(trajectory).label}
            </span>
          </div>
        </div>
      </div>

      {/* Wait Time */}
      <div className="mt-3 flex items-center gap-1 text-xs text-muted-foreground">
        <Clock className="h-3 w-3" />
        <span>Wait: {formatWaitTime(patient.arrival_time)}</span>
      </div>
    </Card>
  );
}

interface PatientQueueProps {
  patients: PatientWithRisk[];
  selectedPatientId?: string | null;
  onPatientClick: (patient: Patient) => void;
  isLoading?: boolean;
}

export function PatientQueue({
  patients,
  selectedPatientId,
  onPatientClick,
  isLoading,
}: PatientQueueProps) {
  // Sort by risk score (highest first) then by arrival time (oldest first)
  const sortedPatients = [...patients].sort((a, b) => {
    const riskA = a.risk_assessment?.risk_score ?? 0;
    const riskB = b.risk_assessment?.risk_score ?? 0;
    if (riskB !== riskA) return riskB - riskA;
    return new Date(a.arrival_time).getTime() - new Date(b.arrival_time).getTime();
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <Card key={i} className="animate-pulse bg-card p-4">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="h-5 w-32 rounded bg-muted" />
                <div className="h-4 w-24 rounded bg-muted" />
              </div>
              <div className="h-10 w-10 rounded-full bg-muted" />
            </div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="space-y-3 pr-4">
        {sortedPatients.map((patient) => (
          <PatientCard
            key={patient.patient_id}
            patient={patient}
            riskAssessment={patient.risk_assessment}
            isSelected={patient.patient_id === selectedPatientId}
            onClick={() => onPatientClick(patient)}
          />
        ))}
        {sortedPatients.length === 0 && (
          <div className="py-8 text-center text-muted-foreground">
            No patients in queue
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
