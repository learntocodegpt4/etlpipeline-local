'use client';

import { useState, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  Button,
  Alert,
  CircularProgress,
  Typography,
  Card,
  CardContent,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Download, Refresh } from '@mui/icons-material';
import { useRuleEngineAwards } from '@/lib/api';
import { useSnackbar } from '@/context/SnackbarContext';
import { useLoader } from '@/context/LoaderContext';

export default function AwardsTab() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(50);
  const [searchCode, setSearchCode] = useState('');
  const { showSnackbar } = useSnackbar();
  const { setIsLoading } = useLoader();
  
  const { awards, isLoading, error, mutate } = useRuleEngineAwards(page + 1, pageSize);

  useEffect(() => {
    setIsLoading(isLoading);
  }, [isLoading, setIsLoading]);

  useEffect(() => {
    if (error) {
      showSnackbar(`Failed to load awards: ${error.message}`, 'error');
    }
  }, [error, showSnackbar]);

  useEffect(() => {
    if (awards && awards.length > 0 && !isLoading && !error) {
      showSnackbar(`Loaded ${awards.length} awards`, 'success', 2000);
    }
  }, [awards, isLoading, error, showSnackbar]);

  const filteredAwards = awards?.filter((award: any) => 
    !searchCode || award.awardCode?.toLowerCase().includes(searchCode.toLowerCase()) ||
    award.awardName?.toLowerCase().includes(searchCode.toLowerCase())
  ) || [];

  const columns: GridColDef[] = [
    { field: 'awardCode', headerName: 'Award Code', width: 150, sortable: true },
    { field: 'awardName', headerName: 'Award Name', width: 400, sortable: true },
    { field: 'industryType', headerName: 'Industry', width: 200, sortable: true },
    { field: 'totalClassifications', headerName: 'Classifications', width: 120, sortable: true },
    { field: 'totalPayRates', headerName: 'Pay Rates', width: 120, sortable: true },
    { field: 'totalExpenseAllowances', headerName: 'Expense Allow.', width: 120, sortable: true },
    { field: 'totalWageAllowances', headerName: 'Wage Allow.', width: 120, sortable: true },
  ];

  const handleExport = () => {
    const csv = [
      columns.map(col => col.headerName).join(','),
      ...filteredAwards.map((row: any) => 
        columns.map(col => row[col.field] || '').join(',')
      )
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'awards.csv';
    a.click();
  };

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Awards Summary
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            View all FWC awards with basic information. Use the search to filter by award code or name.
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
            <TextField
              label="Search by Code or Name"
              variant="outlined"
              size="small"
              value={searchCode}
              onChange={(e) => setSearchCode(e.target.value)}
              sx={{ flexGrow: 1 }}
            />
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={() => mutate()}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<Download />}
              onClick={handleExport}
              disabled={filteredAwards.length === 0}
            >
              Export CSV
            </Button>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Error loading awards: {error.message}
            </Alert>
          )}
        </CardContent>
      </Card>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Box sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={filteredAwards.map((row: any) => ({ ...row, id: row.id }))}
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
      )}
    </Box>
  );
}
