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
import { useCalculatedPayRates, usePayRateStatistics, calculatePayRates } from '@/lib/api';
import { useSnackbar } from '@/context/SnackbarContext';
import { useLoader } from '@/context/LoaderContext';

export default function CalculatedPayRatesTab() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(50);

  const [awardCode, setAwardCode] = useState('');
  const [classificationFixedId, setClassificationFixedId] = useState('');
  const [employmentType, setEmploymentType] = useState('');
  const [dayType, setDayType] = useState('');
  const [shiftType, setShiftType] = useState('');
  const [employeeAgeCategory, setEmployeeAgeCategory] = useState('');
  const { showSnackbar } = useSnackbar();
  const { setIsLoading } = useLoader();

  const { payRates, isLoading, error, mutate } = useCalculatedPayRates(
    awardCode || undefined,
    classificationFixedId ? Number(classificationFixedId) : undefined,
    employmentType || undefined,
    dayType || undefined,
    shiftType || undefined,
    employeeAgeCategory || undefined,
    page + 1,
    pageSize
  );

  useEffect(() => {
    setIsLoading(isLoading);
  }, [isLoading, setIsLoading]);

  useEffect(() => {
    if (error) {
      showSnackbar(`Failed to load pay rates: ${error.message}`, 'error');
    }
  }, [error, showSnackbar]);

  useEffect(() => {
    if (payRates && payRates.length > 0 && !isLoading && !error) {
      showSnackbar(`Loaded ${payRates.length} pay rates`, 'success', 2000);
    }
  }, [payRates, isLoading, error, showSnackbar]);

  const { statistics: payRateStats, mutate: mutateStats } = usePayRateStatistics(awardCode || undefined);

  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'awardCode', headerName: 'Award Code', width: 120 },
      { field: 'awardName', headerName: 'Award Name', width: 260 },
      { field: 'classificationName', headerName: 'Classification', width: 200 },
      { field: 'classificationLevel', headerName: 'Level', width: 90 },
      { field: 'employmentType', headerName: 'Employment', width: 130 },
      { field: 'employeeAgeCategory', headerName: 'Age Category', width: 130 },
      { field: 'employeeCategory', headerName: 'Category', width: 140 },
      { field: 'dayType', headerName: 'Day Type', width: 130 },
      { field: 'shiftType', headerName: 'Shift Type', width: 140 },
      { field: 'timeRange', headerName: 'Time Range', width: 150 },
      { field: 'baseRateType', headerName: 'Base Rate Type', width: 140 },
      {
        field: 'baseRate',
        headerName: 'Base Rate',
        width: 120,
        valueFormatter: (params) =>
          params.value !== undefined && params.value !== null
            ? `$${Number(params.value).toFixed(2)}`
            : 'N/A',
      },
      {
        field: 'casualLoadedRate',
        headerName: 'Casual Loaded Rate',
        width: 170,
        valueFormatter: (params) =>
          params.value !== undefined && params.value !== null
            ? `$${Number(params.value).toFixed(2)}`
            : 'N/A',
      },
      {
        field: 'juniorAdjustedRate',
        headerName: 'Junior Adj. Rate',
        width: 160,
        valueFormatter: (params) =>
          params.value !== undefined && params.value !== null
            ? `$${Number(params.value).toFixed(2)}`
            : 'N/A',
      },
      {
        field: 'apprenticeAdjustedRate',
        headerName: 'Apprentice Adj. Rate',
        width: 180,
        valueFormatter: (params) =>
          params.value !== undefined && params.value !== null
            ? `$${Number(params.value).toFixed(2)}`
            : 'N/A',
      },
      { field: 'penaltyType', headerName: 'Penalty Type', width: 150 },
      {
        field: 'penaltyMultiplierApplied',
        headerName: 'Penalty Multiplier',
        width: 160,
      },
      {
        field: 'penaltyFlatAmountApplied',
        headerName: 'Penalty Flat',
        width: 140,
        valueFormatter: (params) =>
          params.value !== undefined && params.value !== null
            ? `$${Number(params.value).toFixed(2)}`
            : 'N/A',
      },
      {
        field: 'calculatedHourlyRate',
        headerName: 'Calculated Rate',
        width: 150,
        valueFormatter: (params) =>
          params.value !== undefined && params.value !== null
            ? `$${Number(params.value).toFixed(2)}`
            : 'N/A',
      },
      { field: 'calculatedRateDescription', headerName: 'Description', width: 260 },
      {
        field: 'applicableAllowanceTotal',
        headerName: 'Allowance Total',
        width: 150,
        valueFormatter: (params) =>
          params.value !== undefined && params.value !== null
            ? `$${Number(params.value).toFixed(2)}`
            : 'N/A',
      },
      {
        field: 'effectiveFrom',
        headerName: 'Effective From',
        width: 150,
        valueFormatter: (params) =>
          params.value ? new Date(params.value).toLocaleDateString() : 'N/A',
      },
      {
        field: 'effectiveTo',
        headerName: 'Effective To',
        width: 150,
        valueFormatter: (params) =>
          params.value ? new Date(params.value).toLocaleDateString() : 'Current',
      },
    ],
    []
  );

  const handleExport = () => {
    const csv = [
      columns.map((col) => col.headerName).join(','),
      ...payRates.map((row: any) => columns.map((col) => row[col.field] ?? '').join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `calculated-pay-rates-${Date.now()}.csv`;
    a.click();
  };

  const handleCalculate = async () => {
    try {
      await calculatePayRates(
        awardCode || undefined,
        classificationFixedId ? Number(classificationFixedId) : undefined
      );
      mutate();
      mutateStats?.();
      showSnackbar('Pay rates calculated successfully', 'success');
    } catch (e: any) {
      showSnackbar(e.message || 'Failed to calculate pay rates', 'error');
    }
  };

  const totalRateCount = payRates.length;

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Calculated Pay Rates
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            View calculated pay rates with filters for award, classification, employment, day type, shift, and age category.
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
                label="Classification Fixed Id"
                variant="outlined"
                size="small"
                value={classificationFixedId}
                onChange={(e) => {
                  setClassificationFixedId(e.target.value);
                  setPage(0);
                }}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                label="Employment Type"
                placeholder="FULL_TIME / PART_TIME / CASUAL"
                variant="outlined"
                size="small"
                value={employmentType}
                onChange={(e) => {
                  setEmploymentType(e.target.value);
                  setPage(0);
                }}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                label="Day Type"
                placeholder="WEEKDAY / SATURDAY / SUNDAY / PUBLIC_HOLIDAY"
                variant="outlined"
                size="small"
                value={dayType}
                onChange={(e) => {
                  setDayType(e.target.value);
                  setPage(0);
                }}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                label="Shift Type"
                placeholder="STANDARD / NIGHT / AFTERNOON / OVERTIME_FIRST2HR"
                variant="outlined"
                size="small"
                value={shiftType}
                onChange={(e) => {
                  setShiftType(e.target.value);
                  setPage(0);
                }}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                label="Employee Age Category"
                placeholder="ADULT / AGE_20 / AGE_19 / AGE_18"
                variant="outlined"
                size="small"
                value={employeeAgeCategory}
                onChange={(e) => {
                  setEmployeeAgeCategory(e.target.value);
                  setPage(0);
                }}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={12} md={12}>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <Button
                  variant="outlined"
                  startIcon={<Refresh />}
                  onClick={() => mutate()}
                >
                  Refresh
                </Button>
                <Button
                  variant="contained"
                  color="secondary"
                  startIcon={<PlayArrow />}
                  onClick={handleCalculate}
                  disabled={!awardCode}
                  title="Run calculation to (re)compute rates for this award"
                >
                  Calculate Pay Rates
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Download />}
                  onClick={handleExport}
                  disabled={payRates.length === 0}
                >
                  Export CSV
                </Button>
                <Chip label={`Records: ${totalRateCount}`} color="primary" variant="outlined" />
                {payRateStats?.TotalRates !== undefined && (
                  <Chip label={`Total Rates: ${payRateStats.TotalRates}`} variant="outlined" />
                )}
              </Box>
            </Grid>
          </Grid>

          {error && (
            <Alert severity="error" sx={{ mt: 1 }}>
              Error loading calculated pay rates: {error.message}
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
                rows={payRates.map((row: any) => ({ ...row, id: row.id }))}
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
