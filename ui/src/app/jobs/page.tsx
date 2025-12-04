'use client'

import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Chip,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material'
import { DataGrid, GridColDef } from '@mui/x-data-grid'
import { Refresh, PlayArrow } from '@mui/icons-material'
import Link from 'next/link'
import { api } from '@/lib/api'

interface Job {
  job_id: string
  pipeline_name: string
  status: string
  started_at: string | null
  completed_at: string | null
  total_records: number
  error_message: string | null
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchJobs = async () => {
    setLoading(true)
    try {
      const data = await api.getJobs()
      setJobs(data)
      setError(null)
    } catch (err) {
      setError('Failed to fetch jobs')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJobs()
    const interval = setInterval(fetchJobs, 30000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'success'
      case 'failed':
        return 'error'
      case 'running':
        return 'info'
      case 'pending':
        return 'warning'
      default:
        return 'default'
    }
  }

  const columns: GridColDef[] = [
    {
      field: 'job_id',
      headerName: 'Job ID',
      width: 200,
      renderCell: (params) => (
        <Link href={`/jobs/${params.value}`} style={{ color: '#1976d2' }}>
          {params.value}
        </Link>
      ),
    },
    {
      field: 'pipeline_name',
      headerName: 'Pipeline',
      width: 150,
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={getStatusColor(params.value) as any}
          size="small"
        />
      ),
    },
    {
      field: 'started_at',
      headerName: 'Started',
      width: 180,
      valueFormatter: (params) =>
        params.value ? new Date(params.value).toLocaleString() : '-',
    },
    {
      field: 'completed_at',
      headerName: 'Completed',
      width: 180,
      valueFormatter: (params) =>
        params.value ? new Date(params.value).toLocaleString() : '-',
    },
    {
      field: 'total_records',
      headerName: 'Records',
      width: 100,
      type: 'number',
    },
    {
      field: 'error_message',
      headerName: 'Error',
      flex: 1,
      renderCell: (params) =>
        params.value ? (
          <Typography color="error" variant="body2" noWrap>
            {params.value}
          </Typography>
        ) : null,
    },
  ]

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Jobs</Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchJobs}
            sx={{ mr: 2 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            onClick={async () => {
              await api.triggerJob({})
              fetchJobs()
            }}
          >
            Trigger ETL
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ height: 600 }}>
        <DataGrid
          rows={jobs}
          columns={columns}
          getRowId={(row) => row.job_id}
          loading={loading}
          pageSizeOptions={[25, 50, 100]}
          initialState={{
            pagination: { paginationModel: { pageSize: 25 } },
            sorting: { sortModel: [{ field: 'started_at', sort: 'desc' }] },
          }}
        />
      </Paper>
    </Box>
  )
}
