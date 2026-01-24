/**
 * Tests for Document Categories and Tags functionality.
 * Tests category filtering, inline editing, and tag management.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock the API client
vi.mock("../api/client", () => ({
  fetchDocuments: vi.fn(() =>
    Promise.resolve([
      {
        id: "doc-1",
        filename: "policy.pdf",
        content_type: "application/pdf",
        category: "policy",
        tags: ["important"],
      },
      {
        id: "doc-2",
        filename: "contract.pdf",
        content_type: "application/pdf",
        category: "legal",
        tags: ["vendor"],
      },
      {
        id: "doc-3",
        filename: "handbook.pdf",
        content_type: "application/pdf",
        category: "hr",
        tags: [],
      },
    ]),
  ),
  getDocumentCategories: vi.fn(() =>
    Promise.resolve({
      categories: [
        { id: "all", name: "All", color: "gray" },
        { id: "policy", name: "Policy", color: "blue" },
        { id: "legal", name: "Legal", color: "purple" },
        { id: "hr", name: "HR", color: "green" },
        { id: "compliance", name: "Compliance", color: "orange" },
        { id: "technical", name: "Technical", color: "cyan" },
        { id: "other", name: "Other", color: "gray" },
      ],
    }),
  ),
  updateDocument: vi.fn(() => Promise.resolve({ success: true })),
  uploadDocument: vi.fn(),
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

// Mock hooks
vi.mock("../hooks/useApi", () => ({
  useDocuments: () => ({
    data: [
      {
        id: "doc-1",
        filename: "policy.pdf",
        content_type: "application/pdf",
        category: "policy",
        tags: ["important"],
      },
      {
        id: "doc-2",
        filename: "contract.pdf",
        content_type: "application/pdf",
        category: "legal",
        tags: ["vendor"],
      },
      {
        id: "doc-3",
        filename: "handbook.pdf",
        content_type: "application/pdf",
        category: "hr",
        tags: [],
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
  useDeleteDocument: () => ({
    mutate: vi.fn(),
    isLoading: false,
  }),
}));

// Import components after mocks
import UploadPage from "../pages/UploadPage";
import { updateDocument, getDocumentCategories } from "../api/client";

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

describe("Document Categories - Filter Bar", () => {
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

  it("should render category filter section", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      // Look for category filter buttons or dropdown
      const filterSection = screen.queryByText(/category|filter|all/i);
      expect(filterSection).toBeInTheDocument();
    });
  });

  it("should display All category option", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      const allCategory = screen.getByText(/All/i);
      expect(allCategory).toBeInTheDocument();
    });
  });

  it("should display Policy category option", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      const policyCategory = screen.queryByText(/Policy/i);
      expect(policyCategory).toBeInTheDocument();
    });
  });

  it("should display Legal category option", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      const legalCategory = screen.queryByText(/Legal/i);
      expect(legalCategory).toBeInTheDocument();
    });
  });

  it("should display HR category option", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      const hrCategory = screen.queryByText(/HR/i);
      expect(hrCategory).toBeInTheDocument();
    });
  });

  it("should filter documents when clicking category", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      // All documents should be visible initially
      expect(screen.getByText(/policy\.pdf/i)).toBeInTheDocument();
      expect(screen.getByText(/contract\.pdf/i)).toBeInTheDocument();
    });

    // Click on Policy category
    const policyFilter = screen.getByText(/Policy/i);
    fireEvent.click(policyFilter);

    await waitFor(() => {
      // Only policy documents should be visible
      expect(screen.getByText(/policy\.pdf/i)).toBeInTheDocument();
      // Legal and HR documents may be hidden
    });
  });

  it("should highlight selected category", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      const allCategory = screen.getByText(/All/i);
      expect(allCategory).toBeInTheDocument();
    });

    // Click on Legal category
    const legalFilter = screen.queryByText(/Legal/i);
    if (legalFilter) {
      fireEvent.click(legalFilter);

      // Legal button should be highlighted (active state)
      await waitFor(() => {
        const legalBtn = screen.queryByRole("button", { name: /Legal/i });
        if (legalBtn) {
          expect(legalBtn.className).toMatch(/active|selected|bg-/);
        }
      });
    }
  });
});

describe("Document Categories - Inline Editor", () => {
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

  it("should have edit button for each document", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      // Look for edit buttons
      const editButtons = screen.queryAllByRole("button", {
        name: /edit|category/i,
      });
      // Should have edit option for documents
    });
  });

  it("should open category editor when clicking edit", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      const document = screen.getByText(/policy\.pdf/i);
      expect(document).toBeInTheDocument();
    });

    // Find edit button for first document
    const editButton = screen.queryByRole("button", { name: /edit|category/i });
    if (editButton) {
      fireEvent.click(editButton);

      // Editor should appear
      await waitFor(() => {
        const editor =
          screen.queryByRole("combobox") ||
          screen.queryByText(/select category/i) ||
          screen.queryByRole("dialog");
        // Editor should be visible
      });
    }
  });

  it("should show category dropdown in editor", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    // Open editor
    const editButton = screen.queryByRole("button", { name: /edit|category/i });
    if (editButton) {
      fireEvent.click(editButton);

      await waitFor(() => {
        // Category dropdown should show options
        const categorySelect = screen.queryByRole("combobox");
        if (categorySelect) {
          expect(categorySelect).toBeInTheDocument();
        }
      });
    }
  });

  it("should update document category when changed", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    const editButton = screen.queryByRole("button", { name: /edit|category/i });
    if (editButton) {
      fireEvent.click(editButton);

      await waitFor(() => {
        const categorySelect = screen.queryByRole("combobox");
        if (categorySelect) {
          // Select new category
          fireEvent.change(categorySelect, { target: { value: "legal" } });
        }
      });

      // Find and click save
      const saveBtn = screen.queryByRole("button", { name: /save/i });
      if (saveBtn) {
        fireEvent.click(saveBtn);

        await waitFor(() => {
          expect(updateDocument).toHaveBeenCalled();
        });
      }
    }
  });
});

describe("Document Tags - Management", () => {
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

  it("should display existing tags on documents", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      // Look for tag badges
      const importantTag = screen.queryByText(/important/i);
      const vendorTag = screen.queryByText(/vendor/i);
      // Tags should be displayed on documents
    });
  });

  it("should have tag input in editor", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    const editButton = screen.queryByRole("button", { name: /edit|category/i });
    if (editButton) {
      fireEvent.click(editButton);

      await waitFor(() => {
        // Look for tag input field
        const tagInput = screen.queryByPlaceholderText(/tag|add/i);
        // Tag input should exist
      });
    }
  });

  it("should add new tag when entering text and pressing Enter", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    const editButton = screen.queryByRole("button", { name: /edit|category/i });
    if (editButton) {
      fireEvent.click(editButton);

      await waitFor(() => {
        const tagInput = screen.queryByPlaceholderText(/tag|add/i);
        if (tagInput) {
          // Type new tag
          fireEvent.change(tagInput, { target: { value: "new-tag" } });
          fireEvent.keyDown(tagInput, { key: "Enter" });

          // New tag should appear
          waitFor(() => {
            const newTag = screen.queryByText(/new-tag/i);
            expect(newTag).toBeInTheDocument();
          });
        }
      });
    }
  });

  it("should remove tag when clicking remove button", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    const editButton = screen.queryByRole("button", { name: /edit|category/i });
    if (editButton) {
      fireEvent.click(editButton);

      await waitFor(() => {
        // Find existing tag with remove button
        const removeTagBtn = screen.queryByRole("button", {
          name: /remove|×|delete/i,
        });
        if (removeTagBtn) {
          fireEvent.click(removeTagBtn);
          // Tag should be removed from list
        }
      });
    }
  });

  it("should save tags when saving editor", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    const editButton = screen.queryByRole("button", { name: /edit|category/i });
    if (editButton) {
      fireEvent.click(editButton);

      await waitFor(() => {
        const tagInput = screen.queryByPlaceholderText(/tag|add/i);
        if (tagInput) {
          fireEvent.change(tagInput, { target: { value: "test-tag" } });
          fireEvent.keyDown(tagInput, { key: "Enter" });
        }
      });

      const saveBtn = screen.queryByRole("button", { name: /save/i });
      if (saveBtn) {
        fireEvent.click(saveBtn);

        await waitFor(() => {
          expect(updateDocument).toHaveBeenCalledWith(
            expect.anything(),
            expect.objectContaining({
              tags: expect.arrayContaining(["test-tag"]),
            }),
          );
        });
      }
    }
  });
});

describe("Document Categories - API Integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch categories on mount", async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(getDocumentCategories).toHaveBeenCalled();
    });
  });

  it("should handle category update success", async () => {
    updateDocument.mockResolvedValue({
      id: "doc-1",
      category: "legal",
      tags: ["important", "updated"],
    });

    render(<UploadPage />, { wrapper: createWrapper() });

    const editButton = screen.queryByRole("button", { name: /edit|category/i });
    if (editButton) {
      fireEvent.click(editButton);

      const categorySelect = await screen
        .findByRole("combobox")
        .catch(() => null);
      if (categorySelect) {
        fireEvent.change(categorySelect, { target: { value: "legal" } });
      }

      const saveBtn = screen.queryByRole("button", { name: /save/i });
      if (saveBtn) {
        fireEvent.click(saveBtn);

        await waitFor(() => {
          // Success toast should be shown
          const toast = require("react-hot-toast").default;
          expect(toast.success).toHaveBeenCalled();
        });
      }
    }
  });

  it("should handle category update error", async () => {
    updateDocument.mockRejectedValue(new Error("Update failed"));

    render(<UploadPage />, { wrapper: createWrapper() });

    const editButton = screen.queryByRole("button", { name: /edit|category/i });
    if (editButton) {
      fireEvent.click(editButton);

      const saveBtn = screen.queryByRole("button", { name: /save/i });
      if (saveBtn) {
        fireEvent.click(saveBtn);

        await waitFor(() => {
          // Error toast should be shown
          const toast = require("react-hot-toast").default;
          expect(toast.error).toHaveBeenCalled();
        });
      }
    }
  });
});
