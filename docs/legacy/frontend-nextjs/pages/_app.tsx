import type { AppProps } from 'next/app';
import { AuthProvider } from '@/hooks/useAuth';
import '@/styles/globals.css';
import '@/lib/i18n';
import { Component, ReactNode } from 'react';

class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center p-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Something went wrong</h1>
            <p className="text-gray-600 mb-6">An unexpected error occurred. Please try refreshing the page.</p>
            <button
              onClick={() => { this.setState({ hasError: false }); window.location.reload(); }}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <ErrorBoundary>
        <Component {...pageProps} />
      </ErrorBoundary>
    </AuthProvider>
  );
}

export default MyApp;