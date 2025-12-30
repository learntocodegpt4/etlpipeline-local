'use client';

import { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  TextField,
  CircularProgress,
  Alert,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Chip,
} from '@mui/material';
import { DataGrid, GridColDef, GridPaginationModel } from '@mui/x-data-grid';
import { usePenalties, usePenaltyStatistics } from '@/lib/api';
import RefreshIcon from '@mui/icons-material/Refresh';
import DownloadIcon from '@mui/icons-material/Download';

export default function PenaltiesPage() {
  const [awardCodeFilter, setAwardCodeFilter] = useState('MA000120');
  const [classificationLevelFilter, setClassificationLevelFilter] = useState<number | undefined>();
  const [penaltyTypeFilter, setPenaltyTypeFilter] = useState<string>('');
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 100,
  });

  const {
    penalties,
    totalCount,
    totalPages,
    isLoading: penaltiesLoading,
    error,
    mutate,
  } = usePenalties(
    awardCodeFilter || undefined,
    classificationLevelFilter,
    penaltyTypeFilter || undefined,
    paginationModel.page + 1,
    paginationModel.pageSize
  );

  const { statistics, isLoading: statsLoading } = usePenaltyStatistics(
    awardCodeFilter || ''
  );

  // Define DataGrid columns - using snake_case from database
  const columns: GridColDef[] = [
    {
      field: 'penalty_fixed_id',
      headerName: 'Penalty ID',
      width: 120,
    },
    {
      field: 'award_code',
      headerName: 'Award Code',
      width: 120,
    },
    {
      field: 'penalty_description',
      headerName: 'Description',
      flex: 2,
      minWidth: 300,
      renderCell: (params) => (
        <Typography sx={{ whiteSpace: 'normal', wordBreak: 'break-word', py: 1 }}>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'rate',
      headerName: 'Rate (%)',
      width: 100,
      renderCell: (params) =>
        params.value ? `${Number(params.value).toFixed(1)}%` : '-',
    },
    {
      field: 'penalty_calculated_value',
      headerName: 'Calculated Value',
      width: 150,
      renderCell: (params) =>
        params.value ? `$${Number(params.value).toFixed(2)}` : '-',
    },
    {
      field: 'classification_level',
      headerName: 'Classification Level',
      width: 150,
    },
    {
      field: 'clause_description',
      headerName: 'Clause',
      flex: 1,
      minWidth: 250,
      renderCell: (params) => (
        <Typography sx={{ whiteSpace: 'normal', wordBreak: 'break-word', py: 1 }}>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'base_pay_rate_id',
      headerName: 'Base Rate ID',
      width: 130,
    },
  ];

  const handleRefresh = () => {
    mutate();
  };

  const handleDownloadCSV = () => {
    if (!penalties || penalties.length === 0) return;

    const headers = [
      'Penalty ID',
      'Award Code',
      'Description',
      'Rate',
      'Calculated Value',
      'Classification',
      'Clause',
      'Base Pay Rate ID',
    ];
    const rows = penalties.map((p: any) => [
      p.penalty_fixed_id,
      p.award_code,
      p.penalty_description,
      p.rate,
      p.penalty_calculated_value,
      p.classification_level,
      p.clause_description,
      p.base_pay_rate_id,
    ]);

    const csv = [headers.join(',')]
      .concat(rows.map((r:any) => r.map((c:any) => `"${c || ''}"`).join(',')))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `penalties_${awardCodeFilter}_page${paginationModel.page + 1}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleResetFilters = () => {
    setAwardCodeFilter('MA000120');
    setClassificationLevelFilter(undefined);
    setPenaltyTypeFilter('');
    setPaginationModel({ page: 0, pageSize: 100 });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        FWC Penalties Management
      </Typography>

      {/* Statistics Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="textSecondary">
                Award Code
              </Typography>
              <Typography variant="h5">
                {awardCodeFilter || 'All Awards'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="textSecondary">
                Total Penalties
              </Typography>
              <Typography variant="h5">
                {statsLoading ? (
                  <CircularProgress size={24} />
                ) : (
                  statistics?.totalPenalties?.toLocaleString() || 0
                )}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="textSecondary">
                Current Page
              </Typography>
              <Typography variant="h5">
                {paginationModel.page + 1} / {totalPages || 1}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="textSecondary">
                Showing
              </Typography>
              <Typography variant="h5">
                {penalties?.length || 0} records
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Filters
        </Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="Award Code"
              value={awardCodeFilter}
              onChange={(e) => {
                setAwardCodeFilter(e.target.value);
                setPaginationModel({ ...paginationModel, page: 0 });
              }}
              placeholder="e.g., MA000120"
              size="small"
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Classification Level</InputLabel>
              <Select
                value={classificationLevelFilter || ''}
                label="Classification Level"
                onChange={(e) => {
                  const value = e.target.value;
                  setClassificationLevelFilter(value ? Number(value) : undefined);
                  setPaginationModel({ ...paginationModel, page: 0 });
                }}
              >
                <MenuItem value="">All Levels</MenuItem>
                <MenuItem value={1}>Level 1</MenuItem>
                <MenuItem value={2}>Level 2</MenuItem>
                <MenuItem value={3}>Level 3</MenuItem>
                <MenuItem value={4}>Level 4</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="Penalty Type"
              value={penaltyTypeFilter}
              onChange={(e) => {
                setPenaltyTypeFilter(e.target.value);
                setPaginationModel({ ...paginationModel, page: 0 });
              }}
              placeholder="e.g., Overtime"
              size="small"
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Stack direction="row" spacing={1}>
              <Button
                variant="outlined"
                onClick={handleResetFilters}
                fullWidth
              >
                Reset
              </Button>
              <Button
                variant="contained"
                onClick={handleRefresh}
                startIcon={<RefreshIcon />}
                fullWidth
              >
                Refresh
              </Button>
            </Stack>
          </Grid>
        </Grid>

        {/* Active Filters Chips */}
        {(awardCodeFilter || classificationLevelFilter || penaltyTypeFilter) && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="textSecondary" sx={{ mr: 1 }}>
              Active Filters:
            </Typography>
            {awardCodeFilter && (
              <Chip
                label={`Award: ${awardCodeFilter}`}
                size="small"
                onDelete={() => setAwardCodeFilter('')}
                sx={{ mr: 0.5, mb: 0.5 }}
              />
            )}
            {classificationLevelFilter && (
              <Chip
                label={`Level: ${classificationLevelFilter}`}
                size="small"
                onDelete={() => setClassificationLevelFilter(undefined)}
                sx={{ mr: 0.5, mb: 0.5 }}
              />
            )}
            {penaltyTypeFilter && (
              <Chip
                label={`Type: ${penaltyTypeFilter}`}
                size="small"
                onDelete={() => setPenaltyTypeFilter('')}
                sx={{ mr: 0.5, mb: 0.5 }}
              />
            )}
          </Box>
        )}
      </Paper>

      {/* Action Buttons */}
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between' }}>
        <Typography variant="body2" color="textSecondary">
          {totalCount > 0 &&
            `Showing ${(paginationModel.page * paginationModel.pageSize) + 1} - ${Math.min(
              (paginationModel.page + 1) * paginationModel.pageSize,
              totalCount
            )} of ${totalCount.toLocaleString()} total records`}
        </Typography>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={handleDownloadCSV}
          disabled={!penalties || penalties.length === 0}
        >
          Download CSV
        </Button>
      </Box>

      {/* Data Grid */}
      {error ? (
        <Alert severity="error">
          Failed to load penalties: {error.message}
        </Alert>
      ) : (
        <Paper sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={penalties || []}
            columns={columns}
            rowCount={totalCount || 0}
            loading={penaltiesLoading}
            pageSizeOptions={[25, 50, 100, 200, 500]}
            paginationModel={paginationModel}
            paginationMode="server"
            onPaginationModelChange={setPaginationModel}
            getRowId={(row) => row.penalty_fixed_id || row.id}
            disableRowSelectionOnClick
            getRowHeight={() => 'auto'}
            sx={{
              '& .MuiDataGrid-cell': {
                py: 1,
              },
            }}
          />
        </Paper>
      )}

      {/* Info Box */}
      <Paper sx={{ mt: 3, p: 2, bgcolor: 'info.light' }}>
        <Typography variant="body2">
          <strong>Note:</strong> Penalties data is fetched from the FWC API and stored in
          the staging table. Use filters to narrow down results. The system supports
          pagination for large datasets (up to 7,700+ records per award).
        </Typography>
      </Paper>
    </Box>
  );
}
