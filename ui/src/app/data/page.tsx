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
} from '@mui/material';
import { DataGrid, GridColDef, GridPaginationModel } from '@mui/x-data-grid';
import { useTables, useDataPreview } from '@/lib/api';

export default function DataPage() {
  const [selectedTable, setSelectedTable] = useState('awards');
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 50,
  });

  const { tables, isLoading: tablesLoading } = useTables();
  const { data, total, isLoading: dataLoading, error } = useDataPreview(
    selectedTable,
    paginationModel.page + 1,
    paginationModel.pageSize
  );

  // Generate columns dynamically from data
  const columns: GridColDef[] = data && data.length > 0
    ? Object.keys(data[0]).map((key) => ({
        field: key,
        headerName: key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
        width: key === 'id' ? 80 : key.includes('name') || key.includes('description') ? 250 : 150,
        flex: key.includes('name') || key.includes('description') ? 1 : undefined,
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
        <FormControl sx={{ minWidth: 200 }}>
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
      </Paper>

      {/* Data Grid */}
      {error ? (
        <Alert severity="error">Failed to load data: {error.message}</Alert>
      ) : (
        <Paper sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={data || []}
            columns={columns}
            rowCount={total || 0}
            loading={dataLoading}
            pageSizeOptions={[25, 50, 100]}
            paginationModel={paginationModel}
            paginationMode="server"
            onPaginationModelChange={setPaginationModel}
            getRowId={(row) => row.id}
            disableRowSelectionOnClick
          />
        </Paper>
      )}
    </Box>
  );
}
