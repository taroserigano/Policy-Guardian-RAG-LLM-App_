/**
 * Chat page with document filtering and conversation interface.
 * Supports streaming responses and conversation history.
 */
import { useState, useEffect, useRef, useCallback } from "react";
import toast from "react-hot-toast";
import {
  AlertCircle,
  History,
  Trash2,
  X,
  Settings2,
  Sparkles,
  Search,
  BarChart3,
  FileText,
  Image,
  ChevronDown,
  ChevronUp,
  Download,
  Wand2,
  Layers,
  Zap,
} from "lucide-react";
import MessageList from "../components/MessageList";
import ChatBox from "../components/ChatBox";
import DocumentList from "../components/DocumentList";
import ModelPicker from "../components/ModelPicker";
import ImageGallery from "../components/ImageGallery";
import {
  useDocuments,
  useChatHistory,
  useClearChatHistory,
} from "../hooks/useApi";
import {
  streamChatMessage,
  streamMultimodalChat,
  exportChatHistory,
} from "../api/client";

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
  // Core state
  const [messages, setMessages] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState("ollama");
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [selectedImageIds, setSelectedImageIds] = useState([]);
  const [images, setImages] = useState([]);
  const [showImages, setShowImages] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showRagOptions, setShowRagOptions] = useState(false);

  // Advanced RAG options
  const [ragOptions, setRagOptions] = useState({
    query_expansion: false,
    hybrid_search: false,
    reranking: false,
    auto_rewrite: false, // Advanced: Auto-improve queries
    cross_encoder: false, // Advanced: Cross-encoder reranking
  });

  // DEDICATED STREAMING STATE - These will 100% trigger re-renders
  const [streamingText, setStreamingText] = useState("");
  const [streamingCitations, setStreamingCitations] = useState([]);

  // Refs for cleanup and final values
  const messagesEndRef = useRef(null);
  const abortStreamRef = useRef(null);
  const finalContentRef = useRef("");
  const finalCitationsRef = useRef([]);
  const tokenBufferRef = useRef("");
  const rafIdRef = useRef(null);

  const userId = getUserId();

  const {
    data: documents,
    isLoading: docsLoading,
    error: docsError,
  } = useDocuments();

  const { data: chatHistory, refetch: refetchHistory } = useChatHistory(userId);
  const clearHistoryMutation = useClearChatHistory();

  // Load images on mount
  useEffect(() => {
    const loadImages = async () => {
      try {
        const response = await fetch("http://localhost:8001/api/images");
        if (response.ok) {
          const data = await response.json();
          setImages(data);
        }
      } catch (error) {
        console.error("Failed to load images:", error);
      }
    };
    loadImages();
  }, []);

  // Sync streaming text to ref for onDone callback
  useEffect(() => {
    finalContentRef.current = streamingText;
  }, [streamingText]);

  useEffect(() => {
    finalCitationsRef.current = streamingCitations;
  }, [streamingCitations]);

  // Auto-scroll when streaming text changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  // Cleanup stream on unmount
  useEffect(() => {
    return () => {
      if (abortStreamRef.current) {
        abortStreamRef.current();
      }
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+E: Export chat history
      if (e.ctrlKey && e.key === "e" && messages.length > 0) {
        e.preventDefault();
        exportChatHistory(userId, "markdown")
          .then(() => toast.success("Chat history exported"))
          .catch(() => toast.error("Failed to export"));
      }
      // Ctrl+Shift+C: Clear conversation
      if (e.ctrlKey && e.shiftKey && e.key === "C" && messages.length > 0) {
        e.preventDefault();
        if (window.confirm("Clear current conversation?")) {
          setMessages([]);
          setStreamingText("");
          setStreamingCitations([]);
          toast.success("Conversation cleared");
        }
      }
      // Ctrl+/: Toggle RAG options
      if (e.ctrlKey && e.key === "/") {
        e.preventDefault();
        setShowRagOptions((prev) => !prev);
      }
      // Escape: Close panels
      if (e.key === "Escape") {
        setShowHistory(false);
        setShowRagOptions(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [messages, userId]);

  const handleProviderChange = (newProvider) => {
    setSelectedProvider(newProvider);
    setSelectedModel("");
  };

  const handleSendMessage = useCallback(
    async (content) => {
      // Add user message (include selected images info)
      const userMessage = {
        type: "user",
        content,
        imageIds:
          selectedImageIds.length > 0 ? [...selectedImageIds] : undefined,
      };
      setMessages((prev) => [...prev, userMessage]);

      // Reset streaming state
      setStreamingText("");
      setStreamingCitations([]);
      finalContentRef.current = "";
      finalCitationsRef.current = [];
      setIsStreaming(true);

      const chatRequest = {
        user_id: userId,
        provider: selectedProvider,
        model: selectedModel || undefined,
        question: content,
        doc_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
        image_ids: selectedImageIds.length > 0 ? selectedImageIds : undefined,
        top_k: 5,
        rag_options: ragOptions,
      };

      // Use multimodal chat if images are selected, otherwise use regular chat
      const streamFn =
        selectedImageIds.length > 0 ? streamMultimodalChat : streamChatMessage;

      abortStreamRef.current = streamFn(chatRequest, {
        onToken: (token) => {
          // Buffer tokens and batch updates with requestAnimationFrame for performance
          tokenBufferRef.current += token;
          finalContentRef.current += token;

          if (!rafIdRef.current) {
            rafIdRef.current = requestAnimationFrame(() => {
              const buffered = tokenBufferRef.current;
              tokenBufferRef.current = "";
              rafIdRef.current = null;
              setStreamingText((prev) => prev + buffered);
            });
          }
        },
        onCitations: (citations) => {
          setStreamingCitations(citations);
        },
        onDone: (data) => {
          // Cancel any pending animation frame
          if (rafIdRef.current) {
            cancelAnimationFrame(rafIdRef.current);
            rafIdRef.current = null;
          }
          // Flush any remaining buffered tokens
          if (tokenBufferRef.current) {
            finalContentRef.current += tokenBufferRef.current;
            tokenBufferRef.current = "";
          }
          // Add completed message using refs for final content
          setMessages((prev) => [
            ...prev,
            {
              type: "assistant",
              content: finalContentRef.current,
              citations: finalCitationsRef.current,
              model: data.model,
              isStreaming: false,
            },
          ]);
          // Clear streaming state
          setStreamingText("");
          setStreamingCitations([]);
          setIsStreaming(false);
          abortStreamRef.current = null;
          refetchHistory();
        },
        onError: (error) => {
          setMessages((prev) => [
            ...prev,
            {
              type: "assistant",
              content: finalContentRef.current || `Error: ${error.message}`,
              citations: [],
              model: null,
              isStreaming: false,
            },
          ]);
          setStreamingText("");
          setStreamingCitations([]);
          setIsStreaming(false);
          abortStreamRef.current = null;
        },
      });
    },
    [
      userId,
      selectedProvider,
      selectedModel,
      selectedDocIds,
      selectedImageIds,
      ragOptions,
      refetchHistory,
    ],
  );

  const handleClearHistory = () => {
    if (window.confirm("Are you sure you want to clear all chat history?")) {
      clearHistoryMutation.mutate(userId);
    }
  };

  const loadHistoryEntry = (entry) => {
    setMessages([
      { type: "user", content: entry.question },
      {
        type: "assistant",
        content: entry.answer,
        citations: [],
        model: { provider: entry.provider, name: entry.model },
      },
    ]);
    setShowHistory(false);
  };

  // Build display messages - include streaming message if active
  const displayMessages = isStreaming
    ? [
        ...messages,
        {
          type: "assistant",
          content: streamingText,
          citations: streamingCitations,
          model: null,
          isStreaming: true,
        },
      ]
    : messages;

  // Count active RAG options
  const activeRagOptionsCount =
    Object.values(ragOptions).filter(Boolean).length;

  return (
    <div className="min-h-[calc(100vh-7rem)] md:min-h-[calc(100vh-8rem)] flex flex-col">
      {/* Header - Responsive */}
      <div className="mb-4 md:mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 flex-shrink-0">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-[var(--text-primary)] mb-1 flex items-center tracking-tight">
            <span className="gradient-text-vibrant">Document Q&A</span>
            <Sparkles className="h-4 w-4 md:h-5 md:w-5 ml-2 text-amber-400" />
          </h1>
          <p className="text-[var(--text-secondary)] text-xs md:text-sm">
            Ask questions about your uploaded documents
          </p>
        </div>

        {/* Action buttons - horizontal scroll on mobile */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 sm:pb-0 -mx-1 px-1 sm:mx-0 sm:px-0">
          {/* Export Chat Button */}
          {messages.length > 0 && (
            <button
              onClick={async () => {
                try {
                  await exportChatHistory(userId, "markdown");
                  toast.success("Chat history exported");
                } catch (error) {
                  toast.error("Failed to export chat history");
                }
              }}
              className="flex-shrink-0 flex items-center px-3 md:px-4 py-2 rounded-xl text-xs md:text-sm font-medium transition-all duration-200 text-[var(--text-muted)] hover:text-emerald-400 bg-[var(--bg-secondary)]/50 border border-[var(--border-subtle)] hover:border-emerald-500/30 hover:bg-emerald-500/10"
              title="Export chat history (Ctrl+E)"
            >
              <Download className="h-4 w-4 md:mr-2" />
              <span className="hidden md:inline">Export</span>
            </button>
          )}
          {/* Clear Conversation Button */}
          {messages.length > 0 && (
            <button
              onClick={() => {
                if (window.confirm("Clear current conversation?")) {
                  setMessages([]);
                  setStreamingText("");
                  setStreamingCitations([]);
                  toast.success("Conversation cleared");
                }
              }}
              className="flex-shrink-0 flex items-center px-3 md:px-4 py-2 rounded-xl text-xs md:text-sm font-medium transition-all duration-200 text-[var(--text-muted)] hover:text-red-400 bg-[var(--bg-secondary)]/50 border border-[var(--border-subtle)] hover:border-red-500/30 hover:bg-red-500/10"
              title="Clear current conversation (Ctrl+Shift+C)"
            >
              <Trash2 className="h-4 w-4 md:mr-2" />
              <span className="hidden md:inline">Clear</span>
            </button>
          )}
          <button
            onClick={() => setShowRagOptions(!showRagOptions)}
            className={`flex-shrink-0 flex items-center px-3 md:px-4 py-2 rounded-xl text-xs md:text-sm font-medium transition-all duration-200 ${
              showRagOptions
                ? "bg-violet-500/15 text-violet-300 border border-violet-500/25"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)] bg-[var(--bg-secondary)]/50 border border-[var(--border-subtle)] hover:border-violet-500/30"
            }`}
          >
            <Settings2
              className={`h-4 w-4 md:mr-2 ${showRagOptions ? "text-violet-400" : ""}`}
            />
            <span className="hidden md:inline">RAG</span>
            {activeRagOptionsCount > 0 && (
              <span className="ml-1 md:ml-2 bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white text-[10px] px-1.5 py-0.5 rounded-full font-bold">
                {activeRagOptionsCount}
              </span>
            )}
          </button>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className={`flex-shrink-0 flex items-center px-3 md:px-4 py-2 rounded-xl text-xs md:text-sm font-medium transition-all duration-200 ${
              showHistory
                ? "bg-blue-500/15 text-blue-300 border border-blue-500/25"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)] bg-[var(--bg-secondary)]/50 border border-[var(--border-subtle)] hover:border-blue-500/30"
            }`}
          >
            <History
              className={`h-4 w-4 md:mr-2 ${showHistory ? "text-blue-400" : ""}`}
            />
            <span className="hidden md:inline">History</span>
          </button>
        </div>
      </div>

      {/* RAG Options Panel - Responsive */}
      {showRagOptions && (
        <div className="mb-4 md:mb-6 bg-[var(--bg-secondary)]/60 backdrop-blur-sm rounded-xl md:rounded-2xl p-4 md:p-5 border border-[var(--border-subtle)] animate-slideUp transition-colors">
          <div className="flex items-center justify-between mb-4 md:mb-5">
            <div className="flex items-center">
              <div className="p-1.5 md:p-2 rounded-lg md:rounded-xl bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 mr-2 md:mr-3">
                <Sparkles className="h-4 w-4 md:h-5 md:w-5 text-violet-400" />
              </div>
              <div>
                <h3 className="font-semibold text-[var(--text-primary)] text-sm">
                  Advanced RAG
                </h3>
                <p className="text-xs text-[var(--text-secondary)] hidden sm:block">
                  Enhance search quality
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowRagOptions(false)}
              className="p-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--hover-bg)] rounded-lg transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 md:gap-3">
            {/* Query Expansion */}
            <label
              className={`relative flex items-start p-4 rounded-xl border cursor-pointer transition-all duration-200 group ${
                ragOptions.query_expansion
                  ? "bg-violet-500/10 border-violet-500/30"
                  : "bg-[var(--bg-secondary)]/50 border-[var(--border-subtle)] hover:border-violet-500/30"
              }`}
            >
              <input
                type="checkbox"
                checked={ragOptions.query_expansion}
                onChange={(e) =>
                  setRagOptions((prev) => ({
                    ...prev,
                    query_expansion: e.target.checked,
                  }))
                }
                className="sr-only"
              />
              <div
                className={`w-4 h-4 rounded-md border-2 flex items-center justify-center transition-all flex-shrink-0 ${
                  ragOptions.query_expansion
                    ? "bg-gradient-to-br from-violet-500 to-fuchsia-500 border-transparent"
                    : "border-[var(--border-subtle)] group-hover:border-violet-500/50"
                }`}
              >
                {ragOptions.query_expansion && (
                  <svg
                    className="w-2.5 h-2.5 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={3}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                )}
              </div>
              <div className="ml-3">
                <div className="flex items-center">
                  <Sparkles
                    className={`h-3.5 w-3.5 mr-1.5 ${ragOptions.query_expansion ? "text-violet-400" : "text-[var(--text-muted)]"}`}
                  />
                  <span
                    className={`text-sm font-medium ${ragOptions.query_expansion ? "text-[var(--text-primary)]" : "text-[var(--text-secondary)]"}`}
                  >
                    Query Expansion
                  </span>
                </div>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">
                  Multiple query variations
                </p>
              </div>
            </label>

            {/* Hybrid Search */}
            <label
              className={`relative flex items-start p-4 rounded-xl border cursor-pointer transition-all duration-200 group ${
                ragOptions.hybrid_search
                  ? "bg-blue-500/10 border-blue-500/30"
                  : "bg-[var(--bg-secondary)]/50 border-[var(--border-subtle)] hover:border-blue-500/30"
              }`}
            >
              <input
                type="checkbox"
                checked={ragOptions.hybrid_search}
                onChange={(e) =>
                  setRagOptions((prev) => ({
                    ...prev,
                    hybrid_search: e.target.checked,
                  }))
                }
                className="sr-only"
              />
              <div
                className={`w-4 h-4 rounded-md border-2 flex items-center justify-center transition-all flex-shrink-0 ${
                  ragOptions.hybrid_search
                    ? "bg-gradient-to-br from-blue-500 to-cyan-500 border-transparent"
                    : "border-[var(--border-subtle)] group-hover:border-blue-500/50"
                }`}
              >
                {ragOptions.hybrid_search && (
                  <svg
                    className="w-2.5 h-2.5 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={3}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                )}
              </div>
              <div className="ml-3">
                <div className="flex items-center">
                  <Search
                    className={`h-3.5 w-3.5 mr-1.5 ${ragOptions.hybrid_search ? "text-blue-400" : "text-[var(--text-muted)]"}`}
                  />
                  <span
                    className={`text-sm font-medium ${ragOptions.hybrid_search ? "text-[var(--text-primary)]" : "text-[var(--text-secondary)]"}`}
                  >
                    Hybrid Search
                  </span>
                </div>
                <p className="text-xs text-[var(--text-muted)] mt-1">
                  Semantic + keyword search
                </p>
              </div>
            </label>

            {/* Reranking */}
            <label
              className={`relative flex items-start p-4 rounded-xl border cursor-pointer transition-all duration-200 group ${
                ragOptions.reranking
                  ? "bg-emerald-500/10 border-emerald-500/30"
                  : "bg-[var(--bg-secondary)]/50 border-[var(--border-subtle)] hover:border-emerald-500/30"
              }`}
            >
              <input
                type="checkbox"
                checked={ragOptions.reranking}
                onChange={(e) =>
                  setRagOptions((prev) => ({
                    ...prev,
                    reranking: e.target.checked,
                  }))
                }
                className="sr-only"
              />
              <div
                className={`w-4 h-4 rounded-md border-2 flex items-center justify-center transition-all flex-shrink-0 ${
                  ragOptions.reranking
                    ? "bg-gradient-to-br from-emerald-500 to-teal-500 border-transparent"
                    : "border-[var(--border-subtle)] group-hover:border-emerald-500/50"
                }`}
              >
                {ragOptions.reranking && (
                  <svg
                    className="w-2.5 h-2.5 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={3}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                )}
              </div>
              <div className="ml-3">
                <div className="flex items-center">
                  <BarChart3
                    className={`h-3.5 w-3.5 mr-1.5 ${ragOptions.reranking ? "text-emerald-400" : "text-[var(--text-muted)]"}`}
                  />
                  <span
                    className={`text-sm font-medium ${ragOptions.reranking ? "text-[var(--text-primary)]" : "text-[var(--text-secondary)]"}`}
                  >
                    Reranking
                  </span>
                </div>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">
                  Relevance scoring
                </p>
              </div>
            </label>
          </div>

          {/* Advanced Options Section */}
          <div className="mt-4 pt-4 border-t border-[var(--border-subtle)]">
            <p className="text-xs text-[var(--text-muted)] mb-3 flex items-center">
              <Zap className="h-3 w-3 mr-1.5 text-amber-400" />
              Advanced Options (Experimental)
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {/* Auto Query Rewrite */}
              <label
                className={`relative flex items-start p-4 rounded-xl border cursor-pointer transition-all duration-200 group ${
                  ragOptions.auto_rewrite
                    ? "bg-amber-500/10 border-amber-500/30"
                    : "bg-[var(--bg-secondary)]/50 border-[var(--border-subtle)] hover:border-amber-500/30"
                }`}
              >
                <input
                  type="checkbox"
                  checked={ragOptions.auto_rewrite}
                  onChange={(e) =>
                    setRagOptions((prev) => ({
                      ...prev,
                      auto_rewrite: e.target.checked,
                    }))
                  }
                  className="sr-only"
                />
                <div
                  className={`w-4 h-4 rounded-md border-2 flex items-center justify-center transition-all flex-shrink-0 ${
                    ragOptions.auto_rewrite
                      ? "bg-gradient-to-br from-amber-500 to-orange-500 border-transparent"
                      : "border-[var(--border-subtle)] group-hover:border-amber-500/50"
                  }`}
                >
                  {ragOptions.auto_rewrite && (
                    <svg
                      className="w-2.5 h-2.5 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={3}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  )}
                </div>
                <div className="ml-3">
                  <div className="flex items-center">
                    <Wand2
                      className={`h-3.5 w-3.5 mr-1.5 ${ragOptions.auto_rewrite ? "text-amber-400" : "text-[var(--text-muted)]"}`}
                    />
                    <span
                      className={`text-sm font-medium ${ragOptions.auto_rewrite ? "text-[var(--text-primary)]" : "text-[var(--text-secondary)]"}`}
                    >
                      Auto Rewrite
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-muted)] mt-0.5">
                    LLM improves your query
                  </p>
                </div>
              </label>

              {/* Cross-Encoder Reranking */}
              <label
                className={`relative flex items-start p-4 rounded-xl border cursor-pointer transition-all duration-200 group ${
                  ragOptions.cross_encoder
                    ? "bg-rose-500/10 border-rose-500/30"
                    : "bg-[var(--bg-secondary)]/50 border-[var(--border-subtle)] hover:border-rose-500/30"
                }`}
              >
                <input
                  type="checkbox"
                  checked={ragOptions.cross_encoder}
                  onChange={(e) =>
                    setRagOptions((prev) => ({
                      ...prev,
                      cross_encoder: e.target.checked,
                    }))
                  }
                  className="sr-only"
                />
                <div
                  className={`w-4 h-4 rounded-md border-2 flex items-center justify-center transition-all flex-shrink-0 ${
                    ragOptions.cross_encoder
                      ? "bg-gradient-to-br from-rose-500 to-pink-500 border-transparent"
                      : "border-[var(--border-subtle)] group-hover:border-rose-500/50"
                  }`}
                >
                  {ragOptions.cross_encoder && (
                    <svg
                      className="w-2.5 h-2.5 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={3}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  )}
                </div>
                <div className="ml-3">
                  <div className="flex items-center">
                    <Layers
                      className={`h-3.5 w-3.5 mr-1.5 ${ragOptions.cross_encoder ? "text-rose-400" : "text-[var(--text-muted)]"}`}
                    />
                    <span
                      className={`text-sm font-medium ${ragOptions.cross_encoder ? "text-[var(--text-primary)]" : "text-[var(--text-secondary)]"}`}
                    >
                      Cross-Encoder
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-muted)] mt-0.5">
                    Deep relevance scoring
                  </p>
                </div>
              </label>
            </div>
          </div>

          {activeRagOptionsCount > 0 && (
            <div className="mt-4 pt-4 border-t border-[var(--border-subtle)] flex items-center justify-between">
              <p className="text-xs text-violet-400 flex items-center">
                <Sparkles className="h-3 w-3 mr-1.5" />
                {activeRagOptionsCount} option
                {activeRagOptionsCount > 1 ? "s" : ""} enabled
              </p>
              <span className="text-xs text-[var(--text-muted)]">
                May take longer
              </span>
            </div>
          )}
        </div>
      )}

      {/* History Panel - Mobile optimized */}
      {showHistory && (
        <div className="mb-4 md:mb-6 bg-[var(--bg-secondary)]/60 backdrop-blur-sm rounded-xl md:rounded-2xl p-4 md:p-5 border border-[var(--border-subtle)] animate-slideUp transition-colors">
          <div className="flex items-center justify-between mb-3 md:mb-4">
            <div className="flex items-center">
              <div className="p-1.5 md:p-2 rounded-lg md:rounded-xl bg-blue-500/15 mr-2 md:mr-3">
                <History className="h-4 w-4 md:h-5 md:w-5 text-blue-400" />
              </div>
              <h3 className="font-semibold text-[var(--text-primary)] text-sm">
                Chat History
              </h3>
            </div>
            <div className="flex items-center gap-1 md:gap-2">
              <button
                onClick={handleClearHistory}
                disabled={
                  clearHistoryMutation.isPending || !chatHistory?.length
                }
                className="flex items-center px-2 md:px-3 py-1 md:py-1.5 text-xs text-red-400 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
              >
                <Trash2 className="h-3.5 w-3.5 md:h-4 md:w-4 md:mr-1" />
                <span className="hidden md:inline">Clear All</span>
              </button>
              <button
                onClick={() => setShowHistory(false)}
                className="p-1.5 md:p-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--hover-bg)] rounded-lg transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {chatHistory && chatHistory.length > 0 ? (
            <div className="space-y-2 max-h-48 md:max-h-64 overflow-y-auto custom-scrollbar">
              {chatHistory.map((entry, index) => (
                <button
                  key={entry.id}
                  onClick={() => loadHistoryEntry(entry)}
                  className="w-full text-left p-2.5 md:p-3 bg-[var(--bg-secondary)]/50 hover:bg-[var(--hover-bg)] rounded-lg md:rounded-xl border border-[var(--border-subtle)] hover:border-blue-500/30 transition-all duration-200 group"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <p className="text-sm font-medium text-[var(--text-secondary)] truncate group-hover:text-blue-300 transition-colors">
                    {entry.question}
                  </p>
                  <p className="text-xs text-[var(--text-muted)] mt-1">
                    {new Date(entry.created_at).toLocaleString()} •{" "}
                    <span className="text-blue-400/70">{entry.provider}</span>
                  </p>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-center py-6 md:py-8">
              <div className="inline-flex items-center justify-center w-10 h-10 md:w-12 md:h-12 rounded-lg md:rounded-xl bg-[var(--bg-secondary)]/50 mb-2 md:mb-3">
                <History className="h-5 w-5 md:h-6 md:w-6 text-[var(--text-muted)]" />
              </div>
              <p className="text-sm text-[var(--text-muted)]">
                No chat history yet
              </p>
            </div>
          )}
        </div>
      )}

      {/* Model Selection - Mobile optimized */}
      <div className="mb-4 md:mb-6 bg-[var(--bg-secondary)]/60 backdrop-blur-sm rounded-xl md:rounded-2xl p-4 md:p-5 border border-[var(--border-subtle)] transition-colors">
        <ModelPicker
          selectedProvider={selectedProvider}
          selectedModel={selectedModel}
          onProviderChange={handleProviderChange}
          onModelChange={setSelectedModel}
        />
      </div>

      {/* Main Chat Layout - Mobile stacked, desktop side-by-side */}
      <div className="flex flex-col lg:grid lg:grid-cols-4 gap-4 md:gap-6 flex-1 min-h-[400px] md:min-h-[500px]">
        {/* Left Sidebar - Document Filter (collapsible on mobile) */}
        <div className="order-2 lg:order-1 lg:col-span-1 bg-[var(--bg-secondary)]/60 backdrop-blur-sm rounded-xl md:rounded-2xl border border-[var(--border-subtle)] p-4 md:p-5 overflow-y-auto custom-scrollbar max-h-[300px] lg:max-h-[600px] transition-colors">
          <div className="flex items-center mb-3 md:mb-4">
            <div className="p-1.5 md:p-2 rounded-lg md:rounded-xl bg-amber-500/15 mr-2 md:mr-3">
              <FileText className="h-4 w-4 md:h-5 md:w-5 text-amber-400" />
            </div>
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">
              Documents
            </h2>
          </div>

          <DocumentList
            documents={documents}
            isLoading={docsLoading}
            error={docsError}
            onSelectionChange={setSelectedDocIds}
          />

          {!docsLoading &&
            !docsError &&
            (!documents || documents.length === 0) && (
              <div className="mt-4 p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                <p className="text-xs text-amber-400">
                  No documents available. Upload documents first.
                </p>
              </div>
            )}

          {/* Images Section */}
          <div className="mt-6 pt-6 border-t border-[var(--border-subtle)]">
            <button
              onClick={() => setShowImages(!showImages)}
              className="w-full flex items-center justify-between mb-3"
            >
              <div className="flex items-center">
                <div className="p-2 rounded-xl bg-fuchsia-500/15 mr-3">
                  <Image className="h-5 w-5 text-fuchsia-400" />
                </div>
                <h2 className="text-sm font-semibold text-[var(--text-primary)]">
                  Images
                </h2>
                {selectedImageIds.length > 0 && (
                  <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30">
                    {selectedImageIds.length} selected
                  </span>
                )}
              </div>
              {showImages ? (
                <ChevronUp className="h-4 w-4 text-[var(--text-muted)]" />
              ) : (
                <ChevronDown className="h-4 w-4 text-[var(--text-muted)]" />
              )}
            </button>

            {showImages && (
              <div className="space-y-3">
                {images.length > 0 ? (
                  <>
                    <p className="text-xs text-[var(--text-muted)] mb-2">
                      Select images to ask questions about them
                    </p>
                    <div className="grid grid-cols-2 gap-2">
                      {images.map((img) => (
                        <button
                          key={img.id}
                          onClick={() => {
                            setSelectedImageIds((prev) =>
                              prev.includes(img.id)
                                ? prev.filter((id) => id !== img.id)
                                : [...prev, img.id],
                            );
                          }}
                          className={`relative aspect-square rounded-lg overflow-hidden border-2 transition-all ${
                            selectedImageIds.includes(img.id)
                              ? "border-fuchsia-500 ring-2 ring-fuchsia-500/30"
                              : "border-[var(--border-subtle)] hover:border-[var(--text-muted)]"
                          }`}
                        >
                          <img
                            src={`data:${img.content_type};base64,${img.thumbnail_base64}`}
                            alt={img.filename || "Image"}
                            className="w-full h-full object-cover"
                          />
                          {selectedImageIds.includes(img.id) && (
                            <div className="absolute inset-0 bg-fuchsia-500/20 flex items-center justify-center">
                              <div className="w-6 h-6 rounded-full bg-fuchsia-500 flex items-center justify-center">
                                <svg
                                  className="w-4 h-4 text-white"
                                  fill="none"
                                  viewBox="0 0 24 24"
                                  stroke="currentColor"
                                >
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M5 13l4 4L19 7"
                                  />
                                </svg>
                              </div>
                            </div>
                          )}
                        </button>
                      ))}
                    </div>
                    {selectedImageIds.length > 0 && (
                      <button
                        onClick={() => setSelectedImageIds([])}
                        className="w-full mt-2 text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors"
                      >
                        Clear selection
                      </button>
                    )}
                  </>
                ) : (
                  <div className="p-4 bg-fuchsia-500/10 border border-fuchsia-500/20 rounded-xl">
                    <p className="text-xs text-fuchsia-400">
                      No images uploaded. Go to Upload page to add images.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Side - Chat Interface */}
        <div className="order-1 lg:order-2 lg:col-span-3 bg-[var(--bg-secondary)]/60 backdrop-blur-sm rounded-xl md:rounded-2xl border border-[var(--border-subtle)] flex flex-col min-h-[350px] md:min-h-[500px] max-h-[60vh] lg:max-h-[700px] transition-colors">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 md:p-6 custom-scrollbar">
            {displayMessages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center px-4">
                  <div className="inline-flex items-center justify-center w-12 h-12 md:w-16 md:h-16 rounded-xl md:rounded-2xl bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 mb-4 md:mb-5">
                    <Sparkles className="h-6 w-6 md:h-8 md:w-8 text-violet-400" />
                  </div>
                  <h3 className="text-base md:text-lg font-semibold text-[var(--text-primary)] mb-1.5 md:mb-2">
                    Start a Conversation
                  </h3>
                  <p className="text-[var(--text-muted)] text-xs md:text-sm max-w-sm mx-auto">
                    Ask questions about your documents or select images to
                    analyze
                  </p>
                  <div className="mt-4 md:mt-5 flex flex-wrap justify-center gap-2">
                    <span className="px-2.5 md:px-3 py-1 md:py-1.5 text-xs rounded-full bg-[var(--bg-secondary)]/50 text-[var(--text-secondary)] border border-[var(--border-subtle)]">
                      "What is our leave policy?"
                    </span>
                    <span className="px-2.5 md:px-3 py-1 md:py-1.5 text-xs rounded-full bg-[var(--bg-secondary)]/50 text-[var(--text-secondary)] border border-[var(--border-subtle)] hidden sm:inline-block">
                      "Describe this image"
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <>
                <MessageList messages={displayMessages} isLoading={false} />
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input Area */}
          <div className="border-t border-[var(--border-subtle)] p-3 md:p-4">
            <ChatBox onSendMessage={handleSendMessage} disabled={isStreaming} />
          </div>
        </div>
      </div>
    </div>
  );
}
