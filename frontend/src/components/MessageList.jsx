/**
 * Chat message list component displaying conversation history.
 * Modern dark theme with glassmorphism and animations.
 */
import { User, Bot, Sparkles } from "lucide-react";
import CitationsList from "./CitationsList";

export default function MessageList({ messages, isLoading }) {
  return (
    <div className="space-y-6">
      {messages.map((message, index) => (
        <div
          key={index}
          className="animate-slideUp"
          style={{ animationDelay: `${index * 0.03}s` }}
        >
          {/* User Message */}
          {message.type === "user" && (
            <div className="flex items-start gap-3 justify-end">
              <div className="max-w-[80%] bg-gradient-to-br from-violet-500/20 to-fuchsia-500/10 rounded-2xl rounded-tr-md px-4 py-3 border border-violet-500/10">
                <p className="text-zinc-200 leading-relaxed text-[15px]">
                  {message.content}
                </p>
              </div>
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-xl bg-zinc-800 flex items-center justify-center border border-zinc-700/50">
                  <User className="h-4 w-4 text-zinc-400" />
                </div>
              </div>
            </div>
          )}

          {/* Assistant Message */}
          {message.type === "assistant" && (
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <div className="relative group">
                  <div className="absolute inset-0 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-xl blur-md opacity-40 group-hover:opacity-60 transition-opacity" />
                  <div className="relative h-8 w-8 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-white" />
                  </div>
                </div>
              </div>
              <div className="flex-1 space-y-3 max-w-[85%]">
                <div className="relative group">
                  <div className="bg-zinc-900/60 backdrop-blur-sm rounded-2xl rounded-tl-md px-4 py-3 border border-zinc-800/80">
                    <p className="text-zinc-300 whitespace-pre-wrap leading-relaxed text-[15px]">
                      {message.content ||
                        (message.isStreaming ? "" : "(no content)")}
                      {/* Streaming cursor */}
                      {message.isStreaming && (
                        <span className="inline-block w-0.5 h-5 ml-0.5 bg-violet-400 rounded-full animate-pulse" />
                      )}
                    </p>

                    {/* Model info */}
                    {message.model && !message.isStreaming && (
                      <div className="mt-3 pt-3 border-t border-zinc-800/50 flex items-center">
                        <Sparkles className="h-3 w-3 mr-1.5 text-amber-400/80" />
                        <span className="text-xs text-zinc-500">
                          {message.model.provider}
                          {message.model.name && (
                            <span className="text-zinc-600 ml-1">
                              · {message.model.name}
                            </span>
                          )}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Citations */}
                {message.citations && message.citations.length > 0 && (
                  <CitationsList citations={message.citations} />
                )}
              </div>
            </div>
          )}
        </div>
      ))}

      {/* Loading indicator */}
      {isLoading &&
        (messages.length === 0 ||
          !messages[messages.length - 1]?.isStreaming) && (
          <div className="flex items-start gap-3 animate-fadeIn">
            <div className="flex-shrink-0">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-xl blur-md opacity-50 animate-pulse" />
                <div className="relative h-8 w-8 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-white" />
                </div>
              </div>
            </div>
            <div className="bg-zinc-900/60 backdrop-blur-sm rounded-2xl rounded-tl-md px-4 py-3 border border-zinc-800/80">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div
                    className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0ms" }}
                  />
                  <div
                    className="w-1.5 h-1.5 bg-fuchsia-400 rounded-full animate-bounce"
                    style={{ animationDelay: "150ms" }}
                  />
                  <div
                    className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce"
                    style={{ animationDelay: "300ms" }}
                  />
                </div>
                <span className="text-zinc-500 text-sm">Analyzing...</span>
              </div>
            </div>
          </div>
        )}
    </div>
  );
}
