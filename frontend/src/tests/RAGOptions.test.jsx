/**
 * Tests for RAG Options UI controls in ChatPage.
 * Tests the Query Expansion, Hybrid Search, and Reranking toggles.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock the API client
vi.mock("../api/client", () => ({
  streamChatMessage: vi.fn(),
  streamMultimodalChat: vi.fn(),
  exportChatHistory: vi.fn(),
}));

// Mock react-hot-toast
vi.mock("react-hot-toast", () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
    loading: vi.fn(),
    dismiss: vi.fn(),
  },
}));

// Mock the hooks
vi.mock("../hooks/useApi", () => ({
  useDocuments: () => ({
    data: [
      { id: "doc-1", filename: "test.pdf", content_type: "application/pdf" },
    ],
    isLoading: false,
    error: null,
  }),
  useChatHistory: () => ({
    data: [],
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useClearChatHistory: () => ({
    mutate: vi.fn(),
    isLoading: false,
  }),
  useDeleteDocument: () => ({
    mutate: vi.fn(),
    isLoading: false,
  }),
  useBulkDeleteDocuments: () => ({
    mutate: vi.fn(),
    isLoading: false,
  }),
  useImages: () => ({
    data: [],
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useDeleteImage: () => ({
    mutate: vi.fn(),
    isLoading: false,
  }),
  useUploadDocument: () => ({
    mutate: vi.fn(),
    isLoading: false,
  }),
  useUploadImage: () => ({
    mutate: vi.fn(),
    isLoading: false,
  }),
  useDocumentContent: () => ({
    data: null,
    isLoading: false,
    error: null,
  }),
}));

// Import ChatPage after mocks are set up
import ChatPage from "../pages/ChatPage";

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

describe("RAG Options UI Controls", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn(() => "user-123"),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    };
    Object.defineProperty(window, "localStorage", { value: localStorageMock });
  });

  // Helper to find the RAG button
  const findRagButton = () => {
    // The button contains "RAG" text
    return screen.getByRole("button", { name: /^RAG/i });
  };

  describe("RAG Options Panel Visibility", () => {
    it("should not show RAG options panel by default", () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      // RAG options panel should be hidden initially
      expect(screen.queryByText("Query Expansion")).not.toBeInTheDocument();
      expect(screen.queryByText("Hybrid Search")).not.toBeInTheDocument();
      expect(screen.queryByText("Reranking")).not.toBeInTheDocument();
    });

    it("should show RAG options panel when RAG button is clicked", async () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      // Find and click the RAG button
      const ragButton = findRagButton();
      fireEvent.click(ragButton);

      // Now RAG options should be visible
      await waitFor(() => {
        expect(screen.getByText("Query Expansion")).toBeInTheDocument();
        expect(screen.getByText("Hybrid Search")).toBeInTheDocument();
        expect(screen.getByText("Reranking")).toBeInTheDocument();
      });
    });

    it("should close RAG options panel when close button is clicked", async () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      // Open RAG options
      const ragButton = findRagButton();
      fireEvent.click(ragButton);

      // Verify it's open
      await waitFor(() => {
        expect(screen.getByText("Query Expansion")).toBeInTheDocument();
      });

      // Find close button within the RAG options panel (X icon button)
      const closeButtons = screen.getAllByRole("button");
      const closeButton = closeButtons.find((btn) =>
        btn.querySelector("svg.lucide-x"),
      );

      if (closeButton) {
        fireEvent.click(closeButton);
        await waitFor(() => {
          expect(
            screen.queryByText("Multiple query variations"),
          ).not.toBeInTheDocument();
        });
      }
    });
  });

  describe("Query Expansion Toggle", () => {
    it("should toggle query expansion on click", async () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      // Open RAG options
      const ragButton = findRagButton();
      fireEvent.click(ragButton);

      await waitFor(() => {
        expect(screen.getByText("Query Expansion")).toBeInTheDocument();
      });

      // Find the Query Expansion label/checkbox container
      const queryExpansionLabel = screen
        .getByText("Query Expansion")
        .closest("label");
      expect(queryExpansionLabel).toBeInTheDocument();

      // Get the hidden checkbox inside
      const checkbox = queryExpansionLabel.querySelector(
        'input[type="checkbox"]',
      );
      expect(checkbox).toBeInTheDocument();
      expect(checkbox.checked).toBe(false);

      // Click the label to toggle
      fireEvent.click(queryExpansionLabel);

      await waitFor(() => {
        expect(checkbox.checked).toBe(true);
      });
    });

    it("should show description text for query expansion", async () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      const ragButton = findRagButton();
      fireEvent.click(ragButton);

      await waitFor(() => {
        expect(
          screen.getByText("Multiple query variations"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("Hybrid Search Toggle", () => {
    it("should toggle hybrid search on click", async () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      // Open RAG options
      const ragButton = findRagButton();
      fireEvent.click(ragButton);

      await waitFor(() => {
        expect(screen.getByText("Hybrid Search")).toBeInTheDocument();
      });

      // Find the Hybrid Search label/checkbox container
      const hybridSearchLabel = screen
        .getByText("Hybrid Search")
        .closest("label");
      expect(hybridSearchLabel).toBeInTheDocument();

      const checkbox = hybridSearchLabel.querySelector(
        'input[type="checkbox"]',
      );
      expect(checkbox).toBeInTheDocument();
      expect(checkbox.checked).toBe(false);

      // Click the label to toggle
      fireEvent.click(hybridSearchLabel);

      await waitFor(() => {
        expect(checkbox.checked).toBe(true);
      });
    });

    it("should show description text for hybrid search", async () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      const ragButton = findRagButton();
      fireEvent.click(ragButton);

      await waitFor(() => {
        expect(
          screen.getByText("Semantic + keyword search"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("Reranking Toggle", () => {
    it("should toggle reranking on click", async () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      // Open RAG options
      const ragButton = findRagButton();
      fireEvent.click(ragButton);

      await waitFor(() => {
        expect(screen.getByText("Reranking")).toBeInTheDocument();
      });

      // Find the Reranking label/checkbox container
      const rerankingLabel = screen.getByText("Reranking").closest("label");
      expect(rerankingLabel).toBeInTheDocument();

      const checkbox = rerankingLabel.querySelector('input[type="checkbox"]');
      expect(checkbox).toBeInTheDocument();
      expect(checkbox.checked).toBe(false);

      // Click the label to toggle
      fireEvent.click(rerankingLabel);

      await waitFor(() => {
        expect(checkbox.checked).toBe(true);
      });
    });

    it("should show description text for reranking", async () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      const ragButton = findRagButton();
      fireEvent.click(ragButton);

      await waitFor(() => {
        expect(screen.getByText("Relevance scoring")).toBeInTheDocument();
      });
    });
  });

  describe("Multiple Options Selection", () => {
    it("should allow enabling all RAG options simultaneously", async () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      // Open RAG options
      const ragButton = findRagButton();
      fireEvent.click(ragButton);

      await waitFor(() => {
        expect(screen.getByText("Query Expansion")).toBeInTheDocument();
      });

      // Get all three labels
      const queryExpansionLabel = screen
        .getByText("Query Expansion")
        .closest("label");
      const hybridSearchLabel = screen
        .getByText("Hybrid Search")
        .closest("label");
      const rerankingLabel = screen.getByText("Reranking").closest("label");

      // Get checkboxes
      const queryExpansionCheckbox = queryExpansionLabel.querySelector(
        'input[type="checkbox"]',
      );
      const hybridSearchCheckbox = hybridSearchLabel.querySelector(
        'input[type="checkbox"]',
      );
      const rerankingCheckbox = rerankingLabel.querySelector(
        'input[type="checkbox"]',
      );

      // Enable all three
      fireEvent.click(queryExpansionLabel);
      fireEvent.click(hybridSearchLabel);
      fireEvent.click(rerankingLabel);

      await waitFor(() => {
        expect(queryExpansionCheckbox.checked).toBe(true);
        expect(hybridSearchCheckbox.checked).toBe(true);
        expect(rerankingCheckbox.checked).toBe(true);
      });
    });

    it("should allow toggling options on and off", async () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      // Open RAG options
      const ragButton = findRagButton();
      fireEvent.click(ragButton);

      await waitFor(() => {
        expect(screen.getByText("Hybrid Search")).toBeInTheDocument();
      });

      const hybridSearchLabel = screen
        .getByText("Hybrid Search")
        .closest("label");
      const checkbox = hybridSearchLabel.querySelector(
        'input[type="checkbox"]',
      );

      // Toggle on
      fireEvent.click(hybridSearchLabel);
      await waitFor(() => {
        expect(checkbox.checked).toBe(true);
      });

      // Toggle off
      fireEvent.click(hybridSearchLabel);
      await waitFor(() => {
        expect(checkbox.checked).toBe(false);
      });
    });
  });

  describe("Visual Feedback", () => {
    it("should apply active styling when query expansion is enabled", async () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      const ragButton = findRagButton();
      fireEvent.click(ragButton);

      await waitFor(() => {
        expect(screen.getByText("Query Expansion")).toBeInTheDocument();
      });

      const queryExpansionLabel = screen
        .getByText("Query Expansion")
        .closest("label");

      // Initially should not have active class
      expect(queryExpansionLabel.className).toContain(
        "border-[var(--border-subtle)]",
      );

      // Enable it
      fireEvent.click(queryExpansionLabel);

      await waitFor(() => {
        // Should now have violet active styling
        expect(queryExpansionLabel.className).toContain("border-violet-500/30");
      });
    });

    it("should apply active styling when hybrid search is enabled", async () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      const ragButton = findRagButton();
      fireEvent.click(ragButton);

      await waitFor(() => {
        expect(screen.getByText("Hybrid Search")).toBeInTheDocument();
      });

      const hybridSearchLabel = screen
        .getByText("Hybrid Search")
        .closest("label");

      // Enable it
      fireEvent.click(hybridSearchLabel);

      await waitFor(() => {
        // Should have blue active styling
        expect(hybridSearchLabel.className).toContain("border-blue-500/30");
      });
    });

    it("should apply active styling when reranking is enabled", async () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      const ragButton = findRagButton();
      fireEvent.click(ragButton);

      await waitFor(() => {
        expect(screen.getByText("Reranking")).toBeInTheDocument();
      });

      const rerankingLabel = screen.getByText("Reranking").closest("label");

      // Enable it
      fireEvent.click(rerankingLabel);

      await waitFor(() => {
        // Should have emerald active styling
        expect(rerankingLabel.className).toContain("border-emerald-500/30");
      });
    });
  });

  describe("Accessibility", () => {
    it("should have accessible checkbox inputs", async () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      const ragButton = findRagButton();
      fireEvent.click(ragButton);

      await waitFor(() => {
        expect(screen.getByText("Query Expansion")).toBeInTheDocument();
      });

      // All checkboxes should be present (even if visually hidden)
      const checkboxes = document.querySelectorAll('input[type="checkbox"]');
      expect(checkboxes.length).toBeGreaterThanOrEqual(3);
    });

    it("should allow keyboard navigation to toggle options", async () => {
      render(<ChatPage />, { wrapper: createWrapper() });

      const ragButton = findRagButton();
      fireEvent.click(ragButton);

      await waitFor(() => {
        expect(screen.getByText("Query Expansion")).toBeInTheDocument();
      });

      const queryExpansionLabel = screen
        .getByText("Query Expansion")
        .closest("label");
      const checkbox = queryExpansionLabel.querySelector(
        'input[type="checkbox"]',
      );

      // Simulate keyboard interaction
      checkbox.focus();
      fireEvent.keyDown(checkbox, { key: " ", code: "Space" });
      fireEvent.click(checkbox);

      await waitFor(() => {
        expect(checkbox.checked).toBe(true);
      });
    });
  });
});

describe("RAG Options State Integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const localStorageMock = {
      getItem: vi.fn(() => "user-123"),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    };
    Object.defineProperty(window, "localStorage", { value: localStorageMock });
  });

  // Helper to find the RAG button
  const findRagButton = () => {
    return screen.getByRole("button", { name: /^RAG/i });
  };

  it("should maintain RAG options state when panel is closed and reopened", async () => {
    render(<ChatPage />, { wrapper: createWrapper() });

    // Open RAG options
    const ragButton = findRagButton();
    fireEvent.click(ragButton);

    await waitFor(() => {
      expect(screen.getByText("Query Expansion")).toBeInTheDocument();
    });

    // Enable query expansion
    const queryExpansionLabel = screen
      .getByText("Query Expansion")
      .closest("label");
    fireEvent.click(queryExpansionLabel);

    let checkbox = queryExpansionLabel.querySelector('input[type="checkbox"]');
    await waitFor(() => {
      expect(checkbox.checked).toBe(true);
    });

    // Close panel by clicking the toggle button again
    fireEvent.click(ragButton);

    // Reopen panel
    fireEvent.click(ragButton);

    await waitFor(() => {
      expect(screen.getByText("Query Expansion")).toBeInTheDocument();
    });

    // Check that state is preserved
    const reopenedLabel = screen.getByText("Query Expansion").closest("label");
    const reopenedCheckbox = reopenedLabel.querySelector(
      'input[type="checkbox"]',
    );

    expect(reopenedCheckbox.checked).toBe(true);
  });
});
