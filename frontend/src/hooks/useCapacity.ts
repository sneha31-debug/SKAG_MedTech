import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { UnitCapacity, HospitalState } from '@/types/hospital';

export function useCapacity() {
  return useQuery({
    queryKey: ['capacity'],
    queryFn: () => api.getCapacity(),
    refetchInterval: 10000,
  });
}

export function useHospitalState() {
  return useQuery({
    queryKey: ['hospital-state'],
    queryFn: () => api.getHospitalState(),
    refetchInterval: 10000,
  });
}

export function useCapacityUpdates() {
  const queryClient = useQueryClient();

  const updateCapacity = (capacity: UnitCapacity[]) => {
    queryClient.setQueryData(['capacity'], capacity);
  };

  const invalidateCapacity = () => {
    queryClient.invalidateQueries({ queryKey: ['capacity'] });
  };

  return {
    updateCapacity,
    invalidateCapacity,
  };
}

// Helper to get capacity color based on occupancy rate
export function getCapacityColor(occupancyRate: number): 'available' | 'moderate' | 'critical' {
  if (occupancyRate < 0.5) return 'available';
  if (occupancyRate < 0.7) return 'moderate';
  return 'critical';
}

// Helper to get capacity score color
export function getCapacityScoreColor(score: number): 'available' | 'moderate' | 'critical' {
  if (score > 50) return 'available';
  if (score > 30) return 'moderate';
  return 'critical';
}
