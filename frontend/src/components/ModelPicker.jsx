/**
 * Model picker component for selecting LLM provider.
 */
import { useCallback, useMemo, memo } from "react";
import { Cpu, Cloud, Zap } from "lucide-react";

const PROVIDERS = [
  {
    id: "ollama",
    name: "Ollama",
    icon: Cpu,
    description: "FINE TUNED - Ollama llama3.1:8b ",
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

function ModelPicker({
  selectedProvider,
  selectedModel,
  onProviderChange,
  onModelChange,
}) {
  const handleModelChange = useCallback(
    (e) => {
      const value = e.target.value;
      if (onModelChange) {
        onModelChange(value);
      }
    },
    [onModelChange],
  );

  const placeholder = useMemo(() => {
    switch (selectedProvider) {
      case "ollama":
        return "Default: policy-compliance-llm (fine-tuned)";
      case "openai":
        return "e.g., gpt-4o-mini, gpt-4";
      case "anthropic":
        return "e.g., claude-3-5-sonnet-latest";
      default:
        return "Leave empty for default";
    }
  }, [selectedProvider]);

  const modelHint = useMemo(() => {
    if (selectedProvider === "ollama") {
      return (
        <div className="mt-2 text-xs text-[var(--text-secondary)]">
          💡 Fine-tuned on Ollama <strong>llama3.1:8b</strong> for best accuracy
          and performance
        </div>
      );
    }
    return null;
  }, [selectedProvider]);

  return (
    <div>
      <label className="flex items-center text-sm font-medium text-[var(--text-secondary)] mb-3">
        <Zap className="h-4 w-4 mr-2 text-amber-400" />
        Select LLM Provider
      </label>

      {/* Mobile: vertical stack, Desktop: 3-column grid */}
      <div className="flex flex-col gap-2 sm:flex-row sm:gap-3">
        {PROVIDERS.map((provider) => {
          const Icon = provider.icon;
          const isSelected = selectedProvider === provider.id;

          return (
            <button
              key={provider.id}
              onClick={() => onProviderChange(provider.id)}
              className={`relative flex items-center justify-center sm:justify-start gap-3 px-4 py-3 w-full sm:flex-1 rounded-xl border transition-all duration-200 group overflow-hidden touch-manipulation ${
                isSelected
                  ? `border-transparent bg-gradient-to-br ${provider.gradient}`
                  : "border-[var(--border-subtle)] bg-[var(--bg-tertiary)]/50 hover:border-[var(--hover-border)] hover:bg-[var(--hover-bg)] active:scale-[0.98]"
              }`}
            >
              {/* Icon - hidden on mobile */}
              <div
                className={`relative z-10 p-2 rounded-lg flex-shrink-0 hidden sm:block ${
                  isSelected
                    ? "bg-white/20"
                    : "bg-[var(--bg-secondary)] group-hover:bg-[var(--bg-tertiary)]"
                } transition-colors`}
              >
                <Icon
                  className={`h-5 w-5 ${isSelected ? "text-white" : "text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]"}`}
                />
              </div>
              <div className="relative z-10 text-center sm:text-left">
                <div
                  className={`text-sm font-semibold ${isSelected ? "text-white" : "text-[var(--text-primary)]"}`}
                >
                  {provider.name}
                </div>
                <div
                  className={`text-xs ${isSelected ? "text-white/80" : "text-[var(--text-secondary)]"}`}
                >
                  {provider.description}
                </div>
              </div>

              {/* Selection indicator */}
              {isSelected && (
                <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-white" />
              )}
            </button>
          );
        })}
      </div>

      {/* Model hint for Ollama */}
      {modelHint}
    </div>
  );
}

export default memo(ModelPicker);
