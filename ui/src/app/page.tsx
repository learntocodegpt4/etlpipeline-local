'use client';

import { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Schedule as PendingIcon,
  PlayArrow as RunningIcon,
} from '@mui/icons-material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useJobStats, useJobs } from '@/lib/api';
import { useSnackbar } from '@/context/SnackbarContext';
import { useLoader } from '@/context/LoaderContext';

const COLORS = ['#4caf50', '#f44336', '#ff9800', '#2196f3'];

export default function DashboardPage() {
  const { stats, isLoading: statsLoading, error: statsError } = useJobStats();
  const { jobs, isLoading: jobsLoading, error: jobsError } = useJobs(1, 5);
  const { showSnackbar } = useSnackbar();
  const { setIsLoading } = useLoader();

  const isLoading = statsLoading || jobsLoading;
  const error = statsError || jobsError;

  useEffect(() => {
    setIsLoading(isLoading);
  }, [isLoading, setIsLoading]);

  useEffect(() => {
    if (error) {
      showSnackbar(`Failed to load dashboard: ${error.message}`, 'error');
    }
  }, [error, showSnackbar]);

  useEffect(() => {
    if (stats && !statsLoading && !statsError) {
      showSnackbar('Dashboard data loaded successfully', 'success', 3000);
    }
  }, [stats, statsLoading, statsError, showSnackbar]);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load dashboard data: {error.message}
      </Alert>
    );
  }

  const statusData = stats?.by_status
    ? Object.entries(stats.by_status).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value,
      }))
    : [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Jobs
                  </Typography>
                  <Typography variant="h4">{stats?.total || 0}</Typography>
                </Box>
                <PendingIcon sx={{ fontSize: 48, color: 'primary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Completed
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {stats?.by_status?.completed || 0}
                  </Typography>
                </Box>
                <SuccessIcon sx={{ fontSize: 48, color: 'success.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Failed
                  </Typography>
                  <Typography variant="h4" color="error.main">
                    {stats?.by_status?.failed || 0}
                  </Typography>
                </Box>
                <ErrorIcon sx={{ fontSize: 48, color: 'error.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Records Processed
                  </Typography>
                  <Typography variant="h4">
                    {stats?.total_records?.toLocaleString() || 0}
                  </Typography>
                </Box>
                <RunningIcon sx={{ fontSize: 48, color: 'info.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Job Status
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={jobs?.jobs || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="job_id" tick={false} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="total_records_processed" fill="#2196f3" name="Records" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Job Status Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                  label
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Recent Jobs */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Recent Jobs
        </Typography>
        <Grid container spacing={2}>
          {jobs?.jobs?.slice(0, 5).map((job: any) => (
            <Grid item xs={12} key={job.job_id}>
              <Box
                sx={{
                  p: 2,
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 1,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    {job.job_id}
                  </Typography>
                  <Typography>
                    Started: {new Date(job.start_time).toLocaleString()}
                  </Typography>
                </Box>
                <Box textAlign="right">
                  <Typography
                    color={
                      job.status === 'completed'
                        ? 'success.main'
                        : job.status === 'failed'
                        ? 'error.main'
                        : 'warning.main'
                    }
                  >
                    {job.status.toUpperCase()}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {job.total_records_processed} records
                  </Typography>
                </Box>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Paper>
    </Box>
  );
}
