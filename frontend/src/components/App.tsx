import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import Dashboard from './Dashboard';
import { ErrorBoundary } from './ErrorBoundary';
import { WorkspaceProvider } from './workspace/WorkspaceContext';

export default function App() {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <WorkspaceProvider>
          <Dashboard />
        </WorkspaceProvider>
      </ErrorBoundary>
    </QueryClientProvider>
  );
}
