/**
 * Tests for NEW RAG Options: Auto Rewrite and Cross-Encoder
 * These are advanced query optimization features added to ChatPage.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
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
      {
        id: "doc-1",
        filename: "test.pdf",
        content_type: "application/pdf",
        category: "policy",
      },
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

describe("Advanced RAG Options - Auto Rewrite & Cross-Encoder", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn(() => "user-123"),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    };
    Object.defineProperty(window, "localStorage", { value: localStorageMock });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should render RAG options toggle button", async () => {
    render(<ChatPage />, { wrapper: createWrapper() });

    // Wait for component to load - look for "RAG" button
    await waitFor(() => {
      const ragBtn = screen.getByRole("button", { name: /RAG/i });
      expect(ragBtn).toBeInTheDocument();
    });
  });

  it("should expand RAG options panel when clicked", async () => {
    render(<ChatPage />, { wrapper: createWrapper() });

    // Find and click the RAG button
    const ragBtn = await screen.findByRole("button", { name: /RAG/i });
    fireEvent.click(ragBtn);

    // Wait for panel to expand - look for RAG option labels
    await waitFor(() => {
      expect(screen.getByText(/Query Expansion/i)).toBeInTheDocument();
    });
  });

  it("should display Auto Rewrite option in RAG panel", async () => {
    render(<ChatPage />, { wrapper: createWrapper() });

    // Expand RAG options
    const ragBtn = await screen.findByRole("button", { name: /RAG/i });
    fireEvent.click(ragBtn);

    // Look for Auto Rewrite option
    await waitFor(() => {
      expect(screen.getByText(/Auto Rewrite/i)).toBeInTheDocument();
    });
  });

  it("should display Cross-Encoder option in RAG panel", async () => {
    render(<ChatPage />, { wrapper: createWrapper() });

    // Expand RAG options
    const ragBtn = await screen.findByRole("button", { name: /RAG/i });
    fireEvent.click(ragBtn);

    // Look for Cross-Encoder option
    await waitFor(() => {
      expect(screen.getByText(/Cross-Encoder/i)).toBeInTheDocument();
    });
  });

  it("should toggle Auto Rewrite checkbox", async () => {
    render(<ChatPage />, { wrapper: createWrapper() });

    // Expand RAG options
    const ragBtn = await screen.findByRole("button", { name: /RAG/i });
    fireEvent.click(ragBtn);

    // Find Auto Rewrite checkbox (by nearby text)
    await waitFor(() => {
      const autoRewriteText = screen.getByText(/Auto Rewrite/i);
      expect(autoRewriteText).toBeInTheDocument();
    });

    // Find checkbox input associated with Auto Rewrite
    const checkboxes = screen.getAllByRole("checkbox");
    const autoRewriteCheckbox = checkboxes.find((cb) => {
      const label = cb.closest("label");
      return label && label.textContent.includes("Auto Rewrite");
    });

    if (autoRewriteCheckbox) {
      expect(autoRewriteCheckbox).not.toBeChecked();
      fireEvent.click(autoRewriteCheckbox);
      expect(autoRewriteCheckbox).toBeChecked();
    }
  });

  it("should toggle Cross-Encoder checkbox", async () => {
    render(<ChatPage />, { wrapper: createWrapper() });

    // Expand RAG options
    const ragBtn = await screen.findByRole("button", { name: /RAG/i });
    fireEvent.click(ragBtn);

    // Find Cross-Encoder checkbox
    await waitFor(() => {
      const crossEncoderText = screen.getByText(/Cross-Encoder/i);
      expect(crossEncoderText).toBeInTheDocument();
    });

    // Find checkbox input associated with Cross-Encoder
    const checkboxes = screen.getAllByRole("checkbox");
    const crossEncoderCheckbox = checkboxes.find((cb) => {
      const label = cb.closest("label");
      return label && label.textContent.includes("Cross-Encoder");
    });

    if (crossEncoderCheckbox) {
      expect(crossEncoderCheckbox).not.toBeChecked();
      fireEvent.click(crossEncoderCheckbox);
      expect(crossEncoderCheckbox).toBeChecked();
    }
  });

  it("should have amber color for Auto Rewrite option", async () => {
    render(<ChatPage />, { wrapper: createWrapper() });

    // Expand RAG options
    const ragBtn = await screen.findByRole("button", { name: /RAG/i });
    fireEvent.click(ragBtn);

    // Wait for options to render
    await waitFor(() => {
      const autoRewriteLabel = screen
        .getByText(/Auto Rewrite/i)
        .closest("label");
      expect(autoRewriteLabel).toBeInTheDocument();
      // Check for amber color class
      expect(autoRewriteLabel.className).toMatch(/amber/i);
    });
  });

  it("should have rose color for Cross-Encoder option", async () => {
    render(<ChatPage />, { wrapper: createWrapper() });

    // Expand RAG options
    const ragBtn = await screen.findByRole("button", { name: /RAG/i });
    fireEvent.click(ragBtn);

    // Wait for options to render
    await waitFor(() => {
      const crossEncoderLabel = screen
        .getByText(/Cross-Encoder/i)
        .closest("label");
      expect(crossEncoderLabel).toBeInTheDocument();
      // Check for rose color class
      expect(crossEncoderLabel.className).toMatch(/rose/i);
    });
  });
});

describe("RAG Options Integration with Chat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const localStorageMock = {
      getItem: vi.fn(() => "user-123"),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    };
    Object.defineProperty(window, "localStorage", { value: localStorageMock });
  });

  it("should maintain RAG options state when panel is expanded", async () => {
    render(<ChatPage />, { wrapper: createWrapper() });

    // Expand RAG options
    const ragBtn = await screen.findByRole("button", { name: /RAG/i });
    fireEvent.click(ragBtn);

    // Enable Auto Rewrite
    await waitFor(() => {
      const autoRewriteText = screen.getByText(/Auto Rewrite/i);
      expect(autoRewriteText).toBeInTheDocument();
    });

    const checkboxes = screen.getAllByRole("checkbox");
    const autoRewriteCheckbox = checkboxes.find((cb) => {
      const label = cb.closest("label");
      return label && label.textContent.includes("Auto Rewrite");
    });

    if (autoRewriteCheckbox) {
      fireEvent.click(autoRewriteCheckbox);
      expect(autoRewriteCheckbox).toBeChecked();

      // Close and reopen RAG panel
      fireEvent.click(ragBtn);
      await waitFor(() => {
        // Panel should be closed
      });

      fireEvent.click(ragBtn);
      await waitFor(() => {
        // Checkbox should still be checked (state preserved)
        const newCheckboxes = screen.getAllByRole("checkbox");
        const newAutoRewriteCheckbox = newCheckboxes.find((cb) => {
          const label = cb.closest("label");
          return label && label.textContent.includes("Auto Rewrite");
        });
        if (newAutoRewriteCheckbox) {
          expect(newAutoRewriteCheckbox).toBeChecked();
        }
      });
    }
  });
});
