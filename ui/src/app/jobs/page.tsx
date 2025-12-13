'use client';

import { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Alert,
  Chip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
} from '@mui/material';
import { DataGrid, GridColDef, GridPaginationModel } from '@mui/x-data-grid';
import { Refresh, PlayArrow } from '@mui/icons-material';
import { useJobs, triggerJob } from '@/lib/api';

const statusColors: Record<string, 'success' | 'error' | 'warning' | 'info' | 'default'> = {
  completed: 'success',
  failed: 'error',
  running: 'info',
  pending: 'warning',
};

export default function JobsPage() {
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 20,
  });
  const [triggerDialogOpen, setTriggerDialogOpen] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [triggerError, setTriggerError] = useState<string | null>(null);

  const { jobs, total, isLoading, error, mutate: refreshJobs } = useJobs(
    paginationModel.page + 1,
    paginationModel.pageSize
  );

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: 'Name',
      width: 300,
      renderCell: (params) => (
        <Typography sx={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'job_id',
      headerName: 'Job ID',
      width: 300,
      renderCell: (params) => (
        <Typography
          component="a"
          href={`/jobs/${params.value}`}
          sx={{ textDecoration: 'none', color: 'primary.main' }}
        >
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={statusColors[params.value] || 'default'}
          size="small"
        />
      ),
    },
    {
      field: 'start_time',
      headerName: 'Start Time',
      width: 200,
      valueFormatter: (params) =>
        params.value ? new Date(params.value).toLocaleString() : '-',
    },
    {
      field: 'end_time',
      headerName: 'End Time',
      width: 200,
      valueFormatter: (params) =>
        params.value ? new Date(params.value).toLocaleString() : '-',
    },
    {
      field: 'duration_seconds',
      headerName: 'Duration',
      width: 120,
      valueFormatter: (params) =>
        params.value ? `${params.value.toFixed(2)}s` : '-',
    },
    {
      field: 'total_records_processed',
      headerName: 'Records',
      width: 100,
      type: 'number',
    },
    {
      field: 'error_count',
      headerName: 'Errors',
      width: 80,
      type: 'number',
      renderCell: (params) => (
        <Typography color={params.value > 0 ? 'error' : 'textPrimary'}>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 160,
      sortable: false,
      renderCell: (params) => (
        <Box>
          <Button
            size="small"
            color="error"
            onClick={async () => {
              if (!confirm('Delete job ' + params.row.job_id + '?')) return;
              await fetch((process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8081') + '/jobs/' + params.row.job_id, { method: 'DELETE' });
              refreshJobs();
            }}
          >
            Delete
          </Button>
        </Box>
      ),
    },
  ];

  const handleTrigger = async () => {
    setTriggering(true);
    setTriggerError(null);
    try {
      await triggerJob();
      setTriggerDialogOpen(false);
      refreshJobs();
    } catch (err: any) {
      setTriggerError(err.message || 'Failed to trigger job');
    } finally {
      setTriggering(false);
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">ETL Jobs</Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => refreshJobs()}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            onClick={() => setTriggerDialogOpen(true)}
            sx={{ mr: 1 }}
          >
            Trigger Job
          </Button>
          <Button
            variant="outlined"
            color="warning"
            onClick={async () => {
              // Cleanup pending jobs
              const res = await fetch((process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8081') + '/jobs/cleanup_pending', { method: 'POST' });
              if (res.ok) refreshJobs();
            }}
          >
            Cleanup Pending
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load jobs: {error.message}
        </Alert>
      )}

      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={jobs || []}
          columns={columns}
          rowCount={total || 0}
          loading={isLoading}
          pageSizeOptions={[10, 20, 50]}
          paginationModel={paginationModel}
          paginationMode="server"
          onPaginationModelChange={setPaginationModel}
          getRowId={(row) => row.job_id}
          disableRowSelectionOnClick
        />
      </Paper>

      {/* Trigger Confirmation Dialog */}
      <Dialog open={triggerDialogOpen} onClose={() => setTriggerDialogOpen(false)}>
        <DialogTitle>Trigger ETL Pipeline</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to manually trigger the ETL pipeline? This will extract
            data from the FWC API and load it into the database.
          </DialogContentText>
          {triggerError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {triggerError}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTriggerDialogOpen(false)} disabled={triggering}>
            Cancel
          </Button>
          <Button
            onClick={handleTrigger}
            variant="contained"
            disabled={triggering}
            startIcon={triggering ? <CircularProgress size={20} /> : <PlayArrow />}
          >
            {triggering ? 'Triggering...' : 'Trigger'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
