// AdaptiveCare Hospital System Types
// Matches the FastAPI backend data models

export type Gender = 'male' | 'female' | 'other';
export type LocationType = 'ED' | 'ICU' | 'Ward' | 'ED_Obs' | 'OR';
export type Trajectory = 'improving' | 'stable' | 'deteriorating' | 'critical';
export type ActionType = 'escalate' | 'observe' | 'delay' | 'transfer' | 'admit';

export interface VitalSigns {
  heart_rate: number;
  blood_pressure_systolic: number;
  blood_pressure_diastolic: number;
  oxygen_saturation: number;
  respiratory_rate: number;
  temperature: number;
  glasgow_coma_scale: number;
  timestamp: string;
}

export interface LabResult {
  test_name: string;
  value: number;
  unit: string;
  reference_range: string;
  is_abnormal: boolean;
  timestamp: string;
}

export interface Patient {
  patient_id: string;
  name: string;
  age: number;
  gender: Gender;
  chief_complaint: string;
  arrival_time: string;
  current_location: LocationType;
  vitals: VitalSigns[];
  labs: LabResult[];
  medical_history: string[];
}

export interface RiskAssessment {
  patient_id: string;
  risk_score: number; // 0-100
  trajectory: Trajectory;
  confidence: number; // 0-1
  contributing_factors: string[];
  timestamp?: string;
}

export interface UnitCapacity {
  unit: LocationType;
  total_beds: number;
  occupied_beds: number;
  available_beds: number;
  occupancy_rate: number; // 0-1
  staff_on_duty: number;
  patients_per_nurse: number;
  capacity_score: number; // 0-100
}

export interface Decision {
  decision_id: string;
  patient_id: string;
  patient_name?: string;
  agent_name: string;
  action: ActionType;
  confidence: number;
  reasoning: string;
  timestamp: string;
}

export interface MCDAScores {
  safety_score: number;
  urgency_score: number;
  capacity_score: number;
  impact_score: number;
  weighted_total: number;
}

export interface AgentStatus {
  agent_name: string;
  is_active: boolean;
  is_registered: boolean;
  last_decision_time?: string;
  decision_count: number;
}

export interface SimulationStatus {
  is_running: boolean;
  current_time: string;
  speed: number;
  scenario: string;
  event_count: number;
}

export interface HospitalState {
  patients: Patient[];
  capacity: UnitCapacity[];
  decisions: Decision[];
}

// WebSocket event types
export type WebSocketEventType =
  | 'patient.arrival'
  | 'vitals.update'
  | 'risk_monitor.risk_calculated'
  | 'capacity_intelligence.capacity_updated'
  | 'escalation_decision.decision_made'
  | 'simulation.tick';

export interface WebSocketEvent {
  type: WebSocketEventType;
  data: unknown;
}

// Patient with computed risk data for display
export interface PatientWithRisk extends Patient {
  risk_assessment?: RiskAssessment;
}

// API response types
export interface SystemInfo {
  name: string;
  version: string;
  status: string;
  agents: string[];
}

export interface HealthCheck {
  status: string;
  database: string;
  agents: Record<string, boolean>;
}
