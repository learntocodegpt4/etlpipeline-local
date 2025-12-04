import type { Metadata } from 'next'
import { ThemeProvider } from '@/components/ThemeProvider'
import { AppBar, Toolbar, Typography, Container, Box } from '@mui/material'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'FWC ETL Pipeline',
  description: 'ETL Pipeline Management Dashboard for FWC Modern Awards',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <ThemeProvider>
          <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <AppBar position="static">
              <Toolbar>
                <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                  <Link href="/" style={{ color: 'inherit', textDecoration: 'none' }}>
                    FWC ETL Pipeline
                  </Link>
                </Typography>
                <Link href="/jobs" style={{ color: 'inherit', textDecoration: 'none', marginRight: 16 }}>
                  Jobs
                </Link>
                <Link href="/data" style={{ color: 'inherit', textDecoration: 'none', marginRight: 16 }}>
                  Data
                </Link>
                <Link href="/logs" style={{ color: 'inherit', textDecoration: 'none' }}>
                  Logs
                </Link>
              </Toolbar>
            </AppBar>
            <Container component="main" sx={{ mt: 4, mb: 4, flexGrow: 1 }}>
              {children}
            </Container>
            <Box component="footer" sx={{ py: 3, px: 2, mt: 'auto', backgroundColor: 'grey.200' }}>
              <Container maxWidth="sm">
                <Typography variant="body2" color="text.secondary" align="center">
                  FWC ETL Pipeline v1.0.0
                </Typography>
              </Container>
            </Box>
          </Box>
        </ThemeProvider>
      </body>
    </html>
  )
}
