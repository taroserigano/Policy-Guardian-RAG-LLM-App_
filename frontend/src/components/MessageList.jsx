/**
 * Chat message list component displaying conversation history.
 */
import { User, Bot, Loader } from "lucide-react";
import CitationsList from "./CitationsList";

export default function MessageList({ messages, isLoading }) {
  return (
    <div className="space-y-6">
      {messages.map((message, index) => (
        <div key={index} className="animate-fadeIn">
          {/* User Message */}
          {message.type === "user" && (
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                  <User className="h-5 w-5 text-primary-600" />
                </div>
              </div>
              <div className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <p className="text-gray-900">{message.content}</p>
              </div>
            </div>
          )}

          {/* Assistant Message */}
          {message.type === "assistant" && (
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-green-100 flex items-center justify-center">
                  <Bot className="h-5 w-5 text-green-600" />
                </div>
              </div>
              <div className="flex-1 space-y-3">
                <div className="bg-green-50 rounded-lg shadow-sm border border-green-200 p-4">
                  <p className="text-gray-900 whitespace-pre-wrap">
                    {message.content}
                  </p>

                  {/* Model info */}
                  {message.model && (
                    <div className="mt-3 pt-3 border-t border-green-200">
                      <p className="text-xs text-green-700">
                        Model:{" "}
                        <span className="font-medium">
                          {message.model.provider}
                        </span>
                        {message.model.name && ` (${message.model.name})`}
                      </p>
                    </div>
                  )}
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
      {isLoading && (
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="h-8 w-8 rounded-full bg-green-100 flex items-center justify-center">
              <Bot className="h-5 w-5 text-green-600" />
            </div>
          </div>
          <div className="flex-1 bg-green-50 rounded-lg shadow-sm border border-green-200 p-4">
            <div className="flex items-center space-x-2 text-gray-500">
              <Loader className="h-5 w-5 animate-spin" />
              <span>Thinking...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
