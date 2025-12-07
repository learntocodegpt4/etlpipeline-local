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
  awardCode?: string
) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (awardCode) params.set('award_code', awardCode);

  const { data, error, isLoading } = useSWR(
    `${API_URL}/data/preview/${table}?${params}`,
    fetcher
  );

  return {
    data: data?.data,
    total: data?.total_count,
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

export { globalMutate as mutate };
