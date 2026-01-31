/**
 * Chat page with document filtering and conversation interface.
 * Supports streaming responses and conversation history.
 */
import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import toast from "react-hot-toast";
import { useQueryClient } from "@tanstack/react-query";
import DocumentPreview from "../components/DocumentPreview";
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
  Upload,
  Plus,
  Check,
  Eye,
  Loader2,
  Library,
  Cloud,
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
  useImages,
} from "../hooks/useApi";
import {
  streamChatMessage,
  streamMultimodalChat,
  exportChatHistory,
  uploadDocument,
  uploadImage,
  deleteImage as deleteImageApi,
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
  const [selectedProvider, setSelectedProvider] = useState("openai");
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [selectedImageIds, setSelectedImageIds] = useState([]);
  const [showImages, setShowImages] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showRagOptions, setShowRagOptions] = useState(false);

  // Upload section state
  const [showUploadSection, setShowUploadSection] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  // Upload mode state
  const [uploadMode, setUploadMode] = useState("single"); // 'single' or 'batch'
  const [autoDescribe, setAutoDescribe] = useState(false); // AI description for images - default OFF
  const [pendingImageFile, setPendingImageFile] = useState(null); // File waiting for manual description
  const [pendingImagePreview, setPendingImagePreview] = useState(null);
  const [manualDescription, setManualDescription] = useState("");

  // Library selection state
  const [showLibrarySection, setShowLibrarySection] = useState(true);
  const [showLibraryDocs, setShowLibraryDocs] = useState(false);
  const [showLibraryImages, setShowLibraryImages] = useState(false);
  const [libDocSearch, setLibDocSearch] = useState("");
  const [libImageSearch, setLibImageSearch] = useState("");
  const [previewLibImage, setPreviewLibImage] = useState(null);
  const [deletingImageId, setDeletingImageId] = useState(null);
  const [previewDocument, setPreviewDocument] = useState(null);
  const [deletingDocId, setDeletingDocId] = useState(null);

  const queryClient = useQueryClient();

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

  const { data: images = [], isLoading: imagesLoading } = useImages();

  const { data: chatHistory, refetch: refetchHistory } = useChatHistory(userId);
  const clearHistoryMutation = useClearChatHistory();

  // Filter library items by search - memoized to prevent recalculation on every render
  const filteredLibDocs = useMemo(
    () =>
      (documents || []).filter(
        (d) =>
          d.filename?.toLowerCase().includes(libDocSearch.toLowerCase()) ||
          d.name?.toLowerCase().includes(libDocSearch.toLowerCase()),
      ),
    [documents, libDocSearch],
  );

  const filteredLibImages = useMemo(
    () =>
      (images || []).filter(
        (i) =>
          i.filename?.toLowerCase().includes(libImageSearch.toLowerCase()) ||
          i.name?.toLowerCase().includes(libImageSearch.toLowerCase()),
      ),
    [images, libImageSearch],
  );

  // Upload handlers
  const handleFiles = async (files) => {
    if (!files || files.length === 0) return;

    const fileArray = Array.from(files);

    for (const file of fileArray) {
      try {
        const isImage =
          file.type.startsWith("image/") ||
          file.name.toLowerCase().endsWith(".heic") ||
          file.name.toLowerCase().endsWith(".heif");

        if (isImage) {
          // If auto describe is off, show the manual description form
          if (!autoDescribe) {
            const preview = URL.createObjectURL(file);
            setPendingImageFile(file);
            setPendingImagePreview(preview);
            setManualDescription("");
            return; // Wait for user to enter description
          }
          // Auto describe - upload immediately
          setIsUploading(true);
          const result = await uploadImage(file, "", true);
          setSelectedImageIds((prev) => [...prev, result.id]);
          toast.success(`Image uploaded: ${file.name}`);
        } else {
          // For documents (PDFs, etc.), upload immediately
          setIsUploading(true);
          const result = await uploadDocument(file);
          setSelectedDocIds((prev) => [...prev, result.id]);
          toast.success(`Document uploaded: ${file.name}`);
        }
      } catch (err) {
        console.error("Upload failed:", err);
        toast.error(`Failed to upload ${file.name}: ${err.message}`);
      }
    }

    // Refresh library
    queryClient.invalidateQueries({ queryKey: ["documents"] });
    queryClient.invalidateQueries({ queryKey: ["images"] });
    setIsUploading(false);
  };

  // Handle manual image upload with description
  const handleManualImageUpload = async (useAI = false) => {
    if (!pendingImageFile) return;

    setIsUploading(true);
    try {
      const result = await uploadImage(
        pendingImageFile,
        useAI ? "" : manualDescription,
        useAI,
      );
      setSelectedImageIds((prev) => [...prev, result.id]);
      toast.success(`Image uploaded: ${pendingImageFile.name}`);

      // Clear pending state
      setPendingImageFile(null);
      setPendingImagePreview(null);
      setManualDescription("");

      // Refresh library
      queryClient.invalidateQueries({ queryKey: ["images"] });
    } catch (err) {
      console.error("Upload failed:", err);
      toast.error(`Failed to upload: ${err.message}`);
    }
    setIsUploading(false);
  };

  const cancelPendingUpload = () => {
    if (pendingImagePreview) {
      URL.revokeObjectURL(pendingImagePreview);
    }
    setPendingImageFile(null);
    setPendingImagePreview(null);
    setManualDescription("");
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleFiles(e.dataTransfer?.files);
  };

  // Library selection handlers - memoized to prevent child re-renders
  const toggleLibDocSelection = useCallback((id) => {
    setSelectedDocIds((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id],
    );
  }, []);

  const toggleLibImageSelection = useCallback((id) => {
    setSelectedImageIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id],
    );
  }, []);

  const selectAllLibDocs = useCallback(() => {
    setSelectedDocIds(filteredLibDocs.map((d) => d.id));
  }, [filteredLibDocs]);

  const deselectAllLibDocs = useCallback(() => {
    setSelectedDocIds([]);
  }, []);

  const selectAllLibImages = useCallback(() => {
    setSelectedImageIds(filteredLibImages.map((i) => i.id));
  }, [filteredLibImages]);

  const deselectAllLibImages = useCallback(() => {
    setSelectedImageIds([]);
  }, []);

  const handleDeleteLibImage = async (e, imageId) => {
    e.stopPropagation();
    if (deletingImageId) return;

    // Ask for confirmation
    if (
      !window.confirm(
        "Are you sure you want to delete this image? This action cannot be undone.",
      )
    ) {
      return;
    }

    setDeletingImageId(imageId);
    try {
      await deleteImageApi(imageId);
      setSelectedImageIds((prev) => prev.filter((id) => id !== imageId));
      queryClient.invalidateQueries({ queryKey: ["images"] });
      toast.success("Image deleted");
    } catch (err) {
      console.error("Delete failed:", err);
      toast.error("Failed to delete image");
    } finally {
      setDeletingImageId(null);
    }
  };

  const handlePreviewDocument = (doc) => {
    setPreviewDocument(doc);
  };

  const handleDeleteDocument = async (doc) => {
    if (deletingDocId) return;

    if (!confirm(`Delete "${doc.filename || doc.name}"?`)) return;

    setDeletingDocId(doc.id);
    try {
      await fetch(`http://localhost:8001/api/docs/${doc.id}`, {
        method: "DELETE",
      });
      setSelectedDocIds((prev) => prev.filter((id) => id !== doc.id));
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      toast.success("Document deleted");
    } catch (err) {
      console.error("Delete failed:", err);
      toast.error("Failed to delete document");
    } finally {
      setDeletingDocId(null);
    }
  };

  // Sync streaming text to ref for onDone callback
  useEffect(() => {
    finalContentRef.current = streamingText;
  }, [streamingText]);

  useEffect(() => {
    finalCitationsRef.current = streamingCitations;
  }, [streamingCitations]);

  // Auto-scroll only if user is already near bottom
  useEffect(() => {
    const scrollContainer = messagesEndRef.current?.parentElement;
    if (!scrollContainer) return;

    const isNearBottom =
      scrollContainer.scrollHeight -
        scrollContainer.scrollTop -
        scrollContainer.clientHeight <
      100;

    if (isNearBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
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

  const handleProviderChange = useCallback((newProvider) => {
    setSelectedProvider(newProvider);
    setSelectedModel("");
  }, []);

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

  const handleClearHistory = useCallback(() => {
    if (window.confirm("Are you sure you want to clear all chat history?")) {
      clearHistoryMutation.mutate(userId);
    }
  }, [clearHistoryMutation, userId]);

  const loadHistoryEntry = useCallback((entry) => {
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
  }, []);

  // Build display messages - memoized to prevent array recreation
  const displayMessages = useMemo(
    () =>
      isStreaming
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
        : messages,
    [isStreaming, messages, streamingText, streamingCitations],
  );

  // Count active RAG options - memoized
  const activeRagOptionsCount = useMemo(
    () => Object.values(ragOptions).filter(Boolean).length,
    [ragOptions],
  );

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
            className={`flex-shrink-0 flex items-center px-3 md:px-4 py-2 rounded-xl text-xs md:text-sm font-bold transition-all duration-200 shadow-lg ${
              showRagOptions
                ? "bg-gradient-to-r from-violet-600 to-purple-600 text-white border-2 border-violet-400 shadow-violet-500/50"
                : "bg-gradient-to-r from-violet-500/20 to-purple-500/20 text-violet-300 border-2 border-violet-500/40 hover:from-violet-500/30 hover:to-purple-500/30 hover:border-violet-400/60 hover:text-white hover:shadow-violet-500/30"
            }`}
          >
            <Settings2
              className={`h-4 w-4 md:mr-2 ${showRagOptions ? "text-white" : "text-violet-400"}`}
            />
            <span className="hidden md:inline">Advanced Options</span>
            {activeRagOptionsCount > 0 && (
              <span className="ml-1 md:ml-2 bg-gradient-to-r from-yellow-400 to-orange-500 text-gray-900 text-[10px] px-1.5 py-0.5 rounded-full font-bold shadow-md">
                {activeRagOptionsCount}
              </span>
            )}
          </button>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className={`flex-shrink-0 flex items-center px-3 md:px-4 py-2 rounded-xl text-xs md:text-sm font-bold transition-all duration-200 shadow-lg ${
              showHistory
                ? "bg-gradient-to-r from-blue-600 to-cyan-600 text-white border-2 border-blue-400 shadow-blue-500/50"
                : "bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-blue-300 border-2 border-blue-500/40 hover:from-blue-500/30 hover:to-cyan-500/30 hover:border-blue-400/60 hover:text-white hover:shadow-blue-500/30"
            }`}
          >
            <History
              className={`h-4 w-4 md:mr-2 ${showHistory ? "text-white" : "text-blue-400"}`}
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

      {/* Upload Section - Expandable */}
      <div className="mb-4 md:mb-6 bg-[var(--bg-secondary)]/60 backdrop-blur-sm rounded-xl md:rounded-2xl border border-[var(--border-subtle)] transition-colors overflow-hidden">
        <button
          onClick={() => setShowUploadSection(!showUploadSection)}
          className="w-full flex items-center justify-between p-4 md:p-5 hover:bg-[var(--hover-bg)] transition-colors"
        >
          <div className="flex items-center">
            <div className="p-1.5 md:p-2 rounded-lg md:rounded-xl bg-emerald-500/15 mr-2 md:mr-3">
              <Upload className="h-4 w-4 md:h-5 md:w-5 text-emerald-400" />
            </div>
            <div className="text-left">
              <h3 className="font-semibold text-[var(--text-primary)] text-sm">
                Upload Files
              </h3>
              <p className="text-xs text-[var(--text-muted)]">
                Add documents or images to chat about
              </p>
            </div>
          </div>
          {showUploadSection ? (
            <ChevronUp className="h-4 w-4 text-[var(--text-muted)]" />
          ) : (
            <ChevronDown className="h-4 w-4 text-[var(--text-muted)]" />
          )}
        </button>

        {showUploadSection && (
          <div className="px-4 md:px-5 pb-4 md:pb-5 border-t border-[var(--border-subtle)]">
            {/* Top Row: Single/Batch Toggle + Auto-describe option */}
            <div className="flex items-center justify-between mt-4 mb-4 flex-wrap gap-3">
              {/* Single / Batch Toggle */}
              <div className="flex gap-1 p-1 bg-[var(--bg-tertiary)] rounded-full w-fit">
                <button
                  onClick={() => setUploadMode("single")}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                    uploadMode === "single"
                      ? "bg-violet-500 text-white shadow-md"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  Single
                </button>
                <button
                  onClick={() => setUploadMode("batch")}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                    uploadMode === "batch"
                      ? "bg-violet-500 text-white shadow-md"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  Batch
                </button>
              </div>

              {/* Auto-describe toggle */}
              <button
                onClick={() => setAutoDescribe(!autoDescribe)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all border ${
                  autoDescribe
                    ? "bg-violet-500/20 border-violet-500/50 text-violet-300"
                    : "bg-[var(--bg-tertiary)] border-[var(--border-subtle)] text-[var(--text-secondary)] hover:border-violet-500/30"
                }`}
              >
                <Wand2
                  className={`w-4 h-4 ${autoDescribe ? "text-violet-400" : "text-[var(--text-muted)]"}`}
                />
                <span>Auto AI description</span>
                <div
                  className={`w-8 h-4 rounded-full relative transition-all ${
                    autoDescribe ? "bg-violet-500" : "bg-[var(--bg-secondary)]"
                  }`}
                >
                  <div
                    className={`absolute top-0.5 w-3 h-3 rounded-full bg-white transition-all ${
                      autoDescribe ? "left-4" : "left-0.5"
                    }`}
                  />
                </div>
              </button>
            </div>

            {/* Pending Image - Manual Description Form */}
            {pendingImageFile && !isUploading && (
              <div className="mb-4 p-6 bg-[var(--bg-tertiary)] rounded-xl border border-[var(--border-subtle)]">
                <div className="space-y-4">
                  {/* Image Preview and Info */}
                  <div className="flex items-start gap-4">
                    <img
                      src={pendingImagePreview}
                      alt="Preview"
                      className="w-48 h-48 object-cover rounded-lg border-2 border-[var(--border-subtle)] shadow-lg"
                    />
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-base font-semibold text-[var(--text-primary)]">
                            {pendingImageFile.name}
                          </p>
                          <p className="text-xs text-[var(--text-muted)] mt-1">
                            {(pendingImageFile.size / 1024 / 1024).toFixed(2)}{" "}
                            MB
                          </p>
                        </div>
                        <button
                          onClick={cancelPendingUpload}
                          className="text-xs text-[var(--text-muted)] hover:text-red-400 transition-colors px-3 py-1 rounded-lg hover:bg-red-500/10"
                        >
                          Cancel
                        </button>
                      </div>
                      {/* Show current description if entered */}
                      {manualDescription.trim() && (
                        <div className="mt-3 p-3 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)]">
                          <p className="text-xs font-medium text-violet-400 mb-1">
                            Description:
                          </p>
                          <p className="text-sm text-[var(--text-primary)]">
                            {manualDescription}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Description Input */}
                  <div>
                    <label className="text-xs font-medium text-[var(--text-secondary)] mb-2 block">
                      Image Description (Optional)
                    </label>
                    <textarea
                      value={manualDescription}
                      onChange={(e) => setManualDescription(e.target.value)}
                      placeholder="Enter image description..."
                      className="w-full px-4 py-3 text-sm bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg
                                 text-[var(--text-primary)] placeholder-[var(--text-muted)] resize-none
                                 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                      rows={3}
                      autoFocus
                    />
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-3">
                    <button
                      onClick={() => handleManualImageUpload(false)}
                      className="flex-1 px-4 py-2.5 rounded-lg text-sm font-medium bg-violet-500 hover:bg-violet-400 text-white transition-all shadow-lg shadow-violet-500/20"
                    >
                      {manualDescription.trim()
                        ? "Upload with Description"
                        : "Upload without Description"}
                    </button>
                    <button
                      onClick={() => handleManualImageUpload(true)}
                      className="px-4 py-2.5 rounded-lg text-sm font-medium bg-[var(--bg-secondary)] hover:bg-[var(--hover-bg)] 
                                 text-[var(--text-secondary)] transition-all border border-[var(--border-subtle)] flex items-center gap-2"
                    >
                      <Wand2 className="w-4 h-4" />
                      Use AI
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Drop Zone */}
            {!pendingImageFile && (
              <div
                onClick={() => fileInputRef.current?.click()}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`relative border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all bg-gradient-to-b from-[var(--bg-primary)] to-[var(--bg-secondary)]/50 ${
                  dragActive
                    ? "border-violet-500 bg-violet-500/5"
                    : "border-[var(--border-subtle)] hover:border-violet-400/50"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple={uploadMode === "batch"}
                  accept=".pdf,.doc,.docx,.txt,.md,.json,.csv,image/*,.heic,.heif"
                  onChange={(e) => handleFiles(e.target.files)}
                  className="hidden"
                />
                {isUploading ? (
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-16 h-16 rounded-2xl bg-violet-500/15 flex items-center justify-center">
                      <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
                    </div>
                    <p className="text-sm text-[var(--text-secondary)]">
                      {autoDescribe
                        ? "Generating AI description..."
                        : "Uploading..."}
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-3">
                    <div
                      className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all ${
                        dragActive
                          ? "bg-violet-500/25 scale-110"
                          : "bg-violet-500/15"
                      }`}
                    >
                      <Cloud
                        className={`w-8 h-8 transition-colors ${
                          dragActive ? "text-violet-300" : "text-violet-400"
                        }`}
                      />
                    </div>
                    <div className="text-center">
                      <p className="text-base font-semibold text-[var(--text-primary)]">
                        Drop your file{uploadMode === "batch" ? "s" : ""} here
                        or click to browse
                      </p>
                      <p className="text-sm text-[var(--text-muted)] mt-1">
                        Supported: PDF, Word, TXT, Images (max 15MB)
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Library Selection Section - Expandable */}
      <div className="mb-4 md:mb-6 bg-[var(--bg-secondary)]/60 backdrop-blur-sm rounded-xl md:rounded-2xl border border-[var(--border-subtle)] transition-colors overflow-hidden">
        <button
          onClick={() => setShowLibrarySection(!showLibrarySection)}
          className="w-full flex items-center justify-between p-4 md:p-5 hover:bg-[var(--hover-bg)] transition-colors"
        >
          <div className="flex items-center">
            <div className="p-1.5 md:p-2 rounded-lg md:rounded-xl bg-violet-500/15 mr-2 md:mr-3">
              <Library className="h-4 w-4 md:h-5 md:w-5 text-violet-400" />
            </div>
            <div className="text-left">
              <h3 className="font-semibold text-[var(--text-primary)] text-sm">
                Select from Library
              </h3>
              <p className="text-xs text-[var(--text-muted)]">
                {(documents || []).length} docs, {(images || []).length} images
                {(selectedDocIds.length > 0 || selectedImageIds.length > 0) && (
                  <span className="ml-2 text-violet-400">
                    ({selectedDocIds.length + selectedImageIds.length} selected)
                  </span>
                )}
              </p>
            </div>
          </div>
          {showLibrarySection ? (
            <ChevronUp className="h-4 w-4 text-[var(--text-muted)]" />
          ) : (
            <ChevronDown className="h-4 w-4 text-[var(--text-muted)]" />
          )}
        </button>

        {showLibrarySection && (
          <div className="px-4 md:px-5 pb-4 md:pb-5 border-t border-[var(--border-subtle)] space-y-3">
            {/* Library Documents Accordion */}
            <div className="mt-4 border border-[var(--border-subtle)] rounded-lg overflow-hidden">
              <button
                onClick={() => setShowLibraryDocs(!showLibraryDocs)}
                className="w-full flex items-center justify-between px-3 py-2 bg-[var(--bg-tertiary)] hover:bg-[var(--bg-tertiary)]/80 transition-colors"
              >
                <span className="text-sm text-[var(--text-primary)] flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-400" />
                  Documents ({(documents || []).length})
                  {selectedDocIds.length > 0 && (
                    <span className="text-xs px-1.5 py-0.5 bg-violet-500/20 text-violet-400 rounded">
                      {selectedDocIds.length} selected
                    </span>
                  )}
                </span>
                {showLibraryDocs ? (
                  <ChevronUp className="w-4 h-4 text-[var(--text-muted)]" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-[var(--text-muted)]" />
                )}
              </button>

              {showLibraryDocs && (
                <div className="p-2 space-y-2">
                  {/* Search & Actions */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={libDocSearch}
                      onChange={(e) => setLibDocSearch(e.target.value)}
                      placeholder="Search documents..."
                      className="flex-1 px-2 py-1 text-xs bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-violet-500/50"
                    />
                    <button
                      onClick={selectAllLibDocs}
                      className="text-xs px-2 py-1 text-violet-400 hover:bg-violet-500/10 rounded transition-colors"
                    >
                      All
                    </button>
                    <button
                      onClick={deselectAllLibDocs}
                      className="text-xs px-2 py-1 text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)] rounded transition-colors"
                    >
                      None
                    </button>
                  </div>

                  {/* Document List */}
                  <div className="max-h-[200px] overflow-y-auto space-y-1">
                    {docsLoading ? (
                      <div className="flex items-center justify-center py-4">
                        <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />
                      </div>
                    ) : filteredLibDocs.length === 0 ? (
                      <p className="text-xs text-[var(--text-muted)] py-2 text-center">
                        {libDocSearch
                          ? "No matching documents"
                          : "No documents in library"}
                      </p>
                    ) : (
                      filteredLibDocs.map((doc) => (
                        <div
                          key={doc.id}
                          className={`group flex items-center gap-2 px-2 py-1.5 rounded transition-colors ${
                            selectedDocIds.includes(doc.id)
                              ? "bg-violet-500/20 border border-violet-500/30"
                              : "hover:bg-[var(--bg-tertiary)] border border-transparent"
                          }`}
                        >
                          <div
                            className={`w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 cursor-pointer ${
                              selectedDocIds.includes(doc.id)
                                ? "bg-violet-500 border-violet-500"
                                : "border-[var(--border-subtle)]"
                            }`}
                            onClick={() => toggleLibDocSelection(doc.id)}
                          >
                            {selectedDocIds.includes(doc.id) && (
                              <Check className="w-3 h-3 text-white" />
                            )}
                          </div>
                          <span
                            className="text-xs text-[var(--text-primary)] truncate cursor-pointer"
                            onClick={() => toggleLibDocSelection(doc.id)}
                          >
                            {doc.filename || doc.name}
                          </span>
                          <div className="flex items-center gap-1 ml-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handlePreviewDocument(doc);
                              }}
                              className="p-1 hover:bg-blue-500/20 rounded text-blue-400 transition-colors"
                              title="Preview document"
                            >
                              <Eye className="w-3 h-3" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteDocument(doc);
                              }}
                              className="p-1 hover:bg-red-500/20 rounded text-red-400 transition-colors"
                              title="Delete document"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Library Images Accordion */}
            <div className="border border-[var(--border-subtle)] rounded-lg overflow-hidden">
              <button
                onClick={() => setShowLibraryImages(!showLibraryImages)}
                className="w-full flex items-center justify-between px-3 py-2 bg-[var(--bg-tertiary)] hover:bg-[var(--bg-tertiary)]/80 transition-colors"
              >
                <span className="text-sm text-[var(--text-primary)] flex items-center gap-2">
                  <Image className="w-4 h-4 text-green-400" />
                  Images ({(images || []).length})
                  {selectedImageIds.length > 0 && (
                    <span className="text-xs px-1.5 py-0.5 bg-violet-500/20 text-violet-400 rounded">
                      {selectedImageIds.length} selected
                    </span>
                  )}
                </span>
                {showLibraryImages ? (
                  <ChevronUp className="w-4 h-4 text-[var(--text-muted)]" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-[var(--text-muted)]" />
                )}
              </button>

              {showLibraryImages && (
                <div className="p-2 space-y-2">
                  {/* Search & Actions */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={libImageSearch}
                      onChange={(e) => setLibImageSearch(e.target.value)}
                      placeholder="Search images..."
                      className="flex-1 px-2 py-1 text-xs bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-violet-500/50"
                    />
                    <button
                      onClick={selectAllLibImages}
                      className="text-xs px-2 py-1 text-violet-400 hover:bg-violet-500/10 rounded transition-colors"
                    >
                      All
                    </button>
                    <button
                      onClick={deselectAllLibImages}
                      className="text-xs px-2 py-1 text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)] rounded transition-colors"
                    >
                      None
                    </button>
                  </div>

                  {/* Image Grid with Thumbnails */}
                  <div className="max-h-[250px] overflow-y-auto">
                    {imagesLoading ? (
                      <div className="flex items-center justify-center py-4">
                        <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />
                      </div>
                    ) : filteredLibImages.length === 0 ? (
                      <p className="text-xs text-[var(--text-muted)] py-4 text-center">
                        {libImageSearch
                          ? "No matching images"
                          : "No images in library"}
                      </p>
                    ) : (
                      <div className="grid grid-cols-4 md:grid-cols-6 gap-2">
                        {filteredLibImages.map((img) => (
                          <div
                            key={img.id}
                            className={`relative group cursor-pointer rounded-lg overflow-hidden border-2 transition-colors ${
                              selectedImageIds.includes(img.id)
                                ? "border-violet-500"
                                : "border-transparent hover:border-[var(--border-subtle)]"
                            }`}
                            onClick={() => toggleLibImageSelection(img.id)}
                          >
                            {/* Thumbnail */}
                            <div className="aspect-square bg-[var(--bg-tertiary)]">
                              {img.thumbnail_base64 ? (
                                <img
                                  src={`data:image/png;base64,${img.thumbnail_base64}`}
                                  alt={img.filename || img.name}
                                  className="w-full h-full object-cover"
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center">
                                  <Image className="w-4 h-4 text-[var(--text-muted)]" />
                                </div>
                              )}
                            </div>

                            {/* Selection indicator */}
                            <div
                              className={`absolute top-1 left-1 w-4 h-4 rounded border flex items-center justify-center ${
                                selectedImageIds.includes(img.id)
                                  ? "bg-violet-500 border-violet-500"
                                  : "bg-black/50 border-white/30"
                              }`}
                            >
                              {selectedImageIds.includes(img.id) && (
                                <Check className="w-2.5 h-2.5 text-white" />
                              )}
                            </div>

                            {/* Actions overlay */}
                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setPreviewLibImage(img);
                                }}
                                className="p-2 bg-white/20 rounded hover:bg-white/30 transition-colors"
                                title="Preview"
                              >
                                <Eye className="w-5 h-5 text-white" />
                              </button>
                              <button
                                onClick={(e) => handleDeleteLibImage(e, img.id)}
                                disabled={deletingImageId === img.id}
                                className="p-2 bg-red-500/50 rounded hover:bg-red-500/70 transition-colors disabled:opacity-50"
                                title="Delete"
                              >
                                {deletingImageId === img.id ? (
                                  <Loader2 className="w-5 h-5 text-white animate-spin" />
                                ) : (
                                  <Trash2 className="w-5 h-5 text-white" />
                                )}
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Main Chat Layout - Full width */}
      <div className="flex flex-col flex-1 min-h-[400px] md:min-h-[500px]">
        {/* Chat Interface - Full Width */}
        <div className="bg-[var(--bg-secondary)]/60 backdrop-blur-sm rounded-xl md:rounded-2xl border border-[var(--border-subtle)] flex flex-col min-h-[350px] md:min-h-[500px] max-h-[60vh] lg:max-h-[700px] transition-colors flex-1">
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

      {/* Library Image Preview Modals */}
      {previewLibImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-6"
          onClick={() => setPreviewLibImage(null)}
        >
          <div
            className="relative w-full max-w-7xl h-[95vh] flex flex-col gap-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="relative flex-1 flex items-center justify-center overflow-hidden">
              {previewLibImage.thumbnail_base64 ? (
                <img
                  src={`data:image/png;base64,${previewLibImage.thumbnail_base64}`}
                  alt={previewLibImage.filename || previewLibImage.name}
                  className="w-full h-full object-contain rounded-lg shadow-2xl"
                />
              ) : (
                <div className="w-64 h-64 bg-[var(--bg-tertiary)] rounded-lg flex items-center justify-center">
                  <Image className="w-16 h-16 text-[var(--text-muted)]" />
                </div>
              )}
              <button
                onClick={() => setPreviewLibImage(null)}
                className="absolute top-2 right-2 p-2 bg-black/50 rounded-full hover:bg-black/70 transition-colors"
              >
                <X className="w-5 h-5 text-white" />
              </button>
            </div>

            {/* Image Info Card */}
            <div className="bg-[var(--bg-secondary)] rounded-lg p-6 border border-[var(--border-subtle)] max-h-[40vh] overflow-y-auto">
              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium text-[var(--text-muted)] mb-2">
                    Filename
                  </p>
                  <p className="text-lg font-semibold text-[var(--text-primary)]">
                    {previewLibImage.filename || previewLibImage.name}
                  </p>
                </div>
                {previewLibImage.description && (
                  <div>
                    <p className="text-sm font-medium text-[var(--text-muted)] mb-2">
                      Description
                    </p>
                    <p className="text-base text-[var(--text-secondary)] leading-relaxed">
                      {previewLibImage.description}
                    </p>
                  </div>
                )}
                {!previewLibImage.description && (
                  <p className="text-sm text-[var(--text-muted)] italic">
                    No description available
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Document Preview Modal */}
      <DocumentPreview
        docId={previewDocument?.id}
        filename={previewDocument?.filename || previewDocument?.name}
        isOpen={!!previewDocument}
        onClose={() => setPreviewDocument(null)}
      />
    </div>
  );
}
