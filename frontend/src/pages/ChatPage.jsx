/**
 * Chat page with document filtering and conversation interface.
 */
import { useState, useEffect, useRef } from "react";
import { AlertCircle } from "lucide-react";
import MessageList from "../components/MessageList";
import ChatBox from "../components/ChatBox";
import DocumentList from "../components/DocumentList";
import ModelPicker from "../components/ModelPicker";
import { useDocuments, useChatMutation } from "../hooks/useApi";

// Generate a simple session ID for user tracking
const getUserId = () => {
  let userId = localStorage.getItem("user_id");
  if (!userId) {
    userId = `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem("user_id", userId);
  }
  return userId;
};

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState("ollama");
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const messagesEndRef = useRef(null);

  // Reset model when provider changes
  const handleProviderChange = (newProvider) => {
    setSelectedProvider(newProvider);
    setSelectedModel(""); // Clear model name when switching providers
  };

  const {
    data: documents,
    isLoading: docsLoading,
    error: docsError,
  } = useDocuments();
  const chatMutation = useChatMutation();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (content) => {
    // Add user message to conversation
    const userMessage = {
      type: "user",
      content,
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      // Prepare chat request
      const chatRequest = {
        user_id: getUserId(),
        provider: selectedProvider,
        model: selectedModel || undefined,
        question: content,
        doc_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
        top_k: 5,
      };

      // Call API
      const response = await chatMutation.mutateAsync(chatRequest);

      // Add assistant response
      const assistantMessage = {
        type: "assistant",
        content: response.answer,
        citations: response.citations,
        model: response.model,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      // Add error message
      const errorMessage = {
        type: "assistant",
        content: `Sorry, I encountered an error: ${
          error.response?.data?.detail || error.message || "Unknown error"
        }`,
        citations: [],
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  return (
    <div className="h-[calc(100vh-8rem)]">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Document Q&A</h1>
        <p className="text-gray-600">
          Ask questions about your uploaded documents. Select documents to
          filter your search.
        </p>
      </div>

      {/* Model Selection */}
      <div className="mb-6 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <ModelPicker
          selectedProvider={selectedProvider}
          selectedModel={selectedModel}
          onProviderChange={handleProviderChange}
          onModelChange={setSelectedModel}
        />
      </div>

      {/* Main Chat Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100%-12rem)]">
        {/* Left Sidebar - Document Filter */}
        <div className="lg:col-span-1 bg-white rounded-lg shadow-sm border border-gray-200 p-4 overflow-y-auto">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Filter Documents
          </h2>

          <DocumentList
            documents={documents}
            isLoading={docsLoading}
            error={docsError}
            onSelectionChange={setSelectedDocIds}
          />

          {!docsLoading &&
            !docsError &&
            (!documents || documents.length === 0) && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <p className="text-xs text-yellow-800">
                  No documents available. Upload documents first.
                </p>
              </div>
            )}
        </div>

        {/* Right Side - Chat Interface */}
        <div className="lg:col-span-3 bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 mb-4">
                    <AlertCircle className="h-8 w-8 text-primary-600" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Start a Conversation
                  </h3>
                  <p className="text-gray-600 max-w-sm mx-auto">
                    Ask questions about your uploaded documents. I'll provide
                    answers with citations.
                  </p>
                </div>
              </div>
            ) : (
              <>
                <MessageList
                  messages={messages}
                  isLoading={chatMutation.isPending}
                />
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4">
            <ChatBox
              onSendMessage={handleSendMessage}
              disabled={chatMutation.isPending}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
