import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ModelPicker from "../components/ModelPicker";

describe("ModelPicker Component", () => {
  it("renders with default selection", () => {
    const mockOnChange = vi.fn();
    render(
      <ModelPicker provider="ollama" model="llama3.1" onChange={mockOnChange} />
    );

    expect(screen.getByText(/ollama/i)).toBeInTheDocument();
  });

  it("displays all provider options", () => {
    const mockOnChange = vi.fn();
    render(
      <ModelPicker provider="ollama" model="llama3.1" onChange={mockOnChange} />
    );

    const providerSelect = screen.getByRole("combobox", { name: /provider/i });

    // Check if select has options
    expect(providerSelect).toBeInTheDocument();
    expect(providerSelect.querySelectorAll("option").length).toBeGreaterThan(1);
  });

  it("calls onChange when provider changes", () => {
    const mockOnChange = vi.fn();
    render(
      <ModelPicker provider="ollama" model="llama3.1" onChange={mockOnChange} />
    );

    const providerSelect = screen.getByRole("combobox", { name: /provider/i });
    fireEvent.change(providerSelect, { target: { value: "openai" } });

    expect(mockOnChange).toHaveBeenCalledWith("openai", expect.any(String));
  });

  it("updates model options based on provider", () => {
    const mockOnChange = vi.fn();
    const { rerender } = render(
      <ModelPicker provider="ollama" model="llama3.1" onChange={mockOnChange} />
    );

    // Check initial model
    const modelSelect = screen.getByRole("combobox", { name: /model/i });
    expect(modelSelect.value).toBe("llama3.1");

    // Change provider
    rerender(
      <ModelPicker provider="openai" model="gpt-4o" onChange={mockOnChange} />
    );

    // Model should update
    expect(modelSelect.value).toBe("gpt-4o");
  });
});
