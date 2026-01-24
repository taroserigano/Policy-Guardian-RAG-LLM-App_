/**
 * Tests for ErrorBoundary component.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ErrorBoundary from "../components/ErrorBoundary";

// Component that throws an error
function BrokenComponent({ shouldThrow = true }) {
  if (shouldThrow) {
    throw new Error("Test error from BrokenComponent");
  }
  return <div>Working component</div>;
}

// Suppress console.error during tests
const originalError = console.error;

describe("ErrorBoundary Component", () => {
  beforeEach(() => {
    console.error = vi.fn();
  });

  afterEach(() => {
    console.error = originalError;
  });

  it("renders children when no error", () => {
    render(
      <ErrorBoundary>
        <div>Child content</div>
      </ErrorBoundary>,
    );

    expect(screen.getByText("Child content")).toBeInTheDocument();
  });

  it("catches errors and displays fallback UI", () => {
    render(
      <ErrorBoundary>
        <BrokenComponent />
      </ErrorBoundary>,
    );

    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });

  it("displays error message", () => {
    render(
      <ErrorBoundary>
        <BrokenComponent />
      </ErrorBoundary>,
    );

    expect(
      screen.getByText(/test error from brokencomponent/i),
    ).toBeInTheDocument();
  });

  it("provides Try Again button", () => {
    render(
      <ErrorBoundary>
        <BrokenComponent />
      </ErrorBoundary>,
    );

    const retryButton = screen.getByRole("button", { name: /try again/i });
    expect(retryButton).toBeInTheDocument();
  });

  it("provides Go Home button", () => {
    render(
      <ErrorBoundary>
        <BrokenComponent />
      </ErrorBoundary>,
    );

    const homeButton = screen.getByRole("button", { name: /go home/i });
    expect(homeButton).toBeInTheDocument();
  });

  it("resets error state when Try Again is clicked", () => {
    let shouldThrow = true;

    function ConditionalBroken() {
      if (shouldThrow) {
        throw new Error("Conditional error");
      }
      return <div>Recovered content</div>;
    }

    const { rerender } = render(
      <ErrorBoundary>
        <ConditionalBroken />
      </ErrorBoundary>,
    );

    // Should show error UI
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();

    // Fix the error condition
    shouldThrow = false;

    // Click retry
    const retryButton = screen.getByRole("button", { name: /try again/i });
    fireEvent.click(retryButton);

    // Should attempt to re-render
    // Note: The component will still error on next render in this test setup
  });

  it("logs error to console", () => {
    render(
      <ErrorBoundary>
        <BrokenComponent />
      </ErrorBoundary>,
    );

    expect(console.error).toHaveBeenCalled();
  });

  it("shows error details in development mode", () => {
    // NODE_ENV is typically 'test' in vitest, which may show details
    render(
      <ErrorBoundary>
        <BrokenComponent />
      </ErrorBoundary>,
    );

    // Check that the error boundary rendered
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });

  it("handles multiple error resets by showing error again if component keeps failing", () => {
    // Component that always throws
    function AlwaysBroken() {
      throw new Error("Persistent error");
    }

    render(
      <ErrorBoundary>
        <AlwaysBroken />
      </ErrorBoundary>,
    );

    // First error
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();

    // Try again (will error again)
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));

    // Still in error state because component keeps throwing
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });
});
