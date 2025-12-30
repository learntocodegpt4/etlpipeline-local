'use client';

import { useState, useEffect } from 'react';
import { Box, Card, CardContent, Typography, Grid, TextField, Chip, Alert, CircularProgress } from '@mui/material';
import { useRuleEnginePenaltyStatistics } from '@/lib/api';
import { useSnackbar } from '@/context/SnackbarContext';
import { useLoader } from '@/context/LoaderContext';

export default function PenaltiesStatisticsTab() {
  const [awardCode, setAwardCode] = useState('');
  const { statistics, isLoading, error } = useRuleEnginePenaltyStatistics(awardCode || undefined);
  const { showSnackbar } = useSnackbar();
  const { setIsLoading } = useLoader();

  useEffect(() => {
    setIsLoading(isLoading);
  }, [isLoading, setIsLoading]);

  useEffect(() => {
    if (error) {
      showSnackbar(`Failed to load penalties statistics: ${error.message}`, 'error');
    }
  }, [error, showSnackbar]);

  useEffect(() => {
    if (statistics && !isLoading && !error) {
      showSnackbar(`Loaded penalties statistics for ${awardCode}`, 'success', 2000);
    }
  }, [statistics, isLoading, error, awardCode, showSnackbar]);

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Penalties Statistics
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            This view summarizes penalties for a given award using the statistics endpoint. Enter an award code to see totals and pagination info.
          </Typography>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                label="Award Code"
                variant="outlined"
                size="small"
                value={awardCode}
                onChange={(e) => setAwardCode(e.target.value)}
                fullWidth
              />
            </Grid>
          </Grid>

          {error && (
            <Alert severity="error" sx={{ mt: 1 }}>
              Error fetching statistics: {error.message}
            </Alert>
          )}

          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            statistics && (
              <Grid container spacing={2}>
                <Grid item>
                  <Chip label={`Award: ${statistics.awardCode ?? 'N/A'}`} variant="outlined" />
                </Grid>
                <Grid item>
                  <Chip label={`Total Penalties: ${statistics.totalPenalties ?? 0}`} color="primary" variant="outlined" />
                </Grid>
                <Grid item>
                  <Chip label={`Total Pages: ${statistics.totalPages ?? 0}`} variant="outlined" />
                </Grid>
              </Grid>
            )
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            How these statistics apply
          </Typography>
          <Typography variant="body2" color="text.secondary">
            The statistics endpoint reports the total number of penalty records available for the selected award and the total pages based on server-side pagination. Use this to gauge dataset size and navigate pages in the Penalties tab for detailed entries.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}