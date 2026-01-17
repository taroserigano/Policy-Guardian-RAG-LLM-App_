import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import MessageList from "../components/MessageList";

describe("MessageList Component", () => {
  it("renders empty state when no messages", () => {
    render(<MessageList messages={[]} />);

    expect(screen.getByText(/no messages yet/i)).toBeInTheDocument();
  });

  it("renders user and assistant messages", () => {
    const messages = [
      { role: "user", content: "What is the policy?" },
      { role: "assistant", content: "Here is the policy information..." },
    ];

    render(<MessageList messages={messages} />);

    expect(screen.getByText("What is the policy?")).toBeInTheDocument();
    expect(
      screen.getByText(/here is the policy information/i)
    ).toBeInTheDocument();
  });

  it("displays user messages with correct styling", () => {
    const messages = [{ role: "user", content: "Test question" }];

    render(<MessageList messages={messages} />);

    const userMessage = screen.getByText("Test question").parentElement;
    expect(userMessage).toHaveClass("bg-blue-600");
  });

  it("displays assistant messages with correct styling", () => {
    const messages = [{ role: "assistant", content: "Test answer" }];

    render(<MessageList messages={messages} />);

    const assistantMessage = screen.getByText("Test answer").parentElement;
    expect(assistantMessage).toHaveClass("bg-gray-100");
  });

  it("renders multiple messages in order", () => {
    const messages = [
      { role: "user", content: "First" },
      { role: "assistant", content: "Second" },
      { role: "user", content: "Third" },
    ];

    render(<MessageList messages={messages} />);

    const messageElements = screen.getAllByRole("article");
    expect(messageElements).toHaveLength(3);
  });

  it("auto-scrolls to bottom on new messages", () => {
    const { rerender } = render(<MessageList messages={[]} />);

    const scrollToMock = vi.fn();
    HTMLElement.prototype.scrollIntoView = scrollToMock;

    const newMessages = [{ role: "user", content: "New message" }];

    rerender(<MessageList messages={newMessages} />);

    // Should attempt to scroll
    expect(scrollToMock).toHaveBeenCalled();
  });
});
