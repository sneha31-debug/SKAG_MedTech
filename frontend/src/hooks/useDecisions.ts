import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Decision } from '@/types/hospital';

export function useDecisions(limit: number = 50) {
  return useQuery({
    queryKey: ['decisions', limit],
    queryFn: () => api.getLatestDecisions(limit),
    refetchInterval: 5000,
  });
}

export function useAllDecisions() {
  return useQuery({
    queryKey: ['all-decisions'],
    queryFn: () => api.getDecisions(),
  });
}

export function useDecisionUpdates() {
  const queryClient = useQueryClient();

  const addDecision = (decision: Decision) => {
    queryClient.setQueryData<Decision[]>(['decisions', 50], (old = []) => {
      return [decision, ...old].slice(0, 50);
    });
  };

  const invalidateDecisions = () => {
    queryClient.invalidateQueries({ queryKey: ['decisions'] });
  };

  return {
    addDecision,
    invalidateDecisions,
  };
}
