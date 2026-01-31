import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { toast } from '@/hooks/use-toast';

export function useSimulationStatus() {
  return useQuery({
    queryKey: ['simulation-status'],
    queryFn: () => api.getSimulationStatus(),
    refetchInterval: 2000,
  });
}

export function useStartSimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ scenario, speed }: { scenario?: string; speed?: number } = {}) =>
      api.startSimulation(scenario, speed),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulation-status'] });
      toast({
        title: 'Simulation Started',
        description: 'The simulation is now running.',
      });
    },
    onError: (error) => {
      toast({
        title: 'Failed to Start Simulation',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
}

export function useStopSimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.stopSimulation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulation-status'] });
      toast({
        title: 'Simulation Stopped',
        description: 'The simulation has been paused.',
      });
    },
    onError: (error) => {
      toast({
        title: 'Failed to Stop Simulation',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
}

export function useResetSimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.resetSimulation(),
    onSuccess: () => {
      // Invalidate all data queries on reset
      queryClient.invalidateQueries({ queryKey: ['simulation-status'] });
      queryClient.invalidateQueries({ queryKey: ['patients'] });
      queryClient.invalidateQueries({ queryKey: ['decisions'] });
      queryClient.invalidateQueries({ queryKey: ['capacity'] });
      toast({
        title: 'Simulation Reset',
        description: 'All data has been reset to initial state.',
      });
    },
    onError: (error) => {
      toast({
        title: 'Failed to Reset Simulation',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
}
