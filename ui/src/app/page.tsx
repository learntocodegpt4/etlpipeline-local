'use client'

import { useState, useEffect } from 'react'
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material'
import {
  CheckCircle,
  Error,
  Schedule,
  PlayArrow,
  TrendingUp,
} from '@mui/icons-material'
import { api } from '@/lib/api'

interface JobStats {
  total_jobs: number
  by_status: Record<string, number>
  jobs_last_24h: number
  avg_duration_seconds: number
  success_rate: number
}

interface HealthStatus {
  status: string
  timestamp: string
  version: string
  environment: string
  components: Record<string, any>
}

export default function Dashboard() {
  const [stats, setStats] = useState<JobStats | null>(null)
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [statsData, healthData] = await Promise.all([
        api.getJobStats(),
        api.getHealth(),
      ])
      setStats(statsData)
      setHealth(healthData)
      setError(null)
    } catch (err) {
      setError('Failed to fetch dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const handleTriggerETL = async () => {
    setTriggering(true)
    try {
      await api.triggerJob({})
      setError(null)
      fetchData()
    } catch (err) {
      setError('Failed to trigger ETL job')
    } finally {
      setTriggering(false)
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={triggering ? <CircularProgress size={20} color="inherit" /> : <PlayArrow />}
          onClick={handleTriggerETL}
          disabled={triggering}
        >
          {triggering ? 'Triggering...' : 'Run Full ETL'}
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Stats Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Schedule color="primary" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Total Jobs
                  </Typography>
                  <Typography variant="h4">
                    {stats?.total_jobs || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <CheckCircle color="success" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Successful
                  </Typography>
                  <Typography variant="h4">
                    {stats?.by_status?.success || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Error color="error" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Failed
                  </Typography>
                  <Typography variant="h4">
                    {stats?.by_status?.failed || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <TrendingUp color="info" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Success Rate
                  </Typography>
                  <Typography variant="h4">
                    {stats?.success_rate?.toFixed(1) || 0}%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* System Health */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              System Health
            </Typography>
            <Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Status</Typography>
                <Typography
                  color={health?.status === 'healthy' ? 'success.main' : 'error.main'}
                  fontWeight="bold"
                >
                  {health?.status?.toUpperCase()}
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Environment</Typography>
                <Typography>{health?.environment}</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Version</Typography>
                <Typography>{health?.version}</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Database</Typography>
                <Typography
                  color={health?.components?.database?.status === 'healthy' ? 'success.main' : 'error.main'}
                >
                  {health?.components?.database?.status?.toUpperCase()}
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Scheduler</Typography>
                <Typography
                  color={health?.components?.scheduler?.enabled ? 'success.main' : 'warning.main'}
                >
                  {health?.components?.scheduler?.enabled ? 'ENABLED' : 'DISABLED'}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Jobs (Last 24h)</Typography>
                <Typography fontWeight="bold">{stats?.jobs_last_24h || 0}</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Avg Duration</Typography>
                <Typography>
                  {stats?.avg_duration_seconds
                    ? `${Math.round(stats.avg_duration_seconds)}s`
                    : 'N/A'}
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Running</Typography>
                <Typography color="info.main" fontWeight="bold">
                  {stats?.by_status?.running || 0}
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography>Pending</Typography>
                <Typography color="warning.main" fontWeight="bold">
                  {stats?.by_status?.pending || 0}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
