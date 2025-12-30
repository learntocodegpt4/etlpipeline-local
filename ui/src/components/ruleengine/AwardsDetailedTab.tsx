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
  Grid,
  Tab,
  Tabs,
  Chip,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Download, Refresh } from '@mui/icons-material';
import { useAwardsDetailed } from '@/lib/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
}

export default function AwardsDetailedTab() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(50);
  const [awardCodeFilter, setAwardCodeFilter] = useState('');
  const [recordTypeFilter, setRecordTypeFilter] = useState('');
  const [tabValue, setTabValue] = useState(0);

  const { awardsDetailed, isLoading, error, mutate } = useAwardsDetailed(
    awardCodeFilter || undefined,
    recordTypeFilter || undefined,
    page + 1,
    pageSize
  );

  // Filter data based on selected tab
  const filteredData = awardsDetailed.filter((item: any) => {
    if (recordTypeFilter && item.recordType !== recordTypeFilter) return false;
    return true;
  });

  // Base award columns (common to all record types)
  const awardColumns: GridColDef[] = [
    { field: 'awardCode', headerName: 'Award Code', width: 120, sortable: true },
    { field: 'awardName', headerName: 'Award Name', width: 300, sortable: true },
    { field: 'versionNumber', headerName: 'Version', width: 100, sortable: true },
    {
      field: 'awardOperativeFrom',
      headerName: 'Operative From',
      width: 150,
      valueFormatter: (params) =>
        params.value ? new Date(params.value).toLocaleDateString() : 'N/A',
    },
    {
      field: 'awardOperativeTo',
      headerName: 'Operative To',
      width: 150,
      valueFormatter: (params) =>
        params.value ? new Date(params.value).toLocaleDateString() : 'Current',
    },
  ];

  // Classification columns
  const classificationColumns: GridColDef[] = [
    ...awardColumns,
    { field: 'classificationName', headerName: 'Classification', width: 200, sortable: true },
    { field: 'classificationLevel', headerName: 'Level', width: 100, sortable: true },
    { field: 'parentClassificationName', headerName: 'Parent Classification', width: 200, sortable: true },
  ];

  // Pay Rate columns
  const payRateColumns: GridColDef[] = [
    ...awardColumns,
    { field: 'classificationName', headerName: 'Classification', width: 200, sortable: true },
    { field: 'baseRateType', headerName: 'Rate Type', width: 120, sortable: true },
    {
      field: 'baseRate',
      headerName: 'Base Rate',
      width: 120,
      valueFormatter: (params) => params.value ? `$${params.value.toFixed(2)}` : 'N/A',
    },
    {
      field: 'calculatedRate',
      headerName: 'Calculated Rate',
      width: 150,
      valueFormatter: (params) => params.value ? `$${params.value.toFixed(2)}` : 'N/A',
    },
  ];

  // Expense Allowance columns
  const expenseColumns: GridColDef[] = [
    ...awardColumns,
    { field: 'expenseAllowanceName', headerName: 'Allowance', width: 200, sortable: true },
    {
      field: 'expenseAllowanceAmount',
      headerName: 'Amount',
      width: 120,
      valueFormatter: (params) => params.value ? `$${params.value.toFixed(2)}` : 'N/A',
    },
    { field: 'expensePaymentFrequency', headerName: 'Frequency', width: 120, sortable: true },
    { field: 'expenseIsAllPurpose', headerName: 'All Purpose', width: 100, sortable: true },
  ];

  // Wage Allowance columns
  const wageColumns: GridColDef[] = [
    ...awardColumns,
    { field: 'wageAllowanceName', headerName: 'Allowance', width: 200, sortable: true },
    {
      field: 'wageAllowanceRate',
      headerName: 'Rate',
      width: 120,
      valueFormatter: (params) => params.value ? `$${params.value.toFixed(2)}` : 'N/A',
    },
    { field: 'wageAllowanceRateUnit', headerName: 'Unit', width: 120, sortable: true },
    { field: 'wagePaymentFrequency', headerName: 'Frequency', width: 120, sortable: true },
  ];

  const handleExport = () => {
    let columns = awardColumns;
    if (tabValue === 1) columns = classificationColumns;
    else if (tabValue === 2) columns = payRateColumns;
    else if (tabValue === 3) columns = expenseColumns;
    else if (tabValue === 4) columns = wageColumns;

    const csv = [
      columns.map(col => col.headerName).join(','),
      ...filteredData.map((row: any) =>
        columns.map(col => row[col.field] || '').join(',')
      ),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `awards-detailed-${Date.now()}.csv`;
    a.click();
  };

  const recordTypeCounts = {
    classification: filteredData.filter((d: any) => d.recordType === 'Classification').length,
    payRate: filteredData.filter((d: any) => d.recordType === 'PayRate').length,
    expense: filteredData.filter((d: any) => d.recordType === 'ExpenseAllowance').length,
    wage: filteredData.filter((d: any) => d.recordType === 'WageAllowance').length,
  };

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Awards Detailed View
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            View comprehensive award details including classifications, pay rates, and allowances.
            Data includes all combinations from staging tables.
          </Typography>

          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Filter by Award Code"
                variant="outlined"
                size="small"
                value={awardCodeFilter}
                onChange={(e) => {
                  setAwardCodeFilter(e.target.value);
                  setPage(0);
                }}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Box sx={{ display: 'flex', gap: 2 }}>
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
                  disabled={filteredData.length === 0}
                >
                  Export CSV
                </Button>
              </Box>
            </Grid>
          </Grid>

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
        <>
          <Card>
            <CardContent>
              <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                <Tabs
                  value={tabValue}
                  onChange={(e, newValue) => {
                    setTabValue(newValue);
                    setRecordTypeFilter('');
                  }}
                  aria-label="award details tabs"
                >
                  <Tab
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        Overview <Chip label={awardsDetailed.length} size="small" />
                      </Box>
                    }
                  />
                  <Tab
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        Classifications <Chip label={recordTypeCounts.classification} size="small" />
                      </Box>
                    }
                  />
                  <Tab
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        Pay Rates <Chip label={recordTypeCounts.payRate} size="small" />
                      </Box>
                    }
                  />
                  <Tab
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        Expense Allowances <Chip label={recordTypeCounts.expense} size="small" />
                      </Box>
                    }
                  />
                  <Tab
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        Wage Allowances <Chip label={recordTypeCounts.wage} size="small" />
                      </Box>
                    }
                  />
                </Tabs>
              </Box>

              <TabPanel value={tabValue} index={0}>
                <Box sx={{ height: 600, width: '100%' }}>
                  <DataGrid
                    rows={awardsDetailed.map((row: any) => ({ ...row, id: row.id }))}
                    columns={awardColumns}
                    pageSizeOptions={[25, 50, 100]}
                    paginationModel={{ page, pageSize }}
                    onPaginationModelChange={(model) => {
                      setPage(model.page);
                      setPageSize(model.pageSize);
                    }}
                    disableRowSelectionOnClick
                  />
                </Box>
              </TabPanel>

              <TabPanel value={tabValue} index={1}>
                <Box sx={{ height: 600, width: '100%' }}>
                  <DataGrid
                    rows={filteredData
                      .filter((d: any) => d.recordType === 'Classification')
                      .map((row: any) => ({ ...row, id: row.id }))}
                    columns={classificationColumns}
                    pageSizeOptions={[25, 50, 100]}
                    paginationModel={{ page, pageSize }}
                    onPaginationModelChange={(model) => {
                      setPage(model.page);
                      setPageSize(model.pageSize);
                    }}
                    disableRowSelectionOnClick
                  />
                </Box>
              </TabPanel>

              <TabPanel value={tabValue} index={2}>
                <Box sx={{ height: 600, width: '100%' }}>
                  <DataGrid
                    rows={filteredData
                      .filter((d: any) => d.recordType === 'PayRate')
                      .map((row: any) => ({ ...row, id: row.id }))}
                    columns={payRateColumns}
                    pageSizeOptions={[25, 50, 100]}
                    paginationModel={{ page, pageSize }}
                    onPaginationModelChange={(model) => {
                      setPage(model.page);
                      setPageSize(model.pageSize);
                    }}
                    disableRowSelectionOnClick
                  />
                </Box>
              </TabPanel>

              <TabPanel value={tabValue} index={3}>
                <Box sx={{ height: 600, width: '100%' }}>
                  <DataGrid
                    rows={filteredData
                      .filter((d: any) => d.recordType === 'ExpenseAllowance')
                      .map((row: any) => ({ ...row, id: row.id }))}
                    columns={expenseColumns}
                    pageSizeOptions={[25, 50, 100]}
                    paginationModel={{ page, pageSize }}
                    onPaginationModelChange={(model) => {
                      setPage(model.page);
                      setPageSize(model.pageSize);
                    }}
                    disableRowSelectionOnClick
                  />
                </Box>
              </TabPanel>

              <TabPanel value={tabValue} index={4}>
                <Box sx={{ height: 600, width: '100%' }}>
                  <DataGrid
                    rows={filteredData
                      .filter((d: any) => d.recordType === 'WageAllowance')
                      .map((row: any) => ({ ...row, id: row.id }))}
                    columns={wageColumns}
                    pageSizeOptions={[25, 50, 100]}
                    paginationModel={{ page, pageSize }}
                    onPaginationModelChange={(model) => {
                      setPage(model.page);
                      setPageSize(model.pageSize);
                    }}
                    disableRowSelectionOnClick
                  />
                </Box>
              </TabPanel>
            </CardContent>
          </Card>
        </>
      )}
    </Box>
  );
}
