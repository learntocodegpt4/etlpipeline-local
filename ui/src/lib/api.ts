import useSWR, { mutate as globalMutate } from 'swr';

// Use relative URL to support both internet and intranet IPs through Nginx proxy
// Browser will automatically use the current host/IP accessed by user
const API_URL = process.env.NEXT_PUBLIC_API_URL || '/etlapi/api';

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

// Penalties hooks - using data preview endpoint for Stg_TblPenalties
export function usePenalties(
  awardCode?: string,
  classificationLevel?: number,
  penaltyType?: string,
  page: number = 1,
  pageSize: number = 100
) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (awardCode) params.set('award_code', awardCode);
  // Note: Python ETL API doesn't support classificationLevel and penaltyType filters yet
  // These can be added to data.py if needed

  const { data, error, isLoading, mutate } = useSWR(
    `${API_URL}/data/preview/Stg_TblPenalties?${params}`,
    fetcher,
    { dedupingInterval: 1000 }
  );

  return {
    penalties: data?.data || [],
    totalCount: data?.total || 0,
    page: data?.page || 1,
    pageSize: data?.page_size || 100,
    totalPages: Math.ceil((data?.total || 0) / (data?.page_size || 100)),
    isLoading,
    error,
    mutate,
  };
}

export function usePenaltyStatistics(awardCode: string) {
  // For statistics, we can fetch all penalties for the award (or first page)
  const params = new URLSearchParams({
    page: '1',
    page_size: '1',
  });
  if (awardCode) params.set('award_code', awardCode);

  const { data, error, isLoading } = useSWR(
    awardCode ? `${API_URL}/data/preview/Stg_TblPenalties?${params}` : null,
    fetcher
  );

  return {
    statistics: {
      totalPenalties: data?.total || 0,
      awardCode: awardCode,
    },
    isLoading,
    error,
  };
}

export { globalMutate as mutate };
