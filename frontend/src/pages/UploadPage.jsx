/**
 * Upload page for document and image management (multimodal).
 */
import { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Upload,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  Trash2,
  FileText,
  Sparkles,
  Eye,
  Image as ImageIcon,
  X,
  Loader2,
  Tag,
  Folder,
  Edit2,
} from "lucide-react";
import FileDrop from "../components/FileDrop";
import DocumentPreview from "../components/DocumentPreview";
import ImageUpload from "../components/ImageUpload";
import ImageGallery from "../components/ImageGallery";
import DocumentCategoryEditor, {
  CategoryBadge,
  TagBadge,
} from "../components/DocumentCategoryEditor";
import {
  useUploadDocument,
  useUploadDocumentsBatch,
  useDocuments,
  useDeleteDocument,
  useBulkDeleteDocuments,
} from "../hooks/useApi";
import {
  getImages,
  uploadDocumentsWithProgress,
  updateDocument,
} from "../api/client";

export default function UploadPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("documents"); // "documents" | "images"
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadMode, setUploadMode] = useState("single"); // "single" | "batch"
  const [uploadStatus, setUploadStatus] = useState(null);
  const [selectedDocs, setSelectedDocs] = useState(new Set());
  const [previewDoc, setPreviewDoc] = useState(null);

  // Category state
  const [selectedCategory, setSelectedCategory] = useState("");

  // Batch upload progress state
  const [batchProgress, setBatchProgress] = useState([]);
  const [isBatchUploading, setIsBatchUploading] = useState(false);

  // Document editing state
  const [editingDoc, setEditingDoc] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState(null);

  // Image state
  const [images, setImages] = useState([]);
  const [imagesLoading, setImagesLoading] = useState(false);

  const uploadMutation = useUploadDocument();
  const uploadBatchMutation = useUploadDocumentsBatch();
  const {
    data: documents,
    refetch: refetchDocuments,
    isLoading: documentsLoading,
    error: documentsError,
  } = useDocuments();
  const deleteDocMutation = useDeleteDocument();
  const bulkDeleteMutation = useBulkDeleteDocuments();

  // Debug logging
  useEffect(() => {
    console.log("[UploadPage] Documents data:", {
      documents,
      count: documents?.length,
      isLoading: documentsLoading,
      error: documentsError,
    });
  }, [documents, documentsLoading, documentsError]);

  // Load images when tab changes
  useEffect(() => {
    if (activeTab === "images") {
      loadImages();
    }
  }, [activeTab]);

  const loadImages = async () => {
    try {
      setImagesLoading(true);
      const data = await getImages();
      setImages(data);
    } catch (error) {
      console.error("Failed to load images:", error);
    } finally {
      setImagesLoading(false);
    }
  };

  const handleFileSelect = useCallback((file) => {
    setSelectedFile(file);
    setUploadStatus(null);

    // Auto-suggest category based on filename
    const filename = file.name.toLowerCase();
    if (filename.includes("policy") || filename.includes("policies")) {
      setSelectedCategory("policy");
    } else if (
      filename.includes("contract") ||
      filename.includes("agreement") ||
      filename.includes("nda")
    ) {
      setSelectedCategory("contract");
    } else if (
      filename.includes("legal") ||
      filename.includes("compliance") ||
      filename.includes("regulation")
    ) {
      setSelectedCategory("legal");
    } else if (
      filename.includes("procedure") ||
      filename.includes("sop") ||
      filename.includes("workflow")
    ) {
      setSelectedCategory("procedure");
    } else if (
      filename.includes("guide") ||
      filename.includes("manual") ||
      filename.includes("handbook")
    ) {
      setSelectedCategory("guide");
    } else if (filename.includes("form") || filename.includes("application")) {
      setSelectedCategory("form");
    } else if (filename.includes("report") || filename.includes("analysis")) {
      setSelectedCategory("report");
    } else {
      setSelectedCategory("general");
    }
  }, []);

  const handleFilesSelect = useCallback((files) => {
    setSelectedFiles(files);
    setUploadStatus(null);
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploadStatus({
        type: "loading",
        message: "Uploading and indexing...",
      });

      const result = await uploadMutation.mutateAsync({
        file: selectedFile,
        category: selectedCategory || null,
      });

      // Refetch documents list to show newly uploaded document
      refetchDocuments();

      setUploadStatus({
        type: "success",
        message: `✓ Uploaded, embedded & indexed: ${result.filename}`,
      });

      // Reset after 2 seconds
      setTimeout(() => {
        setSelectedFile(null);
        setSelectedCategory("");
        setUploadStatus(null);
      }, 2000);
    } catch (error) {
      setUploadStatus({
        type: "error",
        message: error.response?.data?.detail || "Failed to upload document",
      });
    }
  };

  const handleBatchUpload = async () => {
    if (selectedFiles.length === 0) return;

    setIsBatchUploading(true);
    // Initialize progress for all files
    setBatchProgress(
      selectedFiles.map((file) => ({
        filename: file.name,
        status: "pending",
        percent: 0,
      })),
    );

    try {
      const results = await uploadDocumentsWithProgress(
        selectedFiles,
        (fileIndex, filename, status, percent) => {
          setBatchProgress((prev) => {
            const updated = [...prev];
            updated[fileIndex] = { filename, status, percent };
            return updated;
          });
        },
      );

      const successCount = results.filter((r) => r.status === "success").length;
      const failCount = results.filter((r) => r.status === "error").length;

      // Refetch documents list
      refetchDocuments();

      if (failCount > 0) {
        setUploadStatus({
          type: "success",
          message: `✓ ${successCount} file(s) embedded & indexed, ${failCount} failed`,
        });
      } else {
        setUploadStatus({
          type: "success",
          message: `✓ ${successCount} file(s) uploaded, embedded & indexed`,
        });
      }

      // Clear after delay
      setTimeout(() => {
        setSelectedFiles([]);
        setBatchProgress([]);
        setUploadStatus(null);
        setIsBatchUploading(false);
      }, 3000);
    } catch (error) {
      setUploadStatus({
        type: "error",
        message: error.message || "Failed to upload documents",
      });
      setIsBatchUploading(false);
    }
  };

  const handleImageUploadSuccess = async (result) => {
    // Reload images to get complete data including thumbnail_base64
    await loadImages();
    setUploadStatus({
      type: "success",
      message: `✓ Image uploaded & indexed: ${result.filename}`,
    });
    setTimeout(() => setUploadStatus(null), 3000);
  };

  const handleImageUploadError = (error) => {
    setUploadStatus({
      type: "error",
      message: error,
    });
  };

  const handleImageDelete = (imageId) => {
    setImages((prev) => prev.filter((img) => img.id !== imageId));
  };

  const handleUpdateDocCategory = async (docId, category, tags) => {
    try {
      await updateDocument(docId, { category, tags });
      refetchDocuments();
      setEditingDoc(null);
    } catch (error) {
      console.error("Failed to update document:", error);
    }
  };

  // Filter documents by category - memoized
  const filteredDocuments = useMemo(() => {
    if (!documents) return [];
    if (!categoryFilter) return documents;
    if (categoryFilter === "uncategorized")
      return documents.filter((doc) => !doc.category);
    return documents.filter((doc) => doc.category === categoryFilter);
  }, [documents, categoryFilter]);

  const toggleDocSelection = useCallback(
    (docId) => {
      const newSelected = new Set(selectedDocs);
      if (newSelected.has(docId)) {
        newSelected.delete(docId);
      } else {
        newSelected.add(docId);
      }
      setSelectedDocs(newSelected);
    },
    [selectedDocs],
  );

  const handleSelectAll = useCallback(() => {
    if (selectedDocs.size === documents?.length) {
      setSelectedDocs(new Set());
    } else {
      setSelectedDocs(new Set(documents?.map((d) => d.id) || []));
    }
  }, [selectedDocs.size, documents]);

  const handleDeleteSelected = () => {
    if (selectedDocs.size === 0) return;

    const count = selectedDocs.size;
    if (
      window.confirm(
        `Are you sure you want to delete ${count} document${count !== 1 ? "s" : ""}?`,
      )
    ) {
      bulkDeleteMutation.mutate(Array.from(selectedDocs), {
        onSuccess: () => {
          setSelectedDocs(new Set());
        },
      });
    }
  };

  const handleDeleteSingle = (docId, filename) => {
    if (window.confirm(`Are you sure you want to delete "${filename}"?`)) {
      deleteDocMutation.mutate(docId, {
        onSuccess: () => {
          selectedDocs.delete(docId);
          setSelectedDocs(new Set(selectedDocs));
        },
      });
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-0">
      <div className="mb-6 sm:mb-8">
        <div className="flex items-center mb-3">
          <div className="p-2.5 sm:p-3 rounded-xl bg-violet-500/15 mr-3 sm:mr-4">
            <Upload className="h-5 w-5 sm:h-6 sm:w-6 text-violet-400" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-[var(--text-primary)]">
              Upload Content
            </h1>
            <p className="text-[var(--text-muted)] text-xs sm:text-sm mt-0.5 sm:mt-1">
              Add documents and images to your knowledge base
            </p>
          </div>
        </div>
      </div>

      {/* Tab Navigation - Mobile optimized */}
      <div className="flex gap-2 mb-4 sm:mb-6 overflow-x-auto pb-1 -mx-4 px-4 sm:mx-0 sm:px-0 sm:overflow-visible">
        <button
          onClick={() => setActiveTab("documents")}
          className={`flex items-center px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl font-medium text-sm transition-all flex-shrink-0 ${
            activeTab === "documents"
              ? "bg-violet-500/20 text-violet-400 border border-violet-500/30"
              : "bg-[var(--bg-secondary)] text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:bg-[var(--hover-bg)] hover:text-[var(--text-primary)]"
          }`}
        >
          <FileText className="h-4 w-4 mr-1.5 sm:mr-2" />
          <span className="hidden xs:inline">Documents</span>
          <span className="xs:hidden">Docs</span>
        </button>
        <button
          onClick={() => setActiveTab("images")}
          className={`flex items-center px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl font-medium text-sm transition-all flex-shrink-0 ${
            activeTab === "images"
              ? "bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30"
              : "bg-[var(--bg-secondary)] text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:bg-[var(--hover-bg)] hover:text-[var(--text-primary)]"
          }`}
        >
          <ImageIcon className="h-4 w-4 mr-1.5 sm:mr-2" />
          Images
        </button>
      </div>

      {/* Status Messages (shared) */}
      {uploadStatus && (
        <div
          className={`mb-6 p-4 rounded-xl border ${
            uploadStatus.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/30"
              : uploadStatus.type === "error"
                ? "bg-red-500/10 border-red-500/30"
                : "bg-blue-500/10 border-blue-500/30"
          }`}
        >
          <div className="flex items-center">
            {uploadStatus.type === "success" && (
              <CheckCircle className="h-4 w-4 text-emerald-400 mr-2" />
            )}
            {uploadStatus.type === "error" && (
              <AlertCircle className="h-4 w-4 text-red-400 mr-2" />
            )}
            {uploadStatus.type === "loading" && (
              <div className="h-4 w-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin mr-2" />
            )}
            <p
              className={`text-sm font-medium ${
                uploadStatus.type === "success"
                  ? "text-emerald-400"
                  : uploadStatus.type === "error"
                    ? "text-red-400"
                    : "text-blue-400"
              }`}
            >
              {uploadStatus.message}
            </p>
          </div>
        </div>
      )}

      {/* Documents Tab */}
      {activeTab === "documents" && (
        <>
          {/* Document Upload Section */}
          <div className="bg-[var(--bg-secondary)]/60 backdrop-blur-sm rounded-2xl border border-[var(--border-subtle)] p-4 sm:p-6 mb-6 sm:mb-8 transition-colors">
            {/* Upload Mode Toggle */}
            <div className="flex items-center gap-2 mb-4">
              <button
                onClick={() => {
                  setUploadMode("single");
                  setSelectedFiles([]);
                }}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                  uploadMode === "single"
                    ? "bg-violet-500/20 text-violet-400 border border-violet-500/30"
                    : "bg-[var(--bg-tertiary)] text-[var(--text-muted)] border border-transparent hover:text-[var(--text-secondary)]"
                }`}
              >
                Single
              </button>
              <button
                onClick={() => {
                  setUploadMode("batch");
                  setSelectedFile(null);
                }}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                  uploadMode === "batch"
                    ? "bg-violet-500/20 text-violet-400 border border-violet-500/30"
                    : "bg-[var(--bg-tertiary)] text-[var(--text-muted)] border border-transparent hover:text-[var(--text-secondary)]"
                }`}
              >
                Batch
              </button>
            </div>

            {uploadMode === "single" ? (
              <>
                <FileDrop onFileSelect={handleFileSelect} />
                {selectedFile && !uploadStatus && (
                  <div className="mt-6 space-y-4">
                    {/* Category Selector */}
                    <div>
                      <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Category
                        <span className="text-[var(--text-muted)] font-normal ml-2 text-xs">
                          (Auto-detected, you can change)
                        </span>
                      </label>
                      <select
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        className="w-full px-4 py-2.5 bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500/50 transition-all"
                      >
                        <option value="general">General</option>
                        <option value="policy">Policy</option>
                        <option value="contract">Contract</option>
                        <option value="legal">Legal</option>
                        <option value="procedure">Procedure</option>
                        <option value="guide">Guide</option>
                        <option value="form">Form</option>
                        <option value="report">Report</option>
                      </select>
                    </div>

                    <button
                      onClick={handleUpload}
                      disabled={uploadMutation.isPending}
                      className="w-full flex items-center justify-center px-6 py-3.5 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-semibold rounded-xl hover:from-violet-500 hover:to-fuchsia-500 focus:outline-none focus:ring-2 focus:ring-violet-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      {uploadMutation.isPending
                        ? "Uploading..."
                        : "Upload & Index Document"}
                    </button>
                  </div>
                )}
              </>
            ) : (
              <>
                <FileDrop onFilesSelect={handleFilesSelect} multiple={true} />

                {/* Batch Progress Display */}
                {isBatchUploading && batchProgress.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <p className="text-sm font-medium text-[var(--text-primary)] mb-3">
                      Upload Progress
                    </p>
                    {batchProgress.map((item, index) => (
                      <div
                        key={index}
                        className={`p-3 rounded-lg border ${
                          item.status === "success"
                            ? "bg-emerald-500/10 border-emerald-500/30"
                            : item.status === "error"
                              ? "bg-red-500/10 border-red-500/30"
                              : item.status === "uploading"
                                ? "bg-blue-500/10 border-blue-500/30"
                                : "bg-[var(--bg-secondary)]/50 border-[var(--border-subtle)]"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm text-[var(--text-secondary)] truncate max-w-[70%]">
                            {item.filename}
                          </span>
                          <span className="flex items-center text-xs">
                            {item.status === "success" && (
                              <CheckCircle className="h-4 w-4 text-emerald-400" />
                            )}
                            {item.status === "error" && (
                              <AlertCircle className="h-4 w-4 text-red-400" />
                            )}
                            {item.status === "uploading" && (
                              <Loader2 className="h-4 w-4 text-blue-400 animate-spin" />
                            )}
                            {item.status === "pending" && (
                              <span className="text-[var(--text-muted)]">
                                Waiting...
                              </span>
                            )}
                          </span>
                        </div>
                        {item.status === "uploading" && (
                          <div className="w-full bg-[var(--bg-secondary)] rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-gradient-to-r from-blue-500 to-cyan-500 h-full rounded-full transition-all duration-300"
                              style={{ width: `${item.percent}%` }}
                            />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {selectedFiles.length > 0 &&
                  !isBatchUploading &&
                  !uploadStatus && (
                    <div className="mt-6">
                      <button
                        onClick={handleBatchUpload}
                        disabled={isBatchUploading}
                        className="w-full flex items-center justify-center px-6 py-3.5 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-semibold rounded-xl hover:from-violet-500 hover:to-fuchsia-500 focus:outline-none focus:ring-2 focus:ring-violet-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        Upload & Index {selectedFiles.length} Document(s)
                      </button>
                    </div>
                  )}
              </>
            )}
          </div>

          {/* Documents List */}
          <div className="bg-[var(--bg-secondary)]/60 backdrop-blur-sm rounded-2xl border border-[var(--border-subtle)] p-4 sm:p-6 transition-colors">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-0 mb-4">
              <div className="flex items-center">
                <div className="p-2 rounded-xl bg-amber-500/15 mr-3">
                  <FileText className="h-5 w-5 text-amber-400" />
                </div>
                <div>
                  <h2 className="text-base sm:text-lg font-semibold text-[var(--text-primary)]">
                    Uploaded Documents
                  </h2>
                  <p className="text-xs text-[var(--text-muted)]">
                    {filteredDocuments?.length || 0} of {documents?.length || 0}{" "}
                    documents
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 sm:gap-3 overflow-x-auto pb-1 sm:pb-0 -mx-4 px-4 sm:mx-0 sm:px-0">
                {selectedDocs.size > 0 && (
                  <button
                    onClick={handleDeleteSelected}
                    disabled={bulkDeleteMutation.isPending}
                    className="flex items-center px-3 py-2 text-xs font-medium text-red-400 bg-red-500/10 hover:bg-red-500/20 rounded-xl transition-colors disabled:opacity-50 flex-shrink-0"
                  >
                    <Trash2 className="h-3.5 w-3.5 mr-1.5" />
                    <span className="hidden xs:inline">Delete</span> (
                    {selectedDocs.size})
                  </button>
                )}

                {documents && documents.length > 0 && (
                  <button
                    onClick={() => navigate("/chat")}
                    className="flex items-center px-3 sm:px-4 py-2 text-xs font-semibold bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-xl hover:from-violet-500 hover:to-fuchsia-500 transition-all flex-shrink-0"
                  >
                    <Sparkles className="h-3.5 w-3.5 sm:mr-1.5" />
                    <span className="hidden sm:inline">Start Chat</span>
                    <ArrowRight className="h-3.5 w-3.5 ml-1 sm:ml-1.5" />
                  </button>
                )}
              </div>
            </div>

            {/* Category Filter */}
            {documents && documents.length > 0 && (
              <div className="flex items-center gap-2 mb-4 pb-4 border-b border-[var(--border-subtle)] overflow-x-auto">
                <span className="text-xs text-[var(--text-secondary)] flex-shrink-0 font-medium">
                  <Folder className="h-3 w-3 inline mr-1" />
                  Filter:
                </span>
                <button
                  onClick={() => setCategoryFilter(null)}
                  className={`px-3 py-1.5 text-xs rounded-lg transition-all duration-200 flex-shrink-0 font-medium ${
                    !categoryFilter
                      ? "bg-violet-500/20 text-violet-300 border border-violet-500/40 shadow-sm shadow-violet-500/10"
                      : "text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:text-[var(--text-primary)] hover:bg-[var(--hover-bg)] hover:border-[var(--hover-border)]"
                  }`}
                >
                  All
                </button>
                {[
                  "policy",
                  "contract",
                  "legal",
                  "procedure",
                  "guide",
                  "form",
                  "report",
                  "general",
                ].map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setCategoryFilter(cat)}
                    className={`px-3 py-1.5 text-xs rounded-lg transition-all duration-200 capitalize flex-shrink-0 font-medium ${
                      categoryFilter === cat
                        ? "bg-violet-500/20 text-violet-300 border border-violet-500/40 shadow-sm shadow-violet-500/10"
                        : "text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:text-[var(--text-primary)] hover:bg-[var(--hover-bg)] hover:border-[var(--hover-border)]"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
                <button
                  onClick={() => setCategoryFilter("uncategorized")}
                  className={`px-3 py-1.5 text-xs rounded-lg transition-all duration-200 flex-shrink-0 font-medium ${
                    categoryFilter === "uncategorized"
                      ? "bg-violet-500/20 text-violet-300 border border-violet-500/40 shadow-sm shadow-violet-500/10"
                      : "text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:text-[var(--text-primary)] hover:bg-[var(--hover-bg)] hover:border-[var(--hover-border)]"
                  }`}
                >
                  Uncategorized
                </button>
              </div>
            )}

            {filteredDocuments && filteredDocuments.length > 0 ? (
              <>
                {/* Select All */}
                <button
                  onClick={handleSelectAll}
                  className="mb-4 text-xs font-medium text-violet-400 hover:text-violet-300 transition-colors"
                >
                  {selectedDocs.size === filteredDocuments.length
                    ? "Deselect All"
                    : "Select All"}
                </button>

                <div className="space-y-2">
                  {filteredDocuments.map((doc, index) => {
                    const isSelected = selectedDocs.has(doc.id);
                    const isEditing = editingDoc?.id === doc.id;

                    return (
                      <div
                        key={doc.id}
                        className={`p-4 rounded-xl border transition-all duration-200 group ${
                          isSelected
                            ? "bg-violet-500/10 border-violet-500/30"
                            : "bg-[var(--bg-secondary)]/50 border-[var(--border-subtle)] hover:bg-[var(--hover-bg)] hover:border-[var(--border-subtle)]"
                        }`}
                        style={{ animationDelay: `${index * 50}ms` }}
                      >
                        <div className="flex items-start">
                          {/* Custom Checkbox */}
                          <div
                            onClick={() => toggleDocSelection(doc.id)}
                            className={`w-4 h-4 rounded-md border-2 flex items-center justify-center transition-all flex-shrink-0 mt-0.5 cursor-pointer ${
                              isSelected
                                ? "bg-gradient-to-br from-violet-500 to-fuchsia-500 border-transparent"
                                : "border-[var(--border-subtle)] hover:border-violet-500/50"
                            }`}
                          >
                            {isSelected && (
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

                          <div className="ml-4 flex-1">
                            <div className="flex items-center flex-wrap gap-2">
                              <FileText
                                className={`h-3.5 w-3.5 ${isSelected ? "text-violet-400" : "text-[var(--text-muted)]"}`}
                              />
                              <h3
                                className={`text-sm font-medium ${isSelected ? "text-[var(--text-primary)]" : "text-[var(--text-secondary)]"}`}
                              >
                                {doc.filename}
                              </h3>
                              {doc.category && (
                                <CategoryBadge category={doc.category} />
                              )}
                            </div>

                            {/* Tags */}
                            {doc.tags && doc.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-1.5">
                                {doc.tags.map((tag) => (
                                  <TagBadge key={tag} tag={tag} />
                                ))}
                              </div>
                            )}

                            <p className="text-xs text-[var(--text-muted)] mt-1">
                              Uploaded:{" "}
                              {new Date(doc.created_at).toLocaleString()}
                            </p>
                            {doc.preview_text && (
                              <p className="text-xs text-[var(--text-muted)] mt-1.5 line-clamp-2">
                                {doc.preview_text}
                              </p>
                            )}

                            {/* Inline Category Editor */}
                            {isEditing && (
                              <div className="mt-3 pt-3 border-t border-[var(--border-subtle)]">
                                <DocumentCategoryEditor
                                  category={editingDoc.category}
                                  tags={editingDoc.tags || []}
                                  onCategoryChange={(cat) =>
                                    setEditingDoc({
                                      ...editingDoc,
                                      category: cat,
                                    })
                                  }
                                  onTagsChange={(tags) =>
                                    setEditingDoc({ ...editingDoc, tags })
                                  }
                                  compact
                                />
                                <div className="flex gap-2 mt-3">
                                  <button
                                    onClick={() =>
                                      handleUpdateDocCategory(
                                        doc.id,
                                        editingDoc.category,
                                        editingDoc.tags,
                                      )
                                    }
                                    className="px-3 py-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 rounded-lg transition-colors"
                                  >
                                    Save
                                  </button>
                                  <button
                                    onClick={() => setEditingDoc(null)}
                                    className="px-3 py-1.5 text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text-secondary)] rounded-lg transition-colors"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
                            <button
                              onClick={() =>
                                setEditingDoc(
                                  editingDoc?.id === doc.id ? null : { ...doc },
                                )
                              }
                              className={`p-2 rounded-lg transition-all ${
                                isEditing
                                  ? "text-violet-400 bg-violet-500/10"
                                  : "text-[var(--text-muted)] hover:text-amber-400 hover:bg-amber-500/10"
                              }`}
                              title="Edit category & tags"
                            >
                              <Edit2 className="h-3.5 w-3.5" />
                            </button>
                            <button
                              onClick={() => setPreviewDoc(doc)}
                              className="p-2 text-[var(--text-muted)] hover:text-violet-400 hover:bg-violet-500/10 rounded-lg transition-all"
                              title="Preview document"
                            >
                              <Eye className="h-3.5 w-3.5" />
                            </button>
                            <button
                              onClick={() =>
                                handleDeleteSingle(doc.id, doc.filename)
                              }
                              disabled={deleteDocMutation.isPending}
                              className="p-2 text-[var(--text-muted)] hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all disabled:opacity-50"
                              title="Delete document"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[var(--bg-secondary)]/50 mb-4">
                  <FileText className="h-7 w-7 text-[var(--text-muted)]" />
                </div>
                <p className="text-[var(--text-secondary)]">
                  No documents uploaded yet
                </p>
                <p className="text-xs text-[var(--text-muted)] mt-1">
                  Upload your first document above to get started
                </p>
              </div>
            )}
          </div>

          {/* Document Preview Modal */}
          <DocumentPreview
            docId={previewDoc?.id}
            filename={previewDoc?.filename}
            isOpen={!!previewDoc}
            onClose={() => setPreviewDoc(null)}
          />
        </>
      )}

      {/* Images Tab */}
      {activeTab === "images" && (
        <>
          {/* Image Upload Section */}
          <div className="bg-[var(--bg-secondary)]/60 backdrop-blur-sm rounded-2xl border border-[var(--border-subtle)] p-6 mb-8 transition-colors">
            <div className="flex items-center mb-4">
              <div className="p-2 rounded-xl bg-fuchsia-500/15 mr-3">
                <ImageIcon className="h-5 w-5 text-fuchsia-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                  Upload Image
                </h2>
                <p className="text-xs text-[var(--text-muted)]">
                  Images are indexed with CLIP for semantic search
                </p>
              </div>
            </div>

            <ImageUpload
              onUploadSuccess={handleImageUploadSuccess}
              onUploadError={handleImageUploadError}
            />
          </div>

          {/* Image Gallery */}
          <div className="bg-[var(--bg-secondary)]/60 backdrop-blur-sm rounded-2xl border border-[var(--border-subtle)] p-6 transition-colors">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <div className="p-2 rounded-xl bg-cyan-500/15 mr-3">
                  <ImageIcon className="h-5 w-5 text-cyan-400" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                    Image Gallery
                  </h2>
                  <p className="text-xs text-[var(--text-muted)]">
                    {images.length} images in knowledge base
                  </p>
                </div>
              </div>

              {images.length > 0 && (
                <button
                  onClick={() => navigate("/chat")}
                  className="flex items-center px-4 py-2 text-xs font-semibold bg-gradient-to-r from-fuchsia-600 to-cyan-600 text-white rounded-xl hover:from-fuchsia-500 hover:to-cyan-500 transition-all"
                >
                  <Sparkles className="h-3.5 w-3.5 mr-1.5" />
                  Chat with Images
                  <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
                </button>
              )}
            </div>

            <ImageGallery
              images={images}
              onDelete={handleImageDelete}
              loading={imagesLoading}
              selectable={false}
              showDelete={true}
            />
          </div>
        </>
      )}
    </div>
  );
}
