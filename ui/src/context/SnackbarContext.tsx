'use client';

import React, { createContext, useContext, useState, useCallback } from 'react';
import { Snackbar, Alert, AlertColor } from '@mui/material';

export interface SnackbarMessage {
  id: string;
  message: string;
  severity: AlertColor;
  duration?: number;
}

interface SnackbarContextType {
  showSnackbar: (message: string, severity?: AlertColor, duration?: number) => void;
  hideSnackbar: (id?: string) => void;
}

const SnackbarContext = createContext<SnackbarContextType | undefined>(undefined);

export function SnackbarProvider({ children }: { children: React.ReactNode }) {
  const [messages, setMessages] = useState<SnackbarMessage[]>([]);

  const showSnackbar = useCallback(
    (message: string, severity: AlertColor = 'info', duration: number = 5000) => {
      const id = `${Date.now()}-${Math.random()}`;
      const newMessage: SnackbarMessage = { id, message, severity, duration };

      setMessages((prev) => [...prev, newMessage]);

      if (duration > 0) {
        setTimeout(() => {
          setMessages((prev) => prev.filter((msg) => msg.id !== id));
        }, duration);
      }
    },
    []
  );

  const hideSnackbar = useCallback((id?: string) => {
    if (id) {
      setMessages((prev) => prev.filter((msg) => msg.id !== id));
    } else {
      setMessages([]);
    }
  }, []);

  return (
    <SnackbarContext.Provider value={{ showSnackbar, hideSnackbar }}>
      {children}
      <div style={{ position: 'fixed', bottom: 16, right: 16, zIndex: 9999, maxWidth: 400 }}>
        {messages.map((msg, index) => (
          <Snackbar
            key={msg.id}
            open={true}
            autoHideDuration={msg.duration}
            onClose={() => hideSnackbar(msg.id)}
            style={{ marginBottom: index > 0 ? 12 : 0 }}
          >
            <Alert
              onClose={() => hideSnackbar(msg.id)}
              severity={msg.severity}
              sx={{ width: '100%' }}
            >
              {msg.message}
            </Alert>
          </Snackbar>
        ))}
      </div>
    </SnackbarContext.Provider>
  );
}

export function useSnackbar() {
  const context = useContext(SnackbarContext);
  if (!context) {
    throw new Error('useSnackbar must be used within SnackbarProvider');
  }
  return context;
}
