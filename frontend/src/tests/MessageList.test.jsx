import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import MessageList from "../components/MessageList";

describe("MessageList Component", () => {
  it("renders empty when no messages", () => {
    render(<MessageList messages={[]} />);
    // Empty message list renders an empty div
    const container = document.querySelector(".space-y-6");
    expect(container).toBeInTheDocument();
    expect(container.children.length).toBe(0);
  });

  it("renders user and assistant messages", () => {
    const messages = [
      { type: "user", content: "What is the policy?" },
      { type: "assistant", content: "Here is the policy information..." },
    ];

    render(<MessageList messages={messages} />);

    expect(screen.getByText("What is the policy?")).toBeInTheDocument();
    expect(
      screen.getByText(/here is the policy information/i),
    ).toBeInTheDocument();
  });

  it("displays user messages", () => {
    const messages = [{ type: "user", content: "Test question" }];

    render(<MessageList messages={messages} />);

    expect(screen.getByText("Test question")).toBeInTheDocument();
  });

  it("displays assistant messages", () => {
    const messages = [{ type: "assistant", content: "Test answer" }];

    render(<MessageList messages={messages} />);

    expect(screen.getByText(/test answer/i)).toBeInTheDocument();
  });

  it("renders multiple messages", () => {
    const messages = [
      { type: "user", content: "First message" },
      { type: "assistant", content: "Second message" },
      { type: "user", content: "Third message" },
    ];

    render(<MessageList messages={messages} />);

    expect(screen.getByText("First message")).toBeInTheDocument();
    expect(screen.getByText(/second message/i)).toBeInTheDocument();
    expect(screen.getByText("Third message")).toBeInTheDocument();
  });

  it("shows streaming indicator when message is streaming", () => {
    const messages = [
      { type: "assistant", content: "Partial", isStreaming: true },
    ];

    render(<MessageList messages={messages} />);

    // Streaming cursor should be present (the animated span)
    const streamingCursor = document.querySelector(".animate-pulse");
    expect(streamingCursor).toBeInTheDocument();
  });

  it("hides streaming indicator when message is complete", () => {
    const messages = [
      { type: "assistant", content: "Complete response", isStreaming: false },
    ];

    render(<MessageList messages={messages} />);

    // Streaming cursor should not be present
    const streamingCursor = document.querySelector(".animate-pulse");
    expect(streamingCursor).not.toBeInTheDocument();
  });
});
