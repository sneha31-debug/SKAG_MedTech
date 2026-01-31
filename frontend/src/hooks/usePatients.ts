import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Patient, RiskAssessment, PatientWithRisk, VitalSigns } from '@/types/hospital';

export function usePatients() {
  return useQuery({
    queryKey: ['patients'],
    queryFn: () => api.getPatients(),
    refetchInterval: 10000, // Refetch every 10 seconds as fallback
  });
}

export function usePatient(id: string | null) {
  return useQuery({
    queryKey: ['patient', id],
    queryFn: () => api.getPatient(id!),
    enabled: !!id,
  });
}

export function usePatientVitals(id: string | null) {
  return useQuery({
    queryKey: ['patient-vitals', id],
    queryFn: () => api.getPatientVitals(id!),
    enabled: !!id,
    refetchInterval: 5000, // Vitals update frequently
  });
}

export function usePatientRisk(id: string | null) {
  return useQuery({
    queryKey: ['patient-risk', id],
    queryFn: () => api.getPatientRisk(id!),
    enabled: !!id,
  });
}

// Hook to invalidate patient data when WebSocket events arrive
export function usePatientUpdates() {
  const queryClient = useQueryClient();

  const invalidatePatients = () => {
    queryClient.invalidateQueries({ queryKey: ['patients'] });
  };

  const invalidatePatient = (patientId: string) => {
    queryClient.invalidateQueries({ queryKey: ['patient', patientId] });
    queryClient.invalidateQueries({ queryKey: ['patient-vitals', patientId] });
    queryClient.invalidateQueries({ queryKey: ['patient-risk', patientId] });
  };

  const updatePatientRisk = (patientId: string, risk: RiskAssessment) => {
    queryClient.setQueryData(['patient-risk', patientId], risk);
  };

  return {
    invalidatePatients,
    invalidatePatient,
    updatePatientRisk,
  };
}

// Combine patients with their risk assessments
export function usePatientsWithRisk(): {
  data: PatientWithRisk[] | undefined;
  isLoading: boolean;
  error: Error | null;
} {
  const patientsQuery = usePatients();
  
  // For now, we'll return patients without individual risk queries
  // Risk data will be updated via WebSocket events
  return {
    data: patientsQuery.data,
    isLoading: patientsQuery.isLoading,
    error: patientsQuery.error,
  };
}
