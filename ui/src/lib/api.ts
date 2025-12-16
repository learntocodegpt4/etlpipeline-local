import useSWR, { mutate as globalMutate } from 'swr';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8081/api';

const fetcher = async (url: string) => {
  const res = await fetch(url);
  if (!res.ok) {
    const error = new Error('An error occurred while fetching the data.');
    throw error;
  }
  return res.json();
};

// Jobs hooks
export function useJobs(page: number = 1, pageSize: number = 20, status?: string) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (status) params.set('status', status);

  const { data, error, isLoading, mutate } = useSWR(
    `${API_URL}/jobs?${params}`,
    fetcher
  );

  return {
    jobs: data?.jobs,
    total: data?.total,
    isLoading,
    error,
    mutate,
  };
}

export function useJob(jobId: string) {
  const { data, error, isLoading, mutate } = useSWR(
    jobId ? `${API_URL}/jobs/${jobId}` : null,
    fetcher
  );

  return {
    job: data,
    isLoading,
    error,
    mutate,
  };
}

export function useJobStats(days: number = 7) {
  const { data, error, isLoading } = useSWR(
    `${API_URL}/jobs/stats/summary?days=${days}`,
    fetcher
  );

  return {
    stats: data,
    isLoading,
    error,
  };
}

// Status hooks
export function useStatus() {
  const { data, error, isLoading, mutate } = useSWR(
    `${API_URL}/status`,
    fetcher,
    { refreshInterval: 30000 }
  );

  return {
    status: data,
    isLoading,
    error,
    mutate,
  };
}

export function useDetailedStatus() {
  const { data, error, isLoading, mutate } = useSWR(
    `${API_URL}/status/detailed`,
    fetcher,
    { refreshInterval: 30000 }
  );

  return {
    status: data,
    isLoading,
    error,
    mutate,
  };
}

// Data preview hooks
export function useTables() {
  const { data, error, isLoading } = useSWR(
    `${API_URL}/data/tables`,
    fetcher
  );

  return {
    tables: data?.tables,
    isLoading,
    error,
  };
}

export function useDataPreview(
  table: string,
  page: number = 1,
  pageSize: number = 50,
  filters?: Record<string, string | undefined>
) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  // Add dynamic filters - convert snake_case filter names to backend format
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value && value.trim()) {
        params.set(key, value);
      }
    });
  }

  const { data, error, isLoading } = useSWR(
    `${API_URL}/data/preview/${table}?${params}`,
    fetcher,
    { dedupingInterval: 1000 }
  );

  return {
    data: data?.data,
    total: data?.total,
    isLoading,
    error,
  };
}

// API functions
export async function triggerJob(awardCodes?: string[]) {
  const res = await fetch(`${API_URL}/jobs/trigger`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ award_codes: awardCodes }),
  });

  if (!res.ok) {
    throw new Error('Failed to trigger job');
  }

  return res.json();
}

export async function cleanupPendingJobs() {
  const res = await fetch(`${API_URL}/jobs/cleanup_pending`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to cleanup pending jobs');
  return res.json();
}

export async function deleteJob(jobId: string) {
  const res = await fetch(`${API_URL}/jobs/${jobId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete job');
  return res.json();
}

// Penalties hooks
export function usePenalties(
  awardCode?: string,
  classificationLevel?: number,
  penaltyType?: string,
  page: number = 1,
  pageSize: number = 100
) {
  const params = new URLSearchParams({
    page: page.toString(),
    pageSize: pageSize.toString(),
  });
  if (awardCode) params.set('awardCode', awardCode);
  if (classificationLevel) params.set('classificationLevel', classificationLevel.toString());
  if (penaltyType) params.set('penaltyType', penaltyType);

  const { data, error, isLoading, mutate } = useSWR(
    `http://localhost:5000/api/penalties?${params}`,
    fetcher,
    { dedupingInterval: 1000 }
  );

  return {
    penalties: data?.penalties || [],
    totalCount: data?.totalCount || 0,
    page: data?.page || 1,
    pageSize: data?.pageSize || 100,
    totalPages: data?.totalPages || 0,
    isLoading,
    error,
    mutate,
  };
}

export function usePenaltyStatistics(awardCode: string) {
  const { data, error, isLoading } = useSWR(
    awardCode ? `http://localhost:5000/api/penalties/statistics?awardCode=${awardCode}` : null,
    fetcher
  );

  return {
    statistics: data,
    isLoading,
    error,
  };
}

export { globalMutate as mutate };
