import { Component, type ReactNode } from "react";

// a crash in one page shows a message instead of a blank screen
export class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div role="alert" className="card p-8">
        <p className="label">Error</p>
        <h1 className="mt-2 text-4xl">
          This page <em>broke</em>
        </h1>
        <p className="mt-3 text-sm text-ink-2">Reload to start again. The details below help to fix it.</p>
        <pre data-error className="mt-4 overflow-x-auto rounded-xl bg-card-soft p-4 font-mono text-xs text-val">
          {this.state.error.message}
        </pre>
      </div>
    );
  }
}
