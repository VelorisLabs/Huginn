
import React, { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
    errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
        errorInfo: null,
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error, errorInfo: null };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo);
        this.setState({ errorInfo });
    }

    public render() {
        if (this.state.hasError) {
            return (
                <div className="p-8 max-w-2xl mx-auto mt-20 bg-red-50 border border-red-200 rounded-xl">
                    <h1 className="text-2xl font-bold text-red-800 mb-4">Something went wrong</h1>
                    <div className="bg-white p-4 rounded-lg border border-red-100 overflow-auto shadow-sm">
                        <p className="font-mono text-red-600 font-bold mb-2">
                            {this.state.error?.toString()}
                        </p>
                        <pre className="font-mono text-xs text-slate-500 whitespace-pre-wrap">
                            {this.state.errorInfo?.componentStack}
                        </pre>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
