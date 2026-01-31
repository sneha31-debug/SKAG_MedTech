import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useAgentsStatus() {
  return useQuery({
    queryKey: ['agents-status'],
    queryFn: () => api.getAgentsStatus(),
    refetchInterval: 5000,
  });
}

export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 10000,
  });
}
