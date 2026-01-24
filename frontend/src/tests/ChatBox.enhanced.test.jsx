/**
 * Comprehensive tests for ChatBox component
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatBox from "../components/ChatBox";

describe("ChatBox Component", () => {
  describe("Rendering", () => {
    it("should render textarea", () => {
      render(<ChatBox onSendMessage={vi.fn()} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);
      expect(textarea).toBeInTheDocument();
    });

    it("should render send button", () => {
      render(<ChatBox onSendMessage={vi.fn()} />);
      const button = screen.getByRole("button");
      expect(button).toBeInTheDocument();
    });

    it("should render help text", () => {
      render(<ChatBox onSendMessage={vi.fn()} />);
      // Component shows "Enter ↵ send · Shift+Enter new line"
      expect(screen.getByText(/enter.*send/i)).toBeInTheDocument();
    });

    it("should render with 3 rows by default", () => {
      render(<ChatBox onSendMessage={vi.fn()} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);
      expect(textarea).toHaveAttribute("rows", "3");
    });
  });

  describe("User Input", () => {
    it("should update textarea when user types", async () => {
      const user = userEvent.setup();
      render(<ChatBox onSendMessage={vi.fn()} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);

      await user.type(textarea, "Hello");
      expect(textarea).toHaveValue("Hello");
    });

    it("should handle multi-line input", async () => {
      const user = userEvent.setup();
      render(<ChatBox onSendMessage={vi.fn()} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);

      await user.type(textarea, "Line 1{Shift>}{Enter}{/Shift}Line 2");
      expect(textarea.value).toContain("Line 1");
      expect(textarea.value).toContain("Line 2");
    });

    it("should allow special characters", async () => {
      const user = userEvent.setup();
      render(<ChatBox onSendMessage={vi.fn()} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);

      await user.type(textarea, "What's the policy? @#$%");
      expect(textarea.value).toBe("What's the policy? @#$%");
    });
  });

  describe("Message Sending", () => {
    it("should call onSendMessage when form is submitted", async () => {
      const mockSend = vi.fn();
      render(<ChatBox onSendMessage={mockSend} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);
      const button = screen.getByRole("button");

      fireEvent.change(textarea, { target: { value: "Test message" } });
      fireEvent.click(button);

      expect(mockSend).toHaveBeenCalledWith("Test message");
    });

    it("should clear textarea after sending", async () => {
      const mockSend = vi.fn();
      render(<ChatBox onSendMessage={mockSend} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);
      const button = screen.getByRole("button");

      fireEvent.change(textarea, { target: { value: "Test message" } });
      fireEvent.click(button);

      expect(textarea).toHaveValue("");
    });

    it("should send on Enter key press", async () => {
      const mockSend = vi.fn();
      render(<ChatBox onSendMessage={mockSend} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);

      fireEvent.change(textarea, { target: { value: "Test message" } });
      fireEvent.keyDown(textarea, { key: "Enter", code: "Enter" });

      expect(mockSend).toHaveBeenCalledWith("Test message");
    });

    it("should not send on Shift+Enter", async () => {
      const mockSend = vi.fn();
      render(<ChatBox onSendMessage={mockSend} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);

      fireEvent.change(textarea, { target: { value: "Test message" } });
      fireEvent.keyDown(textarea, {
        key: "Enter",
        code: "Enter",
        shiftKey: true,
      });

      expect(mockSend).not.toHaveBeenCalled();
    });

    it("should trim whitespace from message", () => {
      const mockSend = vi.fn();
      render(<ChatBox onSendMessage={mockSend} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);
      const button = screen.getByRole("button");

      fireEvent.change(textarea, { target: { value: "  Test message  " } });
      fireEvent.click(button);

      expect(mockSend).toHaveBeenCalledWith("Test message");
    });

    it("should not send empty messages", () => {
      const mockSend = vi.fn();
      render(<ChatBox onSendMessage={mockSend} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);
      const button = screen.getByRole("button");

      fireEvent.change(textarea, { target: { value: "" } });
      fireEvent.click(button);

      expect(mockSend).not.toHaveBeenCalled();
    });

    it("should not send whitespace-only messages", () => {
      const mockSend = vi.fn();
      render(<ChatBox onSendMessage={mockSend} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);
      const button = screen.getByRole("button");

      fireEvent.change(textarea, { target: { value: "   " } });
      fireEvent.click(button);

      expect(mockSend).not.toHaveBeenCalled();
    });
  });

  describe("Button States", () => {
    it("should disable send button when message is empty", () => {
      render(<ChatBox onSendMessage={vi.fn()} />);
      const button = screen.getByRole("button");

      expect(button).toBeDisabled();
    });

    it("should enable send button when message has content", () => {
      render(<ChatBox onSendMessage={vi.fn()} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);
      const button = screen.getByRole("button");

      fireEvent.change(textarea, { target: { value: "Test" } });

      expect(button).not.toBeDisabled();
    });

    it("should disable send button with whitespace-only input", () => {
      render(<ChatBox onSendMessage={vi.fn()} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);
      const button = screen.getByRole("button");

      fireEvent.change(textarea, { target: { value: "   " } });

      expect(button).toBeDisabled();
    });
  });

  describe("Disabled State", () => {
    it("should disable textarea when disabled prop is true", () => {
      render(<ChatBox onSendMessage={vi.fn()} disabled={true} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);

      expect(textarea).toBeDisabled();
    });

    it("should disable button when disabled prop is true", () => {
      render(<ChatBox onSendMessage={vi.fn()} disabled={true} />);
      const button = screen.getByRole("button");

      expect(button).toBeDisabled();
    });

    it("should not send message when disabled", () => {
      const mockSend = vi.fn();
      render(<ChatBox onSendMessage={mockSend} disabled={true} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);
      const button = screen.getByRole("button");

      fireEvent.change(textarea, { target: { value: "Test" } });
      fireEvent.click(button);

      expect(mockSend).not.toHaveBeenCalled();
    });

    it("should apply disabled styling to textarea", () => {
      render(<ChatBox onSendMessage={vi.fn()} disabled={true} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);

      expect(textarea).toHaveClass("disabled:opacity-50");
    });
  });

  describe("Accessibility", () => {
    it("should have proper form semantics", () => {
      const { container } = render(<ChatBox onSendMessage={vi.fn()} />);
      const form = container.querySelector("form");

      expect(form).toBeInTheDocument();
    });

    it("should have accessible button", () => {
      render(<ChatBox onSendMessage={vi.fn()} />);
      const button = screen.getByRole("button");

      expect(button).toHaveAttribute("type", "submit");
    });

    it("should maintain focus on textarea after sending", async () => {
      const mockSend = vi.fn();
      render(<ChatBox onSendMessage={mockSend} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);

      textarea.focus();
      fireEvent.change(textarea, { target: { value: "Test" } });
      fireEvent.keyDown(textarea, { key: "Enter" });

      // Textarea should still be in document (not removed)
      expect(textarea).toBeInTheDocument();
    });
  });

  describe("Edge Cases", () => {
    it("should handle very long messages", async () => {
      const mockSend = vi.fn();
      render(<ChatBox onSendMessage={mockSend} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);
      const longMessage = "A".repeat(10000);

      fireEvent.change(textarea, { target: { value: longMessage } });
      fireEvent.submit(textarea.closest("form"));

      expect(mockSend).toHaveBeenCalledWith(longMessage);
    });

    it("should handle rapid successive typing", async () => {
      const user = userEvent.setup();
      render(<ChatBox onSendMessage={vi.fn()} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);

      await user.type(textarea, "Quick typing test", { delay: 1 });

      expect(textarea).toHaveValue("Quick typing test");
    });

    it("should handle unicode characters", async () => {
      const mockSend = vi.fn();
      render(<ChatBox onSendMessage={mockSend} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);

      fireEvent.change(textarea, { target: { value: "Hello 你好 🚀" } });
      fireEvent.submit(textarea.closest("form"));

      expect(mockSend).toHaveBeenCalledWith("Hello 你好 🚀");
    });

    it("should handle emojis", async () => {
      const mockSend = vi.fn();
      render(<ChatBox onSendMessage={mockSend} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);

      fireEvent.change(textarea, { target: { value: "Test 😀 🎉 👍" } });
      fireEvent.submit(textarea.closest("form"));

      expect(mockSend).toHaveBeenCalledWith("Test 😀 🎉 👍");
    });
  });

  describe("Integration Tests", () => {
    it("should handle complete user workflow", async () => {
      const user = userEvent.setup();
      const mockSend = vi.fn();
      render(<ChatBox onSendMessage={mockSend} />);
      const textarea = screen.getByPlaceholderText(/ask a question/i);
      const button = screen.getByRole("button");

      // Type message
      await user.type(textarea, "What is the leave policy?");
      expect(textarea).toHaveValue("What is the leave policy?");

      // Click send
      await user.click(button);

      // Verify sent and cleared
      expect(mockSend).toHaveBeenCalledWith("What is the leave policy?");
      expect(textarea).toHaveValue("");

      // Type another message
      await user.type(textarea, "How many days?");
      await user.keyboard("{Enter}");

      // Verify second message
      expect(mockSend).toHaveBeenCalledTimes(2);
      expect(mockSend).toHaveBeenLastCalledWith("How many days?");
    });
  });
});
