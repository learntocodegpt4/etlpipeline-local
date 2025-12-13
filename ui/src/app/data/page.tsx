'use client';

import { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Button,
  TextField,
  Stack,
} from '@mui/material';
import { DataGrid, GridColDef, GridPaginationModel } from '@mui/x-data-grid';
import { useTables, useDataPreview } from '@/lib/api';

export default function DataPage() {
  const [selectedTable, setSelectedTable] = useState('Stg_TblAwards');
  const [awardFilter, setAwardFilter] = useState('');
  const [nameFilter, setNameFilter] = useState('');
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 50,
  });

  const { tables, isLoading: tablesLoading } = useTables();

  // Build filters object for server-side filtering
  const filters: Record<string, string> = {};
  if (awardFilter) filters.award_code = awardFilter;
  if (nameFilter) filters.name = nameFilter;

  const { data, total, isLoading: dataLoading, error } = useDataPreview(
    selectedTable,
    paginationModel.page + 1,
    paginationModel.pageSize,
    filters
  );

  const currentTableCount =
    tables?.find((t: any) => t.table === selectedTable)?.record_count ?? 0;
  const effectiveTotal = total ?? currentTableCount ?? 0;

  // Generate columns dynamically from data
  const columns: GridColDef[] = data && data.length > 0
    ? Object.keys(data[0]).map((key) => ({
        field: key,
        headerName: key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
        // Give name/description fields more space and allow wrapping
        minWidth: key === 'id' ? 80 : key.toLowerCase().includes('name') || key.toLowerCase().includes('description') ? 300 : 150,
        flex: key.toLowerCase().includes('name') || key.toLowerCase().includes('description') ? 2 : 1,
        renderCell: (params) => {
          const value = params.value as any;
          if (value === null || value === undefined) return '';
          return (
            <Typography sx={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>
              {String(value)}
            </Typography>
          );
        },
      }))
    : [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Data Preview
      </Typography>

      {/* Table Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {tablesLoading ? (
          <Grid item xs={12}>
            <CircularProgress size={24} />
          </Grid>
        ) : (
          tables?.map((table: any) => (
            <Grid item xs={12} sm={6} md={4} lg={2} key={table.table}>
              <Card
                onClick={() => setSelectedTable(table.table)}
                sx={{
                  cursor: 'pointer',
                  border: selectedTable === table.table ? 2 : 0,
                  borderColor: 'primary.main',
                }}
              >
                <CardContent>
                  <Typography variant="subtitle2" color="textSecondary">
                    {table.table}
                  </Typography>
                  <Typography variant="h5">
                    {table.record_count?.toLocaleString() || 0}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))
        )}
      </Grid>

      {/* Table Selection */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item>
            <FormControl sx={{ minWidth: 220 }}>
              <InputLabel>Table</InputLabel>
              <Select
                value={selectedTable}
                label="Table"
                onChange={(e) => {
                  setSelectedTable(e.target.value);
                  setPaginationModel({ ...paginationModel, page: 0 });
                }}
              >
                {tables?.map((table: any) => (
                  <MenuItem key={table.table} value={table.table}>
                    {table.table} ({table.record_count?.toLocaleString() || 0} records)
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item>
            <TextField
              label="Filter by award code"
              value={awardFilter}
              onChange={(e) => {
                setAwardFilter(e.target.value);
                setPaginationModel({ ...paginationModel, page: 0 });
              }}
              size="small"
            />
          </Grid>

          <Grid item>
            <TextField
              label="Name contains"
              value={nameFilter}
              onChange={(e) => setNameFilter(e.target.value)}
              size="small"
            />
          </Grid>

          <Grid item>
            <Stack direction="row" spacing={1}>
              <Button
                variant="contained"
                onClick={() => {
                  // Reset filters
                  setAwardFilter('');
                  setNameFilter('');
                  setSelectedTable('awards');
                }}
              >
                Reset
              </Button>
              <Button
                variant="outlined"
                onClick={() => {
                  // Download current page rows as CSV
                  const rows = (data || []) as any[];
                  if (!rows || rows.length === 0) return;
                  const hdrs = columns.map((c) => c.field);
                  const csv = [hdrs.join(',')]
                    .concat(rows.map(r => hdrs.map(h => '"' + (r[h] ?? '') + '"').join(',')))
                    .join('\n');
                  const blob = new Blob([csv], { type: 'text/csv' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${selectedTable}_export.csv`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
              >
                Download CSV
              </Button>
            </Stack>
          </Grid>
        </Grid>
      </Paper>

      {/* Data Grid */}
      {error ? (
        <Alert severity="error">Failed to load data: {error.message}</Alert>
      ) : (
        <Paper sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={data || []}
            columns={columns}
            rowCount={effectiveTotal || 0}
            loading={dataLoading}
            pageSizeOptions={[25, 50, 100]}
            paginationModel={paginationModel}
            paginationMode="server"
            onPaginationModelChange={setPaginationModel}
            getRowId={(row) => row.id ?? row._id ?? `${selectedTable}-${JSON.stringify(row)}`}
            disableRowSelectionOnClick
          />
        </Paper>
      )}
      {/* Docs iframe */}
      {/* <Paper sx={{ mt: 3, p: 2 }}>
        <Typography variant="h6" gutterBottom>API Docs</Typography>
        <iframe
          title="API Docs"
          src={`${(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8081').replace('/api','')}/docs`}
          style={{ width: '100%', height: '600px', border: 'none' }}
        />
      </Paper> */}
    </Box>
  );
}
