'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  FormControlLabel,
  Switch,
} from '@mui/material';
import { Clear, Pause, PlayArrow } from '@mui/icons-material';

interface LogMessage {
  id: number;
  timestamp: string;
  type: string;
  level?: string;
  message?: string;
  job_id?: string;
  step?: string;
}

export default function LogsPage() {
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [paused, setPaused] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [connected, setConnected] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const idCounter = useRef(0);

  const scrollToBottom = useCallback(() => {
    if (autoScroll) {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [autoScroll]);

  useEffect(() => {
    scrollToBottom();
  }, [logs, scrollToBottom]);

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8081/ws';

    const connect = () => {
      wsRef.current = new WebSocket(`${wsUrl}/logs`);

      wsRef.current.onopen = () => {
        setConnected(true);
        setLogs((prev) => [
          ...prev,
          {
            id: idCounter.current++,
            timestamp: new Date().toISOString(),
            type: 'system',
            message: 'Connected to log stream',
          },
        ]);
      };

      wsRef.current.onclose = () => {
        setConnected(false);
        setLogs((prev) => [
          ...prev,
          {
            id: idCounter.current++,
            timestamp: new Date().toISOString(),
            type: 'system',
            message: 'Disconnected from log stream',
          },
        ]);
        // Reconnect after 5 seconds
        setTimeout(connect, 5000);
      };

      wsRef.current.onerror = () => {
        setLogs((prev) => [
          ...prev,
          {
            id: idCounter.current++,
            timestamp: new Date().toISOString(),
            type: 'error',
            message: 'WebSocket connection error',
          },
        ]);
      };

      wsRef.current.onmessage = (event) => {
        if (paused) return;

        try {
          const data = JSON.parse(event.data);
          setLogs((prev) => {
            const newLogs = [
              ...prev,
              {
                id: idCounter.current++,
                ...data,
              },
            ];
            // Keep only last 1000 logs
            return newLogs.slice(-1000);
          });
        } catch (e) {
          console.error('Failed to parse log message:', e);
        }
      };
    };

    connect();

    return () => {
      wsRef.current?.close();
    };
  }, [paused]);

  const getLevelColor = (level?: string): string => {
    switch (level?.toLowerCase()) {
      case 'error':
        return '#f44336';
      case 'warning':
        return '#ff9800';
      case 'info':
        return '#2196f3';
      case 'debug':
        return '#9e9e9e';
      default:
        return '#4caf50';
    }
  };

  const getTypeChip = (type: string) => {
    switch (type) {
      case 'log':
        return <Chip label="LOG" size="small" color="primary" />;
      case 'job_event':
        return <Chip label="JOB" size="small" color="secondary" />;
      case 'heartbeat':
        return <Chip label="HB" size="small" color="default" />;
      case 'system':
        return <Chip label="SYS" size="small" color="info" />;
      case 'error':
        return <Chip label="ERR" size="small" color="error" />;
      default:
        return <Chip label={type.toUpperCase()} size="small" />;
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">
          Live Logs
          <Chip
            label={connected ? 'Connected' : 'Disconnected'}
            color={connected ? 'success' : 'error'}
            size="small"
            sx={{ ml: 2 }}
          />
        </Typography>
        <Box>
          <FormControlLabel
            control={
              <Switch
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
              />
            }
            label="Auto-scroll"
          />
          <Tooltip title={paused ? 'Resume' : 'Pause'}>
            <IconButton onClick={() => setPaused(!paused)}>
              {paused ? <PlayArrow /> : <Pause />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Clear logs">
            <IconButton onClick={() => setLogs([])}>
              <Clear />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Paper
        sx={{
          height: 'calc(100vh - 200px)',
          overflow: 'auto',
          bgcolor: '#1e1e1e',
          p: 2,
        }}
      >
        {logs.map((log) => (
          <Box
            key={log.id}
            sx={{
              py: 0.5,
              fontFamily: 'monospace',
              fontSize: '0.85rem',
              borderBottom: '1px solid rgba(255,255,255,0.1)',
              display: 'flex',
              alignItems: 'flex-start',
              gap: 1,
            }}
          >
            <Typography
              component="span"
              sx={{ color: '#888', minWidth: 180, flexShrink: 0 }}
            >
              {new Date(log.timestamp).toLocaleTimeString()}
            </Typography>
            {getTypeChip(log.type)}
            {log.level && (
              <Typography
                component="span"
                sx={{
                  color: getLevelColor(log.level),
                  minWidth: 70,
                  fontWeight: 'bold',
                }}
              >
                [{log.level.toUpperCase()}]
              </Typography>
            )}
            {log.job_id && (
              <Typography component="span" sx={{ color: '#bb86fc' }}>
                [{log.job_id.slice(0, 8)}]
              </Typography>
            )}
            {log.step && (
              <Typography component="span" sx={{ color: '#03dac6' }}>
                [{log.step}]
              </Typography>
            )}
            <Typography component="span" sx={{ color: '#fff', flex: 1 }}>
              {log.message}
            </Typography>
          </Box>
        ))}
        <div ref={logsEndRef} />
      </Paper>
    </Box>
  );
}
