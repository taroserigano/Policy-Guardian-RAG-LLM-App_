import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ChatBox from "../components/ChatBox";

describe("ChatBox Component", () => {
  it("renders input field and send button", () => {
    const mockOnSend = vi.fn();
    render(<ChatBox onSend={mockOnSend} disabled={false} />);

    expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /send/i })).toBeInTheDocument();
  });

  it("allows typing in the input field", () => {
    const mockOnSend = vi.fn();
    render(<ChatBox onSend={mockOnSend} disabled={false} />);

    const input = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(input, { target: { value: "Test question" } });

    expect(input.value).toBe("Test question");
  });

  it("calls onSend when send button clicked", () => {
    const mockOnSend = vi.fn();
    render(<ChatBox onSend={mockOnSend} disabled={false} />);

    const input = screen.getByPlaceholderText(/ask a question/i);
    const button = screen.getByRole("button", { name: /send/i });

    fireEvent.change(input, { target: { value: "Test question" } });
    fireEvent.click(button);

    expect(mockOnSend).toHaveBeenCalledWith("Test question");
  });

  it("calls onSend when Enter key pressed", () => {
    const mockOnSend = vi.fn();
    render(<ChatBox onSend={mockOnSend} disabled={false} />);

    const input = screen.getByPlaceholderText(/ask a question/i);

    fireEvent.change(input, { target: { value: "Test question" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });

    expect(mockOnSend).toHaveBeenCalledWith("Test question");
  });

  it("clears input after sending", () => {
    const mockOnSend = vi.fn();
    render(<ChatBox onSend={mockOnSend} disabled={false} />);

    const input = screen.getByPlaceholderText(/ask a question/i);
    const button = screen.getByRole("button", { name: /send/i });

    fireEvent.change(input, { target: { value: "Test question" } });
    fireEvent.click(button);

    expect(input.value).toBe("");
  });

  it("does not send empty messages", () => {
    const mockOnSend = vi.fn();
    render(<ChatBox onSend={mockOnSend} disabled={false} />);

    const button = screen.getByRole("button", { name: /send/i });
    fireEvent.click(button);

    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it("disables input and button when disabled prop is true", () => {
    const mockOnSend = vi.fn();
    render(<ChatBox onSend={mockOnSend} disabled={true} />);

    const input = screen.getByPlaceholderText(/ask a question/i);
    const button = screen.getByRole("button", { name: /send/i });

    expect(input).toBeDisabled();
    expect(button).toBeDisabled();
  });
});
