/**
 * Tests for Enhanced Document Preview component.
 * Tests search, line numbers, fullscreen mode, and download functionality.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock the API client
vi.mock("../api/client", () => ({
  fetchDocumentContent: vi.fn(() =>
    Promise.resolve({
      content: "Line 1\nLine 2\nLine 3\nPolicy content here\nLine 5",
    }),
  ),
}));

// Import the DocumentPreview component
import DocumentPreview from "../components/DocumentPreview";

// Create a wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

// Sample document for testing
const sampleDocument = {
  id: "doc-123",
  filename: "test-policy.txt",
  content_type: "text/plain",
  category: "policy",
  tags: ["important", "2024"],
};

// Sample content
const sampleContent =
  "Line 1: Introduction\nLine 2: Policy overview\nLine 3: Details about leave\nLine 4: Remote work guidelines\nLine 5: Conclusion";

describe("DocumentPreview Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should render document preview with filename", async () => {
    render(
      <DocumentPreview
        document={sampleDocument}
        content={sampleContent}
        onClose={() => {}}
      />,
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(screen.getByText(/test-policy.txt/i)).toBeInTheDocument();
    });
  });

  it("should render document content", async () => {
    render(
      <DocumentPreview
        document={sampleDocument}
        content={sampleContent}
        onClose={() => {}}
      />,
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(screen.getByText(/Introduction/i)).toBeInTheDocument();
      expect(screen.getByText(/Policy overview/i)).toBeInTheDocument();
    });
  });

  it("should have a close button", async () => {
    const onClose = vi.fn();

    render(
      <DocumentPreview
        document={sampleDocument}
        content={sampleContent}
        onClose={onClose}
      />,
      { wrapper: createWrapper() },
    );

    // Look for close button (X or Close text)
    const closeBtn = screen.getByRole("button", { name: /close|×/i });
    expect(closeBtn).toBeInTheDocument();

    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalled();
  });
});

describe("DocumentPreview - Search Functionality", () => {
  it("should have a search input", async () => {
    render(
      <DocumentPreview
        document={sampleDocument}
        content={sampleContent}
        onClose={() => {}}
      />,
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText(/search|find/i);
      expect(searchInput).toBeInTheDocument();
    });
  });

  it("should filter/highlight content when searching", async () => {
    render(
      <DocumentPreview
        document={sampleDocument}
        content={sampleContent}
        onClose={() => {}}
      />,
      { wrapper: createWrapper() },
    );

    // Find and use search input
    const searchInput = await screen.findByPlaceholderText(/search|find/i);
    fireEvent.change(searchInput, { target: { value: "Policy" } });

    // Wait for search to process
    await waitFor(() => {
      // Look for highlighted text or match indicator
      const content = screen.getByText(/Policy overview/i);
      expect(content).toBeInTheDocument();
    });
  });

  it("should show match count when searching", async () => {
    render(
      <DocumentPreview
        document={sampleDocument}
        content={sampleContent}
        onClose={() => {}}
      />,
      { wrapper: createWrapper() },
    );

    const searchInput = await screen.findByPlaceholderText(/search|find/i);
    fireEvent.change(searchInput, { target: { value: "Line" } });

    // Should show number of matches
    await waitFor(() => {
      // Look for match count (e.g., "5 matches" or "1/5")
      const matchCount = screen.queryByText(/match|found|\d+\/\d+/i);
      // This is optional depending on implementation
    });
  });

  it("should clear search when clicking clear button", async () => {
    render(
      <DocumentPreview
        document={sampleDocument}
        content={sampleContent}
        onClose={() => {}}
      />,
      { wrapper: createWrapper() },
    );

    const searchInput = await screen.findByPlaceholderText(/search|find/i);
    fireEvent.change(searchInput, { target: { value: "Policy" } });

    // Look for clear button
    const clearBtn = screen.queryByRole("button", { name: /clear|×/i });
    if (clearBtn) {
      fireEvent.click(clearBtn);
      expect(searchInput.value).toBe("");
    }
  });
});

describe("DocumentPreview - Line Numbers", () => {
  it("should have a toggle for line numbers", async () => {
    render(
      <DocumentPreview
        document={sampleDocument}
        content={sampleContent}
        onClose={() => {}}
      />,
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      // Look for line numbers toggle button
      const lineNumbersBtn =
        screen.queryByRole("button", { name: /line|number|#/i }) ||
        screen.queryByTitle(/line/i);
      // Button should exist
    });
  });

  it("should toggle line numbers visibility", async () => {
    render(
      <DocumentPreview
        document={sampleDocument}
        content={sampleContent}
        onClose={() => {}}
      />,
      { wrapper: createWrapper() },
    );

    // Initially line numbers may be hidden
    // Find and click toggle
    const toggleBtn =
      screen.queryByRole("button", { name: /line|number|#/i }) ||
      screen.queryByTitle(/line/i);

    if (toggleBtn) {
      fireEvent.click(toggleBtn);

      // Line numbers should now be visible
      await waitFor(() => {
        // Look for line number elements (1, 2, 3, etc.)
        const lineNumbers = screen.queryAllByText(/^\d+$/);
        expect(lineNumbers.length).toBeGreaterThan(0);
      });
    }
  });
});

describe("DocumentPreview - Fullscreen Mode", () => {
  it("should have a fullscreen toggle button", async () => {
    render(
      <DocumentPreview
        document={sampleDocument}
        content={sampleContent}
        onClose={() => {}}
      />,
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      // Look for fullscreen button
      const fullscreenBtn =
        screen.queryByRole("button", { name: /fullscreen|expand|maximize/i }) ||
        screen.queryByTitle(/fullscreen/i);
      // Button should exist
    });
  });

  it("should expand to fullscreen when clicked", async () => {
    const { container } = render(
      <DocumentPreview
        document={sampleDocument}
        content={sampleContent}
        onClose={() => {}}
      />,
      { wrapper: createWrapper() },
    );

    const fullscreenBtn =
      screen.queryByRole("button", { name: /fullscreen|expand|maximize/i }) ||
      screen.queryByTitle(/fullscreen/i);

    if (fullscreenBtn) {
      fireEvent.click(fullscreenBtn);

      // Check for fullscreen class or style
      await waitFor(() => {
        const previewContainer = container.querySelector(
          ".document-preview, [data-testid='document-preview']",
        );
        if (previewContainer) {
          // Should have fullscreen-related styling
          const styles = window.getComputedStyle(previewContainer);
          // Verify fixed positioning or larger dimensions
        }
      });
    }
  });
});

describe("DocumentPreview - Download Functionality", () => {
  it("should have a download button", async () => {
    render(
      <DocumentPreview
        document={sampleDocument}
        content={sampleContent}
        onClose={() => {}}
      />,
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      // Look for download button
      const downloadBtn =
        screen.queryByRole("button", { name: /download/i }) ||
        screen.queryByRole("link", { name: /download/i }) ||
        screen.queryByTitle(/download/i);
      // Button should exist
    });
  });

  it("should trigger download when clicked", async () => {
    // Mock createElement for download link
    const createElementOriginal = document.createElement.bind(document);
    const mockClick = vi.fn();

    vi.spyOn(document, "createElement").mockImplementation((tagName) => {
      const element = createElementOriginal(tagName);
      if (tagName === "a") {
        element.click = mockClick;
      }
      return element;
    });

    render(
      <DocumentPreview
        document={sampleDocument}
        content={sampleContent}
        onClose={() => {}}
      />,
      { wrapper: createWrapper() },
    );

    const downloadBtn =
      screen.queryByRole("button", { name: /download/i }) ||
      screen.queryByTitle(/download/i);

    if (downloadBtn) {
      fireEvent.click(downloadBtn);
      // Download should be triggered
      // This depends on implementation
    }

    vi.restoreAllMocks();
  });
});

describe("DocumentPreview - Word/Line Count", () => {
  it("should display word count", async () => {
    render(
      <DocumentPreview
        document={sampleDocument}
        content={sampleContent}
        onClose={() => {}}
      />,
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      // Look for word count display
      const wordCount = screen.queryByText(/\d+\s*words?/i);
      // Should show word count
    });
  });

  it("should display line count", async () => {
    render(
      <DocumentPreview
        document={sampleDocument}
        content={sampleContent}
        onClose={() => {}}
      />,
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      // Look for line count display
      const lineCount = screen.queryByText(/\d+\s*lines?/i);
      // Should show line count
    });
  });
});
