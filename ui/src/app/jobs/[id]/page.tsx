'use client';

import { useParams } from 'next/navigation';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
} from '@mui/material';
import { useJob } from '@/lib/api';

const statusColors: Record<string, 'success' | 'error' | 'warning' | 'info' | 'default'> = {
  completed: 'success',
  failed: 'error',
  running: 'info',
  pending: 'warning',
  skipped: 'default',
};

export default function JobDetailPage() {
  const params = useParams();
  const jobId = params.id as string;
  const { job, isLoading, error } = useJob(jobId);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load job details: {error.message}
      </Alert>
    );
  }

  if (!job) {
    return <Alert severity="warning">Job not found</Alert>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Job Details
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography color="textSecondary" gutterBottom>
              Job ID
            </Typography>
            <Typography variant="h6" sx={{ wordBreak: 'break-all' }}>
              {job.job_id}
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography color="textSecondary" gutterBottom>
              Status
            </Typography>
            <Chip
              label={job.status}
              color={statusColors[job.status] || 'default'}
              size="medium"
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <Typography color="textSecondary" gutterBottom>
              Start Time
            </Typography>
            <Typography>
              {job.start_time ? new Date(job.start_time).toLocaleString() : '-'}
            </Typography>
          </Grid>

          <Grid item xs={12} md={4}>
            <Typography color="textSecondary" gutterBottom>
              End Time
            </Typography>
            <Typography>
              {job.end_time ? new Date(job.end_time).toLocaleString() : '-'}
            </Typography>
          </Grid>

          <Grid item xs={12} md={4}>
            <Typography color="textSecondary" gutterBottom>
              Duration
            </Typography>
            <Typography>
              {job.duration_seconds ? `${job.duration_seconds.toFixed(2)} seconds` : '-'}
            </Typography>
          </Grid>

          <Grid item xs={12} md={4}>
            <Typography color="textSecondary" gutterBottom>
              Records Processed
            </Typography>
            <Typography variant="h5" color="primary">
              {job.total_records_processed?.toLocaleString() || 0}
            </Typography>
          </Grid>

          <Grid item xs={12} md={4}>
            <Typography color="textSecondary" gutterBottom>
              Errors
            </Typography>
            <Typography variant="h5" color={job.error_count > 0 ? 'error' : 'textPrimary'}>
              {job.error_count || 0}
            </Typography>
          </Grid>

          <Grid item xs={12} md={4}>
            <Typography color="textSecondary" gutterBottom>
              Warnings
            </Typography>
            <Typography variant="h5" color={job.warning_count > 0 ? 'warning.main' : 'textPrimary'}>
              {job.warning_count || 0}
            </Typography>
          </Grid>

          {job.error_message && (
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography color="textSecondary" gutterBottom>
                Error Message
              </Typography>
              <Paper
                variant="outlined"
                sx={{
                  p: 2,
                  bgcolor: 'error.light',
                  color: 'error.contrastText',
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                }}
              >
                {job.error_message}
              </Paper>
            </Grid>
          )}
        </Grid>
      </Paper>

      {/* Job Steps */}
      {job.steps && job.steps.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Pipeline Steps
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Step</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell align="right">Records</TableCell>
                  <TableCell align="right">Failed</TableCell>
                  <TableCell>Error</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {job.steps.map((step: any, index: number) => (
                  <TableRow key={index}>
                    <TableCell>{step.step_name}</TableCell>
                    <TableCell>
                      <Chip
                        label={step.status}
                        color={statusColors[step.status] || 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {step.duration_seconds ? `${step.duration_seconds.toFixed(2)}s` : '-'}
                    </TableCell>
                    <TableCell align="right">{step.records_processed || 0}</TableCell>
                    <TableCell align="right">
                      <Typography color={step.records_failed > 0 ? 'error' : 'inherit'}>
                        {step.records_failed || 0}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {step.error_message ? (
                        <Typography
                          color="error"
                          sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}
                        >
                          {step.error_message}
                        </Typography>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}
    </Box>
  );
}
