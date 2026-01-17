/**
 * Model picker component for selecting LLM provider.
 */
import { useState } from "react";
import { Cpu, Cloud } from "lucide-react";

const PROVIDERS = [
  {
    id: "ollama",
    name: "Ollama (Local)",
    icon: Cpu,
    description: "Local LLM via Ollama",
    color: "blue",
  },
  {
    id: "openai",
    name: "OpenAI",
    icon: Cloud,
    description: "GPT models",
    color: "green",
  },
  {
    id: "anthropic",
    name: "Anthropic",
    icon: Cloud,
    description: "Claude models",
    color: "purple",
  },
];

export default function ModelPicker({
  selectedProvider,
  selectedModel,
  onProviderChange,
  onModelChange,
}) {
  const handleModelChange = (e) => {
    const value = e.target.value;
    if (onModelChange) {
      onModelChange(value);
    }
  };

  const getPlaceholder = () => {
    switch (selectedProvider) {
      case "ollama":
        return "e.g., llama3.1:8b, gemma2:9b";
      case "openai":
        return "e.g., gpt-4o-mini, gpt-4";
      case "anthropic":
        return "e.g., claude-3-5-sonnet-latest";
      default:
        return "Leave empty for default";
    }
  };

  const getColorClasses = (color, isSelected) => {
    const colors = {
      blue: isSelected
        ? "border-blue-500 bg-blue-50 text-blue-700"
        : "border-gray-300 hover:border-blue-300",
      green: isSelected
        ? "border-green-500 bg-green-50 text-green-700"
        : "border-gray-300 hover:border-green-300",
      purple: isSelected
        ? "border-purple-500 bg-purple-50 text-purple-700"
        : "border-gray-300 hover:border-purple-300",
    };
    return colors[color];
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select LLM Provider
        </label>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {PROVIDERS.map((provider) => {
            const Icon = provider.icon;
            const isSelected = selectedProvider === provider.id;

            return (
              <button
                key={provider.id}
                onClick={() => onProviderChange(provider.id)}
                className={`flex items-start p-4 border-2 rounded-lg transition-all ${getColorClasses(
                  provider.color,
                  isSelected,
                )}`}
              >
                <Icon className="h-5 w-5 mr-3 mt-0.5 flex-shrink-0" />
                <div className="text-left">
                  <div className="font-medium">{provider.name}</div>
                  <div className="text-xs mt-1 opacity-75">
                    {provider.description}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Optional: Custom model name input */}
      <div>
        <label
          htmlFor="custom-model"
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          Model Name (optional)
        </label>
        <input
          id="custom-model"
          type="text"
          value={selectedModel || ""}
          onChange={handleModelChange}
          placeholder={getPlaceholder()}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
        />
        <p className="mt-1 text-xs text-gray-500">
          Specify a custom model name or leave empty to use the default for
          selected provider
        </p>
      </div>
    </div>
  );
}
