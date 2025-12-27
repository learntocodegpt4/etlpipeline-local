'use client';

import { useMemo, useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Download, Refresh, PlayArrow } from '@mui/icons-material';
import { useRuleEnginePenalties, useRuleEnginePenaltyStatistics, usePayRateStatistics, calculatePayRates } from '@/lib/api';
import { useSnackbar } from '@/context/SnackbarContext';
import { useLoader } from '@/context/LoaderContext';

export default function PenaltiesTab() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(50);

  const [awardCode, setAwardCode] = useState('');
  const [classificationLevel, setClassificationLevel] = useState('');
  const [penaltyType, setPenaltyType] = useState('');
  const { showSnackbar } = useSnackbar();
  const { setIsLoading } = useLoader();

  const { penalties, totalCount, isLoading, error, mutate } = useRuleEnginePenalties(
    awardCode || undefined,
    classificationLevel ? Number(classificationLevel) : undefined,
    page + 1,
    pageSize,
    penaltyType || undefined
  );

  useEffect(() => {
    setIsLoading(isLoading);
  }, [isLoading, setIsLoading]);

  useEffect(() => {
    if (error) {
      showSnackbar(`Failed to load penalties: ${error.message}`, 'error');
    }
  }, [error, showSnackbar]);

  useEffect(() => {
    if (penalties && penalties.length > 0 && !isLoading && !error) {
      showSnackbar(`Loaded ${penalties.length} penalties`, 'success', 2000);
    }
  }, [penalties, isLoading, error, showSnackbar]);

  const { statistics: penaltyStats } = useRuleEnginePenaltyStatistics(awardCode || undefined);
  const { statistics: payRateStats } = usePayRateStatistics(awardCode || undefined);

  const filteredPenalties = useMemo(() => {
    return (penalties || []).filter((p: any) =>
      (!penaltyType || (p.penaltyType || '').toLowerCase().includes(penaltyType.toLowerCase()))
    );
  }, [penalties, penaltyType]);

  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'awardCode', headerName: 'Award Code', width: 120 },
      { field: 'penaltyDescription', headerName: 'Description', width: 300 },
      { field: 'penaltyType', headerName: 'Type', width: 160 },
      { field: 'classificationLevel', headerName: 'Level', width: 90 },
      { field: 'applicableDay', headerName: 'Applicable Day', width: 140 },
      {
        field: 'rate',
        headerName: 'Rate',
        width: 120,
        valueFormatter: (params) =>
          params.value !== undefined && params.value !== null
            ? Number(params.value).toFixed(2)
            : 'N/A',
      },
      {
        field: 'penaltyCalculatedValue',
        headerName: 'Calculated Value',
        width: 150,
        valueFormatter: (params) =>
          params.value !== undefined && params.value !== null
            ? Number(params.value).toFixed(2)
            : 'N/A',
      },
      { field: 'clauseFixedId', headerName: 'Clause Id', width: 120 },
      { field: 'clauseDescription', headerName: 'Clause Description', width: 240 },
      { field: 'basePayRateId', headerName: 'Base Pay Rate Id', width: 160 },
      {
        field: 'operativeFrom',
        headerName: 'Operative From',
        width: 150,
        valueFormatter: (params) =>
          params.value ? new Date(params.value).toLocaleDateString() : 'N/A',
      },
      {
        field: 'operativeTo',
        headerName: 'Operative To',
        width: 150,
        valueFormatter: (params) =>
          params.value ? new Date(params.value).toLocaleDateString() : 'Current',
      },
      { field: 'versionNumber', headerName: 'Version', width: 100 },
      { field: 'publishedYear', headerName: 'Year', width: 100 },
    ],
    []
  );

  const handleExport = () => {
    const csv = [
      columns.map((col) => col.headerName).join(','),
      ...filteredPenalties.map((row: any) => columns.map((col) => row[col.field] ?? '').join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `penalties-${Date.now()}.csv`;
    a.click();
  };

  const handleCalculatePayRates = async () => {
    try {
      const result = await calculatePayRates(awardCode || undefined);
      // Re-fetch penalties and stats after calculation
      mutate();
    } catch (e: any) {
      alert(e.message || 'Failed to calculate pay rates');
    }
  };

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Penalties
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            View penalties by award and classification. Use filters to narrow results and export for analysis.
          </Typography>

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                label="Award Code"
                variant="outlined"
                size="small"
                value={awardCode}
                onChange={(e) => {
                  setAwardCode(e.target.value);
                  setPage(0);
                }}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                label="Classification Level"
                variant="outlined"
                size="small"
                value={classificationLevel}
                onChange={(e) => {
                  setClassificationLevel(e.target.value);
                  setPage(0);
                }}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                label="Penalty Type"
                variant="outlined"
                size="small"
                value={penaltyType}
                onChange={(e) => {
                  setPenaltyType(e.target.value);
                  setPage(0);
                }}
                fullWidth
              />
            </Grid>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <Button variant="outlined" startIcon={<Refresh />} onClick={() => mutate()}>
                  Refresh
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Download />}
                  onClick={handleExport}
                  disabled={filteredPenalties.length === 0}
                >
                  Export CSV
                </Button>
                <Button
                  variant="contained"
                  color="secondary"
                  startIcon={<PlayArrow />}
                  onClick={handleCalculatePayRates}
                  disabled={!awardCode}
                  title="Calculate pay rates to ensure penalty interactions are up to date"
                >
                  Calculate Pay Rates
                </Button>
                <Chip label={`Records: ${totalCount}`} color="primary" variant="outlined" />
                {penaltyStats?.TotalPenalties !== undefined && (
                  <Chip label={`Total Penalties: ${penaltyStats.TotalPenalties}`} variant="outlined" />
                )}
                {payRateStats?.TotalRates !== undefined && (
                  <Chip label={`Total Rates: ${payRateStats.TotalRates}`} variant="outlined" />
                )}
              </Box>
            </Grid>
          </Grid>

          {error && (
            <Alert severity="error" sx={{ mt: 1 }}>
              Error loading penalties: {error.message}
            </Alert>
          )}
        </CardContent>
      </Card>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Card>
          <CardContent>
            <Box sx={{ height: 650, width: '100%' }}>
              <DataGrid
                rows={filteredPenalties.map((row: any) => ({ ...row, id: row.id }))}
                columns={columns}
                pageSizeOptions={[25, 50, 100]}
                paginationModel={{ page, pageSize }}
                onPaginationModelChange={(model) => {
                  setPage(model.page);
                  setPageSize(model.pageSize);
                }}
                disableRowSelectionOnClick
              />
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
