import type { Metadata } from 'next';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AppRouterCacheProvider } from '@mui/material-nextjs/v14-appRouter';
import theme from '@/lib/theme';
import Layout from '@/components/Layout';
import { SnackbarProvider } from '@/context/SnackbarContext';
import { LoaderProvider } from '@/context/LoaderContext';

export const metadata: Metadata = {
  title: 'FWC ETL Pipeline',
  description: 'ETL Pipeline Dashboard for FWC Modern Awards',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AppRouterCacheProvider>
          <ThemeProvider theme={theme}>
            <CssBaseline />
            <LoaderProvider>
              <SnackbarProvider>
                <Layout>{children}</Layout>
              </SnackbarProvider>
            </LoaderProvider>
          </ThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
