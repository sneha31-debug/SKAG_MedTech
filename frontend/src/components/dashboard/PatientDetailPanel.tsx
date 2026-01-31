import { X, TrendingUp, TrendingDown, Minus, Clock, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from 'recharts';
import type { Patient, RiskAssessment, VitalSigns, Decision, MCDAScores, Trajectory } from '@/types/hospital';
import {
  getRiskBgColor,
  getTrajectoryInfo,
  getLocationColor,
  getActionInfo,
  formatDateTime,
  formatTimestamp,
} from '@/lib/display-utils';
import { usePatientVitals, usePatientRisk } from '@/hooks/usePatients';
import { useDecisions } from '@/hooks/useDecisions';

interface PatientDetailPanelProps {
  patient: Patient | null;
  onClose: () => void;
}

function TrajectoryIcon({ trajectory }: { trajectory: Trajectory }) {
  const info = getTrajectoryInfo(trajectory);
  switch (info.icon) {
    case 'up':
      return <TrendingUp className={cn('h-5 w-5', info.color)} />;
    case 'down':
      return <TrendingDown className={cn('h-5 w-5', info.color)} />;
    default:
      return <Minus className={cn('h-5 w-5', info.color)} />;
  }
}

const vitalsChartConfig: ChartConfig = {
  heart_rate: {
    label: 'Heart Rate',
    color: 'hsl(var(--chart-1))',
  },
  oxygen_saturation: {
    label: 'O2 Sat',
    color: 'hsl(var(--chart-2))',
  },
  blood_pressure_systolic: {
    label: 'BP Systolic',
    color: 'hsl(var(--chart-3))',
  },
};

function VitalsChart({ vitals }: { vitals: VitalSigns[] }) {
  const chartData = vitals.slice(-20).map((v, i) => ({
    time: formatTimestamp(v.timestamp),
    heart_rate: v.heart_rate,
    oxygen_saturation: v.oxygen_saturation,
    blood_pressure_systolic: v.blood_pressure_systolic,
  }));

  if (chartData.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-muted-foreground">
        No vitals data available
      </div>
    );
  }

  return (
    <ChartContainer config={vitalsChartConfig} className="h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 10 }}
            tickLine={false}
            className="text-muted-foreground"
          />
          <YAxis tick={{ fontSize: 10 }} tickLine={false} className="text-muted-foreground" />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Line
            type="monotone"
            dataKey="heart_rate"
            stroke="var(--color-heart_rate)"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="oxygen_saturation"
            stroke="var(--color-oxygen_saturation)"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="blood_pressure_systolic"
            stroke="var(--color-blood_pressure_systolic)"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}

function MCDABreakdown({ scores }: { scores?: MCDAScores }) {
  if (!scores) {
    return (
      <div className="text-sm text-muted-foreground">
        MCDA scores not available
      </div>
    );
  }

  const items = [
    { label: 'Safety', value: scores.safety_score },
    { label: 'Urgency', value: scores.urgency_score },
    { label: 'Capacity', value: scores.capacity_score },
    { label: 'Impact', value: scores.impact_score },
  ];

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.label} className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">{item.label}</span>
            <span className="font-medium">{Math.round(item.value * 100)}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
            <div
              className="h-full bg-primary transition-all"
              style={{ width: `${item.value * 100}%` }}
            />
          </div>
        </div>
      ))}
      <Separator />
      <div className="flex justify-between">
        <span className="font-medium">Weighted Total</span>
        <span className="text-lg font-bold text-primary">
          {Math.round(scores.weighted_total * 100)}%
        </span>
      </div>
    </div>
  );
}

export function PatientDetailPanel({ patient, onClose }: PatientDetailPanelProps) {
  const { data: vitals } = usePatientVitals(patient?.patient_id ?? null);
  const { data: riskAssessment } = usePatientRisk(patient?.patient_id ?? null);
  const { data: allDecisions } = useDecisions();

  if (!patient) return null;

  const patientDecisions = allDecisions?.filter((d) => d.patient_id === patient.patient_id) ?? [];
  const riskScore = riskAssessment?.risk_score ?? 0;
  const trajectory = riskAssessment?.trajectory ?? 'stable';
  const trajectoryInfo = getTrajectoryInfo(trajectory);

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-lg animate-slide-in-right border-l border-border bg-background shadow-xl">
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-border p-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold">{patient.name}</h2>
              <Badge
                className={cn(getLocationColor(patient.current_location), 'text-white border-0')}
              >
                {patient.current_location}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              {patient.age}y, {patient.gender} • {patient.chief_complaint}
            </p>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              Arrived: {formatDateTime(patient.arrival_time)}
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Content */}
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-6">
            {/* Medical History */}
            {patient.medical_history.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {patient.medical_history.map((history) => (
                  <Badge key={history} variant="secondary" className="text-xs">
                    {history}
                  </Badge>
                ))}
              </div>
            )}

            {/* Vitals Chart */}
            <Card className="border-border bg-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Vitals Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <VitalsChart vitals={vitals ?? patient.vitals} />
                <div className="mt-2 flex gap-4 text-xs">
                  <div className="flex items-center gap-1">
                    <div className="h-2 w-2 rounded-full bg-chart-1" />
                    <span>HR</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="h-2 w-2 rounded-full bg-chart-2" />
                    <span>O2</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="h-2 w-2 rounded-full bg-chart-3" />
                    <span>BP</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Risk Assessment */}
            <Card className="border-border bg-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Risk Assessment</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-6">
                  <div
                    className={cn(
                      'flex h-20 w-20 items-center justify-center rounded-full text-2xl font-bold text-white',
                      getRiskBgColor(riskScore)
                    )}
                  >
                    {riskScore}
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <TrajectoryIcon trajectory={trajectory} />
                      <span className={cn('font-medium', trajectoryInfo.color)}>
                        {trajectoryInfo.label}
                      </span>
                    </div>
                    {riskAssessment?.confidence && (
                      <p className="text-sm text-muted-foreground">
                        Confidence: {Math.round(riskAssessment.confidence * 100)}%
                      </p>
                    )}
                  </div>
                </div>
                {riskAssessment?.contributing_factors && (
                  <div className="mt-4 space-y-2">
                    <p className="text-sm font-medium">Contributing Factors</p>
                    <div className="flex flex-wrap gap-2">
                      {riskAssessment.contributing_factors.map((factor) => (
                        <Badge key={factor} variant="outline" className="text-xs">
                          <AlertTriangle className="mr-1 h-3 w-3" />
                          {factor}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* MCDA Breakdown - placeholder for future data */}
            <Card className="border-border bg-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">MCDA Score Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <MCDABreakdown />
              </CardContent>
            </Card>

            {/* Recent Decisions */}
            <Card className="border-border bg-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Recent Decisions</CardTitle>
              </CardHeader>
              <CardContent>
                {patientDecisions.length > 0 ? (
                  <div className="space-y-3">
                    {patientDecisions.slice(0, 5).map((decision) => {
                      const actionInfo = getActionInfo(decision.action);
                      return (
                        <div
                          key={decision.decision_id}
                          className="rounded-lg border border-border bg-secondary/30 p-3"
                        >
                          <div className="flex items-center justify-between">
                            <Badge
                              className={cn(
                                'text-xs font-bold border-0',
                                actionInfo.bgColor,
                                actionInfo.color
                              )}
                            >
                              {actionInfo.label}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {formatTimestamp(decision.timestamp)}
                            </span>
                          </div>
                          <p className="mt-2 text-sm text-muted-foreground">{decision.reasoning}</p>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {decision.agent_name} • {Math.round(decision.confidence * 100)}% confidence
                          </p>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No decisions for this patient yet</p>
                )}
              </CardContent>
            </Card>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
