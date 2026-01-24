import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ChatBox from "../components/ChatBox";

describe("ChatBox Component", () => {
  it("renders textarea and send button", () => {
    const mockOnSendMessage = vi.fn();
    render(<ChatBox onSendMessage={mockOnSendMessage} disabled={false} />);

    expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument();
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("allows typing in the textarea", () => {
    const mockOnSendMessage = vi.fn();
    render(<ChatBox onSendMessage={mockOnSendMessage} disabled={false} />);

    const textarea = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(textarea, { target: { value: "Test question" } });

    expect(textarea.value).toBe("Test question");
  });

  it("calls onSendMessage when send button clicked", () => {
    const mockOnSendMessage = vi.fn();
    render(<ChatBox onSendMessage={mockOnSendMessage} disabled={false} />);

    const textarea = screen.getByPlaceholderText(/ask a question/i);
    const button = screen.getByRole("button");

    fireEvent.change(textarea, { target: { value: "Test question" } });
    fireEvent.click(button);

    expect(mockOnSendMessage).toHaveBeenCalledWith("Test question");
  });

  it("calls onSendMessage when Enter key pressed", () => {
    const mockOnSendMessage = vi.fn();
    render(<ChatBox onSendMessage={mockOnSendMessage} disabled={false} />);

    const textarea = screen.getByPlaceholderText(/ask a question/i);

    fireEvent.change(textarea, { target: { value: "Test question" } });
    fireEvent.keyDown(textarea, { key: "Enter", code: "Enter" });

    expect(mockOnSendMessage).toHaveBeenCalledWith("Test question");
  });

  it("clears textarea after sending", () => {
    const mockOnSendMessage = vi.fn();
    render(<ChatBox onSendMessage={mockOnSendMessage} disabled={false} />);

    const textarea = screen.getByPlaceholderText(/ask a question/i);
    const button = screen.getByRole("button");

    fireEvent.change(textarea, { target: { value: "Test question" } });
    fireEvent.click(button);

    expect(textarea.value).toBe("");
  });

  it("does not send empty messages", () => {
    const mockOnSendMessage = vi.fn();
    render(<ChatBox onSendMessage={mockOnSendMessage} disabled={false} />);

    const button = screen.getByRole("button");
    fireEvent.click(button);

    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });

  it("disables textarea and button when disabled prop is true", () => {
    const mockOnSendMessage = vi.fn();
    render(<ChatBox onSendMessage={mockOnSendMessage} disabled={true} />);

    const textarea = screen.getByPlaceholderText(/ask a question/i);
    const button = screen.getByRole("button");

    expect(textarea).toBeDisabled();
    expect(button).toBeDisabled();
  });

  it("does not allow sending with Shift+Enter (allows newlines)", () => {
    const mockOnSendMessage = vi.fn();
    render(<ChatBox onSendMessage={mockOnSendMessage} disabled={false} />);

    const textarea = screen.getByPlaceholderText(/ask a question/i);

    fireEvent.change(textarea, { target: { value: "Test question" } });
    fireEvent.keyDown(textarea, {
      key: "Enter",
      code: "Enter",
      shiftKey: true,
    });

    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });
});
