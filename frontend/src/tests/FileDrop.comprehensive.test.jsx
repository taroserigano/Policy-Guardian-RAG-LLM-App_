/**
 * Comprehensive tests for FileDrop component with batch upload support.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import FileDrop from "../components/FileDrop";

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
  describe("Single File Mode", () => {
    it("renders upload area with correct text", () => {
      render(<FileDrop onFileSelect={vi.fn()} />, { wrapper });
      expect(screen.getByText(/drop your file here/i)).toBeInTheDocument();
    });

    it("shows file input element", () => {
      render(<FileDrop onFileSelect={vi.fn()} />, { wrapper });
      const fileInput = document.querySelector('input[type="file"]');
      expect(fileInput).toBeInTheDocument();
      expect(fileInput).not.toHaveAttribute("multiple");
    });

    it("accepts PDF and TXT files by default", () => {
      render(<FileDrop onFileSelect={vi.fn()} />, { wrapper });
      const fileInput = document.querySelector('input[type="file"]');
      expect(fileInput).toHaveAttribute("accept", ".pdf,.txt");
    });

    it("calls onFileSelect when file is selected", async () => {
      const onFileSelect = vi.fn();
      render(<FileDrop onFileSelect={onFileSelect} />, { wrapper });

      const fileInput = document.querySelector('input[type="file"]');
      const file = new File(["test content"], "test.pdf", {
        type: "application/pdf",
      });

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(onFileSelect).toHaveBeenCalledWith(file);
      });
    });

    it("displays selected file name and size", async () => {
      render(<FileDrop onFileSelect={vi.fn()} />, { wrapper });

      const fileInput = document.querySelector('input[type="file"]');
      const file = new File(["test content for size"], "document.pdf", {
        type: "application/pdf",
      });

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText(/document\.pdf/i)).toBeInTheDocument();
      });
    });

    it("shows error for invalid file type", async () => {
      render(<FileDrop onFileSelect={vi.fn()} />, { wrapper });

      const fileInput = document.querySelector('input[type="file"]');
      const file = new File(["test"], "test.exe", {
        type: "application/x-msdownload",
      });

      Object.defineProperty(file, "name", { value: "test.exe" });

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
      });
    });

    it("shows error for file exceeding size limit", async () => {
      render(<FileDrop onFileSelect={vi.fn()} maxSizeMB={0.001} />, {
        wrapper,
      });

      const fileInput = document.querySelector('input[type="file"]');
      const largeContent = new Array(2000).fill("x").join("");
      const file = new File([largeContent], "large.txt", {
        type: "text/plain",
      });

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText(/file too large/i)).toBeInTheDocument();
      });
    });
  });

  describe("Batch Upload Mode (multiple=true)", () => {
    it("renders with multiple file support", () => {
      render(<FileDrop onFilesSelect={vi.fn()} multiple={true} />, { wrapper });

      const fileInput = document.querySelector('input[type="file"]');
      expect(fileInput).toHaveAttribute("multiple");
    });

    it("shows multiple files allowed hint", () => {
      render(<FileDrop onFilesSelect={vi.fn()} multiple={true} />, { wrapper });
      expect(screen.getByText(/multiple files allowed/i)).toBeInTheDocument();
    });

    it("calls onFilesSelect with array of files", async () => {
      const onFilesSelect = vi.fn();
      render(<FileDrop onFilesSelect={onFilesSelect} multiple={true} />, {
        wrapper,
      });

      const fileInput = document.querySelector('input[type="file"]');
      const files = [
        new File(["content 1"], "doc1.txt", { type: "text/plain" }),
        new File(["content 2"], "doc2.txt", { type: "text/plain" }),
      ];

      fireEvent.change(fileInput, { target: { files } });

      await waitFor(() => {
        expect(onFilesSelect).toHaveBeenCalledWith(
          expect.arrayContaining([
            expect.objectContaining({ name: "doc1.txt" }),
            expect.objectContaining({ name: "doc2.txt" }),
          ]),
        );
      });
    });

    it("displays count of selected files", async () => {
      render(<FileDrop onFilesSelect={vi.fn()} multiple={true} />, { wrapper });

      const fileInput = document.querySelector('input[type="file"]');
      const files = [
        new File(["1"], "a.txt", { type: "text/plain" }),
        new File(["2"], "b.txt", { type: "text/plain" }),
        new File(["3"], "c.txt", { type: "text/plain" }),
      ];

      fireEvent.change(fileInput, { target: { files } });

      await waitFor(() => {
        expect(screen.getByText(/3 files? selected/i)).toBeInTheDocument();
      });
    });

    it("filters out invalid files from batch", async () => {
      const onFilesSelect = vi.fn();
      render(<FileDrop onFilesSelect={onFilesSelect} multiple={true} />, {
        wrapper,
      });

      const fileInput = document.querySelector('input[type="file"]');

      const validFile = new File(["valid"], "valid.txt", {
        type: "text/plain",
      });
      const invalidFile = new File(["invalid"], "invalid.exe", {
        type: "application/x-msdownload",
      });
      Object.defineProperty(invalidFile, "name", { value: "invalid.exe" });

      fireEvent.change(fileInput, {
        target: { files: [validFile, invalidFile] },
      });

      await waitFor(() => {
        // Should only include valid file
        expect(onFilesSelect).toHaveBeenCalled();
        const calledFiles = onFilesSelect.mock.calls[0][0];
        expect(calledFiles.length).toBe(1);
        expect(calledFiles[0].name).toBe("valid.txt");
      });
    });
  });

  describe("Drag and Drop", () => {
    it("shows drag active state on dragenter", async () => {
      render(<FileDrop onFileSelect={vi.fn()} />, { wrapper });

      const dropZone = screen
        .getByText(/drop your file/i)
        .closest("[class*='border-dashed']");

      fireEvent.dragEnter(dropZone, {
        dataTransfer: { files: [] },
      });

      // After drag enter, the text should change to "Drop your file here"
      await waitFor(() => {
        expect(screen.getByText(/drop your file here$/i)).toBeInTheDocument();
      });
    });

    it("removes drag active state on dragleave", () => {
      render(<FileDrop onFileSelect={vi.fn()} />, { wrapper });

      const dropZone = screen.getByText(/drop your file/i).closest("div");

      fireEvent.dragEnter(dropZone, { dataTransfer: { files: [] } });
      fireEvent.dragLeave(dropZone, { dataTransfer: { files: [] } });

      // Should return to normal state
      expect(dropZone).not.toHaveClass("scale-[1.01]");
    });

    it("handles file drop in single mode", async () => {
      const onFileSelect = vi.fn();
      render(<FileDrop onFileSelect={onFileSelect} />, { wrapper });

      const dropZone = screen.getByText(/drop your file/i).closest("div");
      const file = new File(["dropped"], "dropped.txt", { type: "text/plain" });

      fireEvent.drop(dropZone, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(onFileSelect).toHaveBeenCalledWith(file);
      });
    });

    it("handles multiple file drop in batch mode", async () => {
      const onFilesSelect = vi.fn();
      render(<FileDrop onFilesSelect={onFilesSelect} multiple={true} />, {
        wrapper,
      });

      const dropZone = screen.getByText(/drop your file/i).closest("div");
      const files = [
        new File(["1"], "drop1.txt", { type: "text/plain" }),
        new File(["2"], "drop2.txt", { type: "text/plain" }),
      ];

      fireEvent.drop(dropZone, {
        dataTransfer: { files },
      });

      await waitFor(() => {
        expect(onFilesSelect).toHaveBeenCalled();
      });
    });
  });

  describe("Custom Props", () => {
    it("accepts custom file types", () => {
      render(<FileDrop onFileSelect={vi.fn()} accept=".doc,.docx" />, {
        wrapper,
      });

      const fileInput = document.querySelector('input[type="file"]');
      expect(fileInput).toHaveAttribute("accept", ".doc,.docx");
    });

    it("uses custom max file size", async () => {
      render(<FileDrop onFileSelect={vi.fn()} maxSizeMB={1} />, { wrapper });

      expect(screen.getByText(/max 1MB/i)).toBeInTheDocument();
    });
  });
});
