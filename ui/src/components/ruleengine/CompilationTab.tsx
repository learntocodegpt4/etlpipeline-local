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
  Grid,
} from '@mui/material';
import { PlayArrow, Download, Bolt } from '@mui/icons-material';
import { compileAwards, compileAwardsDetailed, getAwardRulesJson, applyRule } from '@/lib/api';
import { useSnackbar } from '@/context/SnackbarContext';
import { useLoader } from '@/context/LoaderContext';

export default function CompilationTab() {
  const [awardCode, setAwardCode] = useState('');
  const [ruleCode, setRuleCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rulesJson, setRulesJson] = useState<any | null>(null);
  const { showSnackbar } = useSnackbar();
  const { setIsLoading } = useLoader();

  useEffect(() => {
    setIsLoading(loading);
  }, [loading, setIsLoading]);

  useEffect(() => {
    if (error) {
      showSnackbar(error, 'error');
    }
  }, [error, showSnackbar]);

  useEffect(() => {
    if (message && !error) {
      showSnackbar(message, 'success', 3000);
    }
  }, [message, error, showSnackbar]);

  const runCompileAwards = async () => {
    setLoading(true);
    setMessage(null);
    setError(null);
    try {
      const res = await compileAwards(awardCode || undefined);
      setMessage(res.message || 'Awards summary compilation triggered');
    } catch (e: any) {
      setError(e.message || 'Failed to compile awards summary');
    } finally {
      setLoading(false);
    }
  };

  const runCompileAwardsDetailed = async () => {
    setLoading(true);
    setMessage(null);
    setError(null);
    try {
      const res = await compileAwardsDetailed(awardCode || undefined);
      setMessage(res.message || 'Awards detailed compilation triggered');
    } catch (e: any) {
      setError(e.message || 'Failed to compile awards detailed');
    } finally {
      setLoading(false);
    }
  };

  const fetchRulesJson = async () => {
    setLoading(true);
    setMessage(null);
    setError(null);
    try {
      const json = await getAwardRulesJson(awardCode);
      setRulesJson(json);
      setMessage('Fetched award rules JSON');
    } catch (e: any) {
      setError(e.message || 'Failed to fetch award rules JSON');
    } finally {
      setLoading(false);
    }
  };

  const downloadJson = () => {
    if (!rulesJson) return;
    const blob = new Blob([JSON.stringify(rulesJson, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `award-rules-${awardCode || 'ALL'}-${Date.now()}.json`;
    a.click();
  };

  const runApplyRule = async () => {
    if (!awardCode || !ruleCode) {
      setError('Award Code and Rule Code are required to apply a rule');
      return;
    }
    setLoading(true);
    setMessage(null);
    setError(null);
    try {
      const res = await applyRule(awardCode, ruleCode);
      setMessage(res.message || 'Rule applied successfully');
    } catch (e: any) {
      setError(e.message || 'Failed to apply rule');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Compilation & Rule Operations
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Compile awards summary/detailed data and fetch award rules JSON. Optionally apply a specific rule to an award.
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
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                label="Rule Code"
                variant="outlined"
                size="small"
                value={ruleCode}
                onChange={(e) => setRuleCode(e.target.value)}
                fullWidth
              />
            </Grid>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  startIcon={<PlayArrow />}
                  onClick={runCompileAwards}
                  disabled={loading}
                >
                  Compile Awards Summary
                </Button>
                <Button
                  variant="contained"
                  startIcon={<PlayArrow />}
                  onClick={runCompileAwardsDetailed}
                  disabled={loading}
                >
                  Compile Awards Detailed
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Bolt />}
                  onClick={runApplyRule}
                  disabled={loading || !awardCode || !ruleCode}
                >
                  Apply Rule
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<PlayArrow />}
                  onClick={fetchRulesJson}
                  disabled={loading || !awardCode}
                >
                  Fetch Award Rules JSON
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Download />}
                  onClick={downloadJson}
                  disabled={!rulesJson}
                >
                  Download JSON
                </Button>
              </Box>
            </Grid>
          </Grid>

          {error && (
            <Alert severity="error" sx={{ mt: 1 }}>
              {error}
            </Alert>
          )}
          {message && (
            <Alert severity="success" sx={{ mt: 1 }}>
              {message}
            </Alert>
          )}
          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress />
            </Box>
          )}
        </CardContent>
      </Card>

      {rulesJson && (
        <Card>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom>
              Award Rules JSON Preview
            </Typography>
            <Box sx={{ maxHeight: 400, overflow: 'auto', fontFamily: 'monospace', fontSize: 12, whiteSpace: 'pre' }}>
              {JSON.stringify(rulesJson, null, 2)}
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
