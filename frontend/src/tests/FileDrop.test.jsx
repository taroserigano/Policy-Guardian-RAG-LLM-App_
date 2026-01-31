import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import FileDrop from "../components/FileDrop";

describe("FileDrop Component", () => {
  it("renders upload area", () => {
    render(<FileDrop />);

    expect(
      screen.getByText(/drop your file here or click to browse/i),
    ).toBeInTheDocument();
  });

  it("shows file input", () => {
    render(<FileDrop />);

    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
  });

  it("accepts PDF, Word, and TXT files by default", () => {
    render(<FileDrop />);

    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toHaveAttribute("accept", ".pdf,.txt,.docx,.doc");
  });

  it("displays selected file name after selection", async () => {
    const mockOnFileSelect = vi.fn();
    render(<FileDrop onFileSelect={mockOnFileSelect} />);

    const fileInput = document.querySelector('input[type="file"]');
    const file = new File(["test content"], "test.pdf", {
      type: "application/pdf",
    });

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/test\.pdf/i)).toBeInTheDocument();
    });
    expect(mockOnFileSelect).toHaveBeenCalledWith(file);
  });

  it("shows error for invalid file type", async () => {
    render(<FileDrop />);

    const fileInput = document.querySelector('input[type="file"]');
    const file = new File(["test content"], "test.jpg", {
      type: "image/jpeg",
    });

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
    });
  });

  it("shows error for file too large", async () => {
    // maxSizeMB = 0.0001 = ~100 bytes
    render(<FileDrop maxSizeMB={0.0001} />);

    const fileInput = document.querySelector('input[type="file"]');
    // Create a file with content larger than 100 bytes
    const largeContent = "x".repeat(500);
    const file = new File([largeContent], "test.pdf", {
      type: "application/pdf",
    });

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/file too large/i)).toBeInTheDocument();
    });
  });

  it("enables multiple file selection when multiple prop is true", () => {
    render(<FileDrop multiple={true} />);

    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toHaveAttribute("multiple");
  });

  it("handles drag events", () => {
    render(<FileDrop />);

    const dropZone = screen
      .getByText(/drop your file here or click to browse/i)
      .closest("div");

    fireEvent.dragEnter(dropZone);
    expect(screen.getByText(/drop your file here$/i)).toBeInTheDocument();

    fireEvent.dragLeave(dropZone);
    expect(
      screen.getByText(/drop your file here or click to browse/i),
    ).toBeInTheDocument();
  });

  it("handles file drop", async () => {
    const mockOnFileSelect = vi.fn();
    render(<FileDrop onFileSelect={mockOnFileSelect} />);

    const dropZone = screen
      .getByText(/drop your file here or click to browse/i)
      .closest("div");
    const file = new File(["test content"], "dropped.pdf", {
      type: "application/pdf",
    });

    const dataTransfer = {
      files: [file],
    };

    fireEvent.drop(dropZone, { dataTransfer });

    await waitFor(() => {
      expect(screen.getByText(/dropped\.pdf/i)).toBeInTheDocument();
    });
    expect(mockOnFileSelect).toHaveBeenCalledWith(file);
  });
});
