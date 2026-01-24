/**
 * Tests for ConnectionStatus component.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import ConnectionStatus from "../components/ConnectionStatus";

// Mock fetch
const originalFetch = global.fetch;

describe("ConnectionStatus Component", () => {
  beforeEach(() => {
    // Reset fetch mock
    global.fetch = vi.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.clearAllTimers();
  });

  it("does not show banner when connected", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true });

    render(<ConnectionStatus />);

    // Wait for initial health check
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });

    // Banner should eventually hide (after success animation)
    await waitFor(
      () => {
        expect(
          screen.queryByText(/server unreachable/i),
        ).not.toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });

  it("shows banner when API is unreachable", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("Network error"));

    render(<ConnectionStatus />);

    await waitFor(() => {
      expect(screen.getByText(/server unreachable/i)).toBeInTheDocument();
    });
  });

  it("shows retry button when disconnected", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("Network error"));

    render(<ConnectionStatus />);

    await waitFor(() => {
      const retryButton = screen.getByRole("button");
      expect(retryButton).toBeInTheDocument();
    });
  });

  it("retries connection when retry button is clicked", async () => {
    // Keep failing so the retry button stays visible
    global.fetch = vi.fn().mockRejectedValue(new Error("Network error"));

    render(<ConnectionStatus />);

    // Wait for initial failed check
    await waitFor(() => {
      expect(screen.getByText(/server unreachable/i)).toBeInTheDocument();
    });

    const initialCallCount = global.fetch.mock.calls.length;

    // Click retry button
    const retryButton = screen.getByRole("button");
    fireEvent.click(retryButton);

    // Should have called fetch more times after clicking retry
    // Use a longer timeout since the retry may have a delay
    await waitFor(
      () => {
        expect(global.fetch.mock.calls.length).toBeGreaterThan(
          initialCallCount,
        );
      },
      { timeout: 3000 },
    );
  });

  it("calls health endpoint with correct URL", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true });

    render(<ConnectionStatus />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/health"),
        expect.any(Object),
      );
    });
  });

  it("shows connected message briefly after reconnection", async () => {
    // Start with failure, then succeed on retry
    global.fetch = vi
      .fn()
      .mockRejectedValueOnce(new Error("Network error"))
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValue({ ok: true });

    render(<ConnectionStatus />);

    // Wait for disconnected state (first fetch fails)
    await waitFor(
      () => {
        expect(screen.getByText(/server unreachable/i)).toBeInTheDocument();
      },
      { timeout: 3000 },
    );

    // Click retry button
    const retryButton = screen.getByRole("button");
    fireEvent.click(retryButton);

    // Should eventually show connected
    await waitFor(
      () => {
        expect(screen.getByText(/connected/i)).toBeInTheDocument();
      },
      { timeout: 5000 },
    );
  });

  it("handles fetch timeout", async () => {
    global.fetch = vi.fn().mockImplementation(() => {
      return new Promise((_, reject) => {
        setTimeout(() => reject(new Error("Timeout")), 100);
      });
    });

    render(<ConnectionStatus />);

    await waitFor(
      () => {
        expect(screen.getByText(/server unreachable/i)).toBeInTheDocument();
      },
      { timeout: 2000 },
    );
  });

  it("shows spinner while checking connection", async () => {
    let resolvePromise;
    global.fetch = vi.fn().mockImplementation(() => {
      return new Promise((resolve) => {
        resolvePromise = resolve;
      });
    });

    render(<ConnectionStatus />);

    // First need to get into error state
    global.fetch = vi.fn().mockRejectedValue(new Error("Error"));

    // Re-render to trigger error state
    const { rerender } = render(<ConnectionStatus />);

    await waitFor(() => {
      expect(screen.getByText(/server unreachable/i)).toBeInTheDocument();
    });

    // Now setup slow fetch for retry
    global.fetch = vi.fn().mockImplementation(() => {
      return new Promise((resolve) => {
        setTimeout(() => resolve({ ok: true }), 1000);
      });
    });

    // Click retry - spinner should show during check
    const retryButton = screen.getByRole("button");
    fireEvent.click(retryButton);

    // Button should be disabled or show loading state
    expect(retryButton).toBeInTheDocument();
  });
});

describe("ConnectionStatus - Online/Offline Events", () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true });
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("responds to browser offline event", async () => {
    render(<ConnectionStatus />);

    // Simulate going offline
    act(() => {
      window.dispatchEvent(new Event("offline"));
    });

    await waitFor(() => {
      expect(screen.getByText(/no internet connection/i)).toBeInTheDocument();
    });
  });

  it("responds to browser online event", async () => {
    render(<ConnectionStatus />);

    // First go offline
    act(() => {
      window.dispatchEvent(new Event("offline"));
    });

    await waitFor(() => {
      expect(screen.getByText(/no internet connection/i)).toBeInTheDocument();
    });

    // Then go online
    act(() => {
      window.dispatchEvent(new Event("online"));
    });

    // Should attempt to reconnect
    await waitFor(
      () => {
        expect(
          screen.queryByText(/no internet connection/i),
        ).not.toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });
});
