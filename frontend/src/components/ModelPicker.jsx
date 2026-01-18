/**
 * Model picker component for selecting LLM provider.
 */
import { useState } from "react";
import { Cpu, Cloud, Zap } from "lucide-react";

const PROVIDERS = [
  {
    id: "ollama",
    name: "Ollama",
    icon: Cpu,
    description: "Local LLM",
    color: "blue",
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    id: "openai",
    name: "OpenAI",
    icon: Zap,
    description: "GPT models",
    color: "green",
    gradient: "from-emerald-500 to-teal-500",
  },
  {
    id: "anthropic",
    name: "Anthropic",
    icon: Cloud,
    description: "Claude models",
    color: "purple",
    gradient: "from-purple-500 to-pink-500",
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

  return (
    <div className="space-y-5">
      <div>
        <label className="flex items-center text-sm font-medium text-zinc-300 mb-3">
          <Zap className="h-4 w-4 mr-2 text-amber-400" />
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
                className={`relative flex items-center p-3.5 rounded-xl border transition-all duration-200 group overflow-hidden ${
                  isSelected
                    ? `border-transparent bg-gradient-to-br ${provider.gradient}`
                    : "border-zinc-700/50 bg-zinc-800/50 hover:border-zinc-600 hover:bg-zinc-800"
                }`}
              >
                <div
                  className={`relative z-10 p-2 rounded-lg mr-3 ${
                    isSelected
                      ? "bg-white/20"
                      : "bg-zinc-700/50 group-hover:bg-zinc-700"
                  } transition-colors`}
                >
                  <Icon
                    className={`h-4 w-4 ${isSelected ? "text-white" : "text-zinc-400 group-hover:text-zinc-200"}`}
                  />
                </div>
                <div className="relative z-10 text-left">
                  <div
                    className={`text-sm font-semibold ${isSelected ? "text-white" : "text-zinc-300 group-hover:text-white"}`}
                  >
                    {provider.name}
                  </div>
                  <div
                    className={`text-xs ${isSelected ? "text-white/70" : "text-zinc-500"}`}
                  >
                    {provider.description}
                  </div>
                </div>

                {/* Selection indicator */}
                {isSelected && (
                  <div className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-white" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Custom model name input */}
      <div>
        <label
          htmlFor="custom-model"
          className="block text-sm font-medium text-zinc-300 mb-2"
        >
          Model Name <span className="text-zinc-600">(optional)</span>
        </label>
        <input
          id="custom-model"
          type="text"
          value={selectedModel || ""}
          onChange={handleModelChange}
          placeholder={getPlaceholder()}
          className="w-full px-4 py-2.5 bg-zinc-800/50 border border-zinc-700/50 rounded-xl text-white text-sm placeholder-zinc-500 focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20 transition-all"
        />
        <p className="mt-2 text-xs text-zinc-600">
          Specify a custom model or leave empty for default
        </p>
      </div>
    </div>
  );
}
