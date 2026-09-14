"use client";

import { Component, type ReactNode } from "react";

type MapErrorBoundaryProps = {
  children: ReactNode;
  fallback?: ReactNode;
};

type MapErrorBoundaryState = {
  hasError: boolean;
};

export class MapErrorBoundary extends Component<
  MapErrorBoundaryProps,
  MapErrorBoundaryState
> {
  state: MapErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): MapErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: unknown) {
    console.error("Map rendering failed:", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div className="flex h-full min-h-[320px] items-center justify-center bg-[var(--surface-muted)] px-6 text-center">
            <div>
              <p className="font-medium text-civic-navy">Map unavailable</p>
              <p className="mt-2 text-sm text-[var(--muted)]">
                The map could not load, but you can still browse issues and report
                problems.
              </p>
            </div>
          </div>
        )
      );
    }

    return this.props.children;
  }
}
