'use client';

import { useState } from 'react';
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

export default function AwardsTab() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(50);
  const [searchCode, setSearchCode] = useState('');
  
  const { awards, isLoading, error, mutate } = useRuleEngineAwards(page + 1, pageSize);

  const filteredAwards = awards?.filter((award: any) => 
    !searchCode || award.code?.toLowerCase().includes(searchCode.toLowerCase()) ||
    award.name?.toLowerCase().includes(searchCode.toLowerCase())
  ) || [];

  const columns: GridColDef[] = [
    { field: 'code', headerName: 'Award Code', width: 150, sortable: true },
    { field: 'name', headerName: 'Award Name', width: 400, sortable: true },
    { field: 'industry', headerName: 'Industry', width: 200, sortable: true },
    { field: 'version_number', headerName: 'Version', width: 100, sortable: true },
    { 
      field: 'award_operative_from', 
      headerName: 'Operative From', 
      width: 150,
      valueFormatter: (params) => params.value ? new Date(params.value).toLocaleDateString() : 'N/A'
    },
    { 
      field: 'award_operative_to', 
      headerName: 'Operative To', 
      width: 150,
      valueFormatter: (params) => params.value ? new Date(params.value).toLocaleDateString() : 'Current'
    },
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
            rows={filteredAwards.map((row: any, index: number) => ({ ...row, id: row.award_id || index }))}
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
