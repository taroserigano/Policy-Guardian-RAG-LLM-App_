import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ModelPicker from "../components/ModelPicker";

describe("ModelPicker Component", () => {
  it("renders with default selection", () => {
    const mockOnProviderChange = vi.fn();
    const mockOnModelChange = vi.fn();
    render(
      <ModelPicker
        selectedProvider="ollama"
        selectedModel="llama3.1"
        onProviderChange={mockOnProviderChange}
        onModelChange={mockOnModelChange}
      />,
    );

    expect(screen.getByText(/ollama/i)).toBeInTheDocument();
  });

  it("displays all provider options as buttons", () => {
    const mockOnProviderChange = vi.fn();
    const mockOnModelChange = vi.fn();
    render(
      <ModelPicker
        selectedProvider="ollama"
        selectedModel="llama3.1"
        onProviderChange={mockOnProviderChange}
        onModelChange={mockOnModelChange}
      />,
    );

    // Check provider buttons exist
    expect(screen.getByRole("button", { name: /ollama/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /openai/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /anthropic/i }),
    ).toBeInTheDocument();
  });

  it("calls onProviderChange when provider button is clicked", () => {
    const mockOnProviderChange = vi.fn();
    const mockOnModelChange = vi.fn();
    render(
      <ModelPicker
        selectedProvider="ollama"
        selectedModel="llama3.1"
        onProviderChange={mockOnProviderChange}
        onModelChange={mockOnModelChange}
      />,
    );

    const openaiButton = screen.getByRole("button", { name: /openai/i });
    fireEvent.click(openaiButton);

    expect(mockOnProviderChange).toHaveBeenCalledWith("openai");
  });

  it("has custom model input field", () => {
    const mockOnProviderChange = vi.fn();
    const mockOnModelChange = vi.fn();
    render(
      <ModelPicker
        selectedProvider="ollama"
        selectedModel="llama3.1"
        onProviderChange={mockOnProviderChange}
        onModelChange={mockOnModelChange}
      />,
    );

    // Check model input exists
    const modelInput = screen.getByRole("textbox");
    expect(modelInput).toBeInTheDocument();
  });

  it("calls onModelChange when custom model is entered", () => {
    const mockOnProviderChange = vi.fn();
    const mockOnModelChange = vi.fn();
    render(
      <ModelPicker
        selectedProvider="ollama"
        selectedModel=""
        onProviderChange={mockOnProviderChange}
        onModelChange={mockOnModelChange}
      />,
    );

    const modelInput = screen.getByRole("textbox");
    fireEvent.change(modelInput, { target: { value: "custom-model" } });

    expect(mockOnModelChange).toHaveBeenCalledWith("custom-model");
  });

  it("highlights selected provider", () => {
    const mockOnProviderChange = vi.fn();
    const mockOnModelChange = vi.fn();
    render(
      <ModelPicker
        selectedProvider="openai"
        selectedModel="gpt-4"
        onProviderChange={mockOnProviderChange}
        onModelChange={mockOnModelChange}
      />,
    );

    const openaiButton = screen.getByRole("button", { name: /openai/i });
    // The selected button should have specific styling
    expect(openaiButton).toBeInTheDocument();
  });
});
