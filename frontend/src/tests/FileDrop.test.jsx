import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import FileDrop from "../components/FileDrop";

// Create a new QueryClient for each test
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const wrapper = ({ children }) => (
  <QueryClientProvider client={createTestQueryClient()}>
    {children}
  </QueryClientProvider>
);

describe("FileDrop Component", () => {
  it("renders upload area", () => {
    render(<FileDrop />, { wrapper });

    expect(screen.getByText(/drag & drop/i)).toBeInTheDocument();
    expect(screen.getByText(/click to browse/i)).toBeInTheDocument();
  });

  it("shows file input when clicked", () => {
    render(<FileDrop />, { wrapper });

    const uploadArea = screen.getByText(/drag & drop/i).parentElement;
    fireEvent.click(uploadArea);

    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
  });

  it("accepts only PDF and TXT files", () => {
    render(<FileDrop />, { wrapper });

    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toHaveAttribute("accept", ".pdf,.txt");
  });

  it("displays selected file name", async () => {
    render(<FileDrop />, { wrapper });

    const fileInput = document.querySelector('input[type="file"]');
    const file = new File(["test content"], "test.pdf", {
      type: "application/pdf",
    });

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/test\.pdf/i)).toBeInTheDocument();
    });
  });
});
