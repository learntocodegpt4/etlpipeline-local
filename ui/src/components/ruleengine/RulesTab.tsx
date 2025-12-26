'use client';

import { Box, Typography, Alert } from '@mui/material';

export default function RulesTab() {
  return (
    <Box>
      <Typography variant="h6">Rules</Typography>
      <Alert severity="info" sx={{ mt: 2 }}>
        Implementation in progress. See RULE_ENGINE_UI_IMPLEMENTATION.md for full specification.
      </Alert>
    </Box>
  );
}
