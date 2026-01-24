/**
 * Tests for KeyboardShortcuts component.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import KeyboardShortcuts from "../components/KeyboardShortcuts";

describe("KeyboardShortcuts Component", () => {
  beforeEach(() => {
    // Reset body overflow before each test
    document.body.style.overflow = "";
  });

  afterEach(() => {
    document.body.style.overflow = "";
  });

  it("does not render initially", () => {
    render(<KeyboardShortcuts />);
    expect(
      screen.queryByRole("heading", { name: /keyboard shortcuts/i }),
    ).not.toBeInTheDocument();
  });

  it("opens when ? key is pressed", async () => {
    render(<KeyboardShortcuts />);

    fireEvent.keyDown(document, { key: "?" });

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /keyboard shortcuts/i }),
      ).toBeInTheDocument();
    });
  });

  it("shows all shortcut categories", async () => {
    render(<KeyboardShortcuts />);
    fireEvent.keyDown(document, { key: "?" });

    await waitFor(() => {
      expect(screen.getByText("Chat")).toBeInTheDocument();
      expect(screen.getByText("Navigation")).toBeInTheDocument();
      expect(screen.getByText("General")).toBeInTheDocument();
    });
  });

  it("displays export chat history shortcut", async () => {
    render(<KeyboardShortcuts />);
    fireEvent.keyDown(document, { key: "?" });

    await waitFor(() => {
      expect(screen.getByText(/export chat history/i)).toBeInTheDocument();
    });
  });

  it("displays clear conversation shortcut", async () => {
    render(<KeyboardShortcuts />);
    fireEvent.keyDown(document, { key: "?" });

    await waitFor(() => {
      expect(screen.getByText(/clear conversation/i)).toBeInTheDocument();
    });
  });

  it("closes on Escape key", async () => {
    render(<KeyboardShortcuts />);

    // Open
    fireEvent.keyDown(document, { key: "?" });
    await waitFor(() => {
      // Use role heading to get the specific title
      expect(
        screen.getByRole("heading", { name: /keyboard shortcuts/i }),
      ).toBeInTheDocument();
    });

    // Close
    fireEvent.keyDown(document, { key: "Escape" });
    await waitFor(() => {
      expect(
        screen.queryByRole("heading", { name: /keyboard shortcuts/i }),
      ).not.toBeInTheDocument();
    });
  });

  it("closes when backdrop is clicked", async () => {
    render(<KeyboardShortcuts />);

    // Open
    fireEvent.keyDown(document, { key: "?" });
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /keyboard shortcuts/i }),
      ).toBeInTheDocument();
    });

    // Click backdrop (the dark overlay)
    const backdrop = document.querySelector(".bg-black\\/80");
    if (backdrop) {
      fireEvent.click(backdrop);
    }

    await waitFor(() => {
      expect(
        screen.queryByRole("heading", { name: /keyboard shortcuts/i }),
      ).not.toBeInTheDocument();
    });
  });

  it("closes when X button is clicked", async () => {
    render(<KeyboardShortcuts />);

    // Open
    fireEvent.keyDown(document, { key: "?" });
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /keyboard shortcuts/i }),
      ).toBeInTheDocument();
    });

    // Click close button
    const closeButton = screen.getByRole("button");
    fireEvent.click(closeButton);

    await waitFor(() => {
      expect(
        screen.queryByRole("heading", { name: /keyboard shortcuts/i }),
      ).not.toBeInTheDocument();
    });
  });

  it("does not open ? when typing in input", () => {
    render(
      <div>
        <KeyboardShortcuts />
        <input type="text" data-testid="test-input" />
      </div>,
    );

    const input = screen.getByTestId("test-input");
    input.focus();

    fireEvent.keyDown(input, { key: "?" });

    expect(screen.queryByText(/keyboard shortcuts/i)).not.toBeInTheDocument();
  });

  it("does not open ? when typing in textarea", () => {
    render(
      <div>
        <KeyboardShortcuts />
        <textarea data-testid="test-textarea" />
      </div>,
    );

    const textarea = screen.getByTestId("test-textarea");
    textarea.focus();

    fireEvent.keyDown(textarea, { key: "?" });

    expect(screen.queryByText(/keyboard shortcuts/i)).not.toBeInTheDocument();
  });

  it("prevents body scroll when open", async () => {
    render(<KeyboardShortcuts />);

    fireEvent.keyDown(document, { key: "?" });

    await waitFor(() => {
      expect(document.body.style.overflow).toBe("hidden");
    });
  });

  it("restores body scroll when closed", async () => {
    render(<KeyboardShortcuts />);

    // Open
    fireEvent.keyDown(document, { key: "?" });
    await waitFor(() => {
      expect(document.body.style.overflow).toBe("hidden");
    });

    // Close
    fireEvent.keyDown(document, { key: "Escape" });
    await waitFor(() => {
      expect(document.body.style.overflow).toBe("unset");
    });
  });

  it("shows keyboard badge styling", async () => {
    render(<KeyboardShortcuts />);
    fireEvent.keyDown(document, { key: "?" });

    await waitFor(() => {
      const kbdElements = document.querySelectorAll("kbd");
      expect(kbdElements.length).toBeGreaterThan(0);
    });
  });
});
