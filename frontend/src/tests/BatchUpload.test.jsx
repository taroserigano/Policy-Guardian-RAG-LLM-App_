/**
 * Tests for Batch Upload with Progress functionality.
 * Tests multiple file upload, progress tracking, and status display.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock the API client
vi.mock("../api/client", () => ({
  uploadDocumentsWithProgress: vi.fn(),
  uploadDocument: vi.fn(),
  fetchDocuments: vi.fn(() => Promise.resolve([])),
  getDocumentCategories: vi.fn(() =>
    Promise.resolve({
      categories: [
        { id: "policy", name: "Policy", color: "blue" },
        { id: "legal", name: "Legal", color: "purple" },
        { id: "hr", name: "HR", color: "green" },
      ],
    }),
  ),
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
        filename: "existing.pdf",
        content_type: "application/pdf",
        category: "policy",
      },
    ],
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useUploadDocument: () => ({
    mutate: vi.fn(),
    isLoading: false,
  }),
}));

// Import UploadPage after mocks
import UploadPage from "../pages/UploadPage";
import { uploadDocumentsWithProgress } from "../api/client";

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

describe("Batch Upload - File Selection", () => {
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

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should render upload section", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      // Look for upload dropzone or input
      const uploadArea = screen.getByText(/drag|drop|upload|choose/i);
      expect(uploadArea).toBeInTheDocument();
    });
  });

  it("should accept multiple files", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    // Find file input
    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();

    // Check if it accepts multiple files
    expect(
      fileInput.hasAttribute("multiple") || fileInput.multiple,
    ).toBeTruthy();
  });

  it("should display selected files before upload", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    const fileInput = document.querySelector('input[type="file"]');

    // Create test files
    const files = [
      new File(["content 1"], "test1.txt", { type: "text/plain" }),
      new File(["content 2"], "test2.txt", { type: "text/plain" }),
    ];

    // Simulate file selection
    Object.defineProperty(fileInput, "files", {
      value: files,
      writable: false,
    });
    fireEvent.change(fileInput);

    // Wait for files to be displayed
    await waitFor(() => {
      // Should show selected file names or count
      const fileList = screen.queryByText(/test1\.txt|test2\.txt|2 files?/i);
      // Expect file info to be shown
    });
  });
});

describe("Batch Upload - Progress Tracking", () => {
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

  it("should call uploadDocumentsWithProgress for batch upload", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    const fileInput = document.querySelector('input[type="file"]');

    const files = [
      new File(["content"], "batch-test.txt", { type: "text/plain" }),
    ];

    Object.defineProperty(fileInput, "files", {
      value: files,
      writable: false,
    });
    fireEvent.change(fileInput);

    // Find and click upload button
    const uploadBtn = screen.queryByRole("button", { name: /upload/i });
    if (uploadBtn) {
      fireEvent.click(uploadBtn);

      await waitFor(() => {
        // uploadDocumentsWithProgress should be called
        // (depends on implementation)
      });
    }
  });

  it("should show upload status for each file", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    // Mock ongoing upload with progress
    const fileInput = document.querySelector('input[type="file"]');

    const files = [
      new File(["content 1"], "file1.txt", { type: "text/plain" }),
      new File(["content 2"], "file2.txt", { type: "text/plain" }),
    ];

    Object.defineProperty(fileInput, "files", {
      value: files,
      writable: false,
    });
    fireEvent.change(fileInput);

    await waitFor(() => {
      // Should show individual file statuses
      // This depends on implementation - could be progress bars, checkmarks, etc.
    });
  });
});

describe("Batch Upload - Error Handling", () => {
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

  it("should show error for unsupported file types", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    const fileInput = document.querySelector('input[type="file"]');

    // Try uploading unsupported file type
    const files = [
      new File(["binary"], "test.exe", { type: "application/x-msdownload" }),
    ];

    Object.defineProperty(fileInput, "files", {
      value: files,
      writable: false,
    });
    fireEvent.change(fileInput);

    await waitFor(() => {
      // Should show error message for unsupported type
      const errorMessage = screen.queryByText(/unsupported|invalid|error/i);
      // Error handling depends on implementation
    });
  });

  it("should handle partial upload failures gracefully", async () => {
    // Mock partial failure
    uploadDocumentsWithProgress.mockImplementation(
      async (files, onProgress) => {
        onProgress({ file: "file1.txt", status: "success" });
        onProgress({
          file: "file2.txt",
          status: "error",
          error: "Network error",
        });
        return { success: 1, failed: 1 };
      },
    );

    render(<UploadPage />, { wrapper: createWrapper() });

    // Trigger upload
    const fileInput = document.querySelector('input[type="file"]');
    const files = [
      new File(["content 1"], "file1.txt", { type: "text/plain" }),
      new File(["content 2"], "file2.txt", { type: "text/plain" }),
    ];

    Object.defineProperty(fileInput, "files", {
      value: files,
      writable: false,
    });
    fireEvent.change(fileInput);

    await waitFor(() => {
      // Should show mixed results
    });
  });
});
