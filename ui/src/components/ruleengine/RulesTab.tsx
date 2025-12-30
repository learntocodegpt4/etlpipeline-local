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
  FormControlLabel,
  Checkbox,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Download, Refresh, Add } from '@mui/icons-material';
import { useRules } from '@/lib/api';
import { useSnackbar } from '@/context/SnackbarContext';
import { useLoader } from '@/context/LoaderContext';
import CreateRuleDialog from './CreateRuleDialog';

export default function RulesTab() {
  const [ruleType, setRuleType] = useState('');
  const [ruleCategory, setRuleCategory] = useState('');
  const [isActive, setIsActive] = useState<boolean | undefined>(undefined);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const { showSnackbar } = useSnackbar();
  const { setIsLoading } = useLoader();

  const { rules, isLoading, error, mutate, totalCount } = useRules(
    ruleType || undefined,
    ruleCategory || undefined,
    typeof isActive === 'boolean' ? isActive : undefined,
    1,
    1000
  );

  useEffect(() => {
    setIsLoading(isLoading);
  }, [isLoading, setIsLoading]);

  useEffect(() => {
    if (error) {
      showSnackbar(`Failed to load rules: ${error.message}`, 'error');
    }
  }, [error, showSnackbar]);

  useEffect(() => {
    if (rules && rules.length > 0 && !isLoading && !error) {
      showSnackbar(`Loaded ${rules.length} rules`, 'success', 2000);
    }
  }, [rules, isLoading, error, showSnackbar]);

  const filtered = useMemo(() => {
    return (rules || []).filter((r: any) =>
      (!ruleType || (r.ruleType || '').toLowerCase().includes(ruleType.toLowerCase())) &&
      (!ruleCategory || (r.ruleCategory || '').toLowerCase().includes(ruleCategory.toLowerCase())) &&
      (typeof isActive !== 'boolean' || r.isActive === isActive)
    );
  }, [rules, ruleType, ruleCategory, isActive]);

  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'ruleCode', headerName: 'Rule Code', width: 140 },
      { field: 'ruleName', headerName: 'Rule Name', width: 240 },
      { field: 'ruleType', headerName: 'Type', width: 140 },
      { field: 'ruleCategory', headerName: 'Category', width: 160 },
      { field: 'priority', headerName: 'Priority', width: 100 },
      { field: 'isActive', headerName: 'Active', width: 100 },
      { field: 'createdBy', headerName: 'Created By', width: 140 },
      {
        field: 'createdAt',
        headerName: 'Created At',
        width: 160,
        valueFormatter: (params) => params.value ? new Date(params.value).toLocaleString() : 'N/A',
      },
      {
        field: 'updatedAt',
        headerName: 'Updated At',
        width: 160,
        valueFormatter: (params) => params.value ? new Date(params.value).toLocaleString() : 'N/A',
      },
      { field: 'ruleExpression', headerName: 'Expression', width: 220 },
      { field: 'ruleDefinition', headerName: 'Definition', width: 400 },
    ],
    []
  );

  const handleExport = () => {
    const csv = [
      columns.map((c) => c.headerName).join(','),
      ...filtered.map((row: any) => columns.map((c) => JSON.stringify(row[c.field] ?? '').replace(/,/g, ';')).join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rules-${Date.now()}.csv`;
    a.click();
  };

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Rules
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Browse and filter rule definitions by type, category, and active status.
          </Typography>

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                label="Rule Type"
                variant="outlined"
                size="small"
                value={ruleType}
                onChange={(e) => setRuleType(e.target.value)}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                label="Rule Category"
                variant="outlined"
                size="small"
                value={ruleCategory}
                onChange={(e) => setRuleCategory(e.target.value)}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={isActive === true}
                    indeterminate={isActive === undefined}
                    onChange={(e) => setIsActive(e.target.checked ? true : undefined)}
                  />
                }
                label="Active Only"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={isActive === false}
                    indeterminate={isActive === undefined}
                    onChange={(e) => setIsActive(e.target.checked ? false : undefined)}
                  />
                }
                label="Inactive Only"
              />
            </Grid>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <Button variant="outlined" startIcon={<Refresh />} onClick={() => mutate()}>
                  Refresh
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => setCreateDialogOpen(true)}
                >
                  Create Rule
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Download />}
                  onClick={handleExport}
                  disabled={filtered.length === 0}
                >
                  Export CSV
                </Button>
                <Chip label={`Records: ${totalCount}`} color="primary" variant="outlined" />
              </Box>
            </Grid>
          </Grid>

          {error && (
            <Alert severity="error" sx={{ mt: 1 }}>
              Error loading rules: {error.message}
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
                rows={filtered.map((row: any) => ({ ...row, id: row.id ?? row.ruleCode }))}
                columns={columns}
                pageSizeOptions={[25, 50, 100]}
                disableRowSelectionOnClick
              />
            </Box>
          </CardContent>
        </Card>
      )}

      <CreateRuleDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSuccess={() => {
          setCreateDialogOpen(false);
          mutate();
          showSnackbar('Rule created successfully', 'success');
        }}
      />
    </Box>
  );
}
