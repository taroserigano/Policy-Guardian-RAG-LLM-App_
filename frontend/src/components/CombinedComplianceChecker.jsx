/**
 * CombinedComplianceChecker Component
 *
 * All-in-one compliance checker: upload, select from library, and check in one place.
 */
import { useState, useRef } from "react";
import {
  Shield,
  Upload,
  FileText,
  Image as ImageIcon,
  X,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Search,
  Loader2,
  AlertCircle,
  Send,
  Trash2,
  Eye,
  Check,
  Plus,
  Library,
  ChevronDown,
  ChevronUp,
  Cloud,
  Wand2,
} from "lucide-react";
import toast from "react-hot-toast";
import {
  uploadDocument,
  uploadImage,
  streamComplianceCheck,
  deleteImage as deleteImageApi,
} from "../api/client";

// Status badge styling
const statusStyles = {
  compliant: {
    bg: "bg-green-500/10",
    text: "text-green-400",
    border: "border-green-500/20",
    icon: CheckCircle,
    label: "Compliant",
  },
  non_compliant: {
    bg: "bg-red-500/10",
    text: "text-red-400",
    border: "border-red-500/20",
    icon: XCircle,
    label: "Non-Compliant",
  },
  partial: {
    bg: "bg-yellow-500/10",
    text: "text-yellow-400",
    border: "border-yellow-500/20",
    icon: AlertTriangle,
    label: "Partially Compliant",
  },
  needs_review: {
    bg: "bg-blue-500/10",
    text: "text-blue-400",
    border: "border-blue-500/20",
    icon: Search,
    label: "Needs Review",
  },
};

function StatusBadge({ status }) {
  const style = statusStyles[status] || statusStyles.needs_review;
  const Icon = style.icon;
  return (
    <span
      className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium ${style.bg} ${style.text} ${style.border} border`}
    >
      <Icon className="w-4 h-4" />
      {style.label}
    </span>
  );
}

export default function CombinedComplianceChecker({
  provider = "openai",
  userId = "default-user",
  libraryDocuments = [],
  libraryImages = [],
  isLoadingLibrary = false,
  onLibraryImageDeleted,
}) {
  // Upload state
  const [uploadedDocs, setUploadedDocs] = useState([]);
  const [uploadedImages, setUploadedImages] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadMode, setUploadMode] = useState("single"); // 'single' or 'batch'
  const [autoDescribe, setAutoDescribe] = useState(false); // AI description for images - default OFF
  const [pendingImageFile, setPendingImageFile] = useState(null); // File waiting for manual description
  const [pendingImagePreview, setPendingImagePreview] = useState(null);
  const [manualDescription, setManualDescription] = useState("");

  // Selection state (for uploaded files)
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [selectedImageIds, setSelectedImageIds] = useState([]);

  // Library selection state
  const [selectedLibDocIds, setSelectedLibDocIds] = useState([]);
  const [selectedLibImageIds, setSelectedLibImageIds] = useState([]);

  // Library UI state
  const [showLibraryDocs, setShowLibraryDocs] = useState(false);
  const [showLibraryImages, setShowLibraryImages] = useState(false);
  const [libDocSearch, setLibDocSearch] = useState("");
  const [libImageSearch, setLibImageSearch] = useState("");

  // Compliance state
  const [query, setQuery] = useState("");
  const [isChecking, setIsChecking] = useState(false);
  const [report, setReport] = useState(null);
  const [streamingText, setStreamingText] = useState("");
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  // Preview state (for uploaded images)
  const [previewImage, setPreviewImage] = useState(null);
  // Preview state (for library images)
  const [previewLibImage, setPreviewLibImage] = useState(null);
  // Deleting state
  const [deletingImageId, setDeletingImageId] = useState(null);

  const fileInputRef = useRef(null);
  const abortRef = useRef(null);
  const resultRef = useRef(null);

  // Example queries
  const exampleQueries = [
    "Is this compliant with the policy?",
    "What violations are shown in the images?",
    "Does this meet the required standards?",
    "Summarize the compliance status",
  ];

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
          const newImg = {
            id: result.id,
            name: file.name,
            preview: URL.createObjectURL(file),
            size: file.size,
          };
          setUploadedImages((prev) => [...prev, newImg]);
          setSelectedImageIds((prev) => [...prev, result.id]); // Auto-select
          toast.success(`Image uploaded: ${file.name}`);
        } else {
          setIsUploading(true);
          const result = await uploadDocument(file);
          const newDoc = {
            id: result.id,
            name: file.name,
            size: file.size,
          };
          setUploadedDocs((prev) => [...prev, newDoc]);
          setSelectedDocIds((prev) => [...prev, result.id]); // Auto-select
          toast.success(`Document uploaded: ${file.name}`);
        }
      } catch (err) {
        console.error("Upload failed:", err);
        toast.error(`Failed to upload ${file.name}: ${err.message}`);
      }
    }

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
      const newImg = {
        id: result.id,
        name: pendingImageFile.name,
        preview: pendingImagePreview,
        size: pendingImageFile.size,
      };
      setUploadedImages((prev) => [...prev, newImg]);
      setSelectedImageIds((prev) => [...prev, result.id]);
      toast.success(`Image uploaded: ${pendingImageFile.name}`);

      // Clear pending state (don't revoke URL since we're using it in the uploaded list)
      setPendingImageFile(null);
      setPendingImagePreview(null);
      setManualDescription("");
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

  const toggleDocSelection = (id) => {
    setSelectedDocIds((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id],
    );
  };

  const toggleImageSelection = (id) => {
    setSelectedImageIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id],
    );
  };

  const removeDoc = (id) => {
    setUploadedDocs((prev) => prev.filter((d) => d.id !== id));
    setSelectedDocIds((prev) => prev.filter((d) => d !== id));
  };

  const removeImage = (id) => {
    setUploadedImages((prev) => prev.filter((i) => i.id !== id));
    setSelectedImageIds((prev) => prev.filter((i) => i !== id));
  };

  // Library toggle functions
  const toggleLibDocSelection = (id) => {
    setSelectedLibDocIds((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id],
    );
  };

  const toggleLibImageSelection = (id) => {
    setSelectedLibImageIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, i],
    );
  };

  const selectAllUploaded = () => {
    setSelectedDocIds(uploadedDocs.map((d) => d.id));
    setSelectedImageIds(uploadedImages.map((i) => i.id));
  };

  const deselectAllUploaded = () => {
    setSelectedDocIds([]);
    setSelectedImageIds([]);
  };

  const selectAllLibDocs = () => {
    setSelectedLibDocIds(filteredLibDocs.map((d) => d.id));
  };

  const deselectAllLibDocs = () => {
    setSelectedLibDocIds([]);
  };

  const selectAllLibImages = () => {
    setSelectedLibImageIds(filteredLibImages.map((i) => i.id));
  };

  const deselectAllLibImages = () => {
    setSelectedLibImageIds([]);
  };

  // Filter library items by search
  const filteredLibDocs = libraryDocuments.filter(
    (d) =>
      d.filename?.toLowerCase().includes(libDocSearch.toLowerCase()) ||
      d.name?.toLowerCase().includes(libDocSearch.toLowerCase()),
  );

  const filteredLibImages = libraryImages.filter(
    (i) =>
      i.filename?.toLowerCase().includes(libImageSearch.toLowerCase()) ||
      i.name?.toLowerCase().includes(libImageSearch.toLowerCase()),
  );

  // Delete library image
  const handleDeleteLibImage = async (e, imageId) => {
    e.stopPropagation();
    if (deletingImageId) return;

    setDeletingImageId(imageId);
    try {
      await deleteImageApi(imageId);
      // Remove from selection if selected
      setSelectedLibImageIds((prev) => prev.filter((id) => id !== imageId));
      // Notify parent to refresh
      onLibraryImageDeleted?.(imageId);
      toast.success("Image deleted");
    } catch (err) {
      console.error("Delete failed:", err);
      toast.error("Failed to delete image");
    } finally {
      setDeletingImageId(null);
    }
  };

  const handleCheck = async () => {
    if (!query.trim()) {
      toast.error("Please enter a compliance question");
      return;
    }

    // Combine uploaded selections with library selections
    const allDocIds = [...selectedDocIds, ...selectedLibDocIds];
    const allImageIds = [...selectedImageIds, ...selectedLibImageIds];

    if (allDocIds.length === 0 && allImageIds.length === 0) {
      toast.error("Please select at least one document or image");
      return;
    }

    setIsChecking(true);
    setError(null);
    setReport(null);
    setStreamingText("");
    setStatus({
      stage: "starting",
      message: "Initializing compliance check...",
    });

    abortRef.current = streamComplianceCheck(
      {
        user_id: userId,
        query: query.trim(),
        provider,
        doc_ids: allDocIds.length > 0 ? allDocIds : undefined,
        image_ids: allImageIds.length > 0 ? allImageIds : undefined,
        include_image_search: allImageIds.length > 0,
      },
      {
        onStatus: (data) => setStatus(data),
        onCitations: () => {},
        onToken: (token) => setStreamingText((prev) => prev + token),
        onReport: (data) => {
          setReport(data);
          setIsChecking(false);
          setTimeout(() => {
            resultRef.current?.scrollIntoView({ behavior: "smooth" });
          }, 100);
        },
        onDone: () => setIsChecking(false),
        onError: (err) => {
          setError(err.message);
          setIsChecking(false);
        },
      },
    );
  };

  const handleCancel = () => {
    if (abortRef.current) {
      abortRef.current();
      setIsChecking(false);
      setStatus(null);
    }
  };

  const totalUploadedFiles = uploadedDocs.length + uploadedImages.length;
  const selectedUploadedCount = selectedDocIds.length + selectedImageIds.length;
  const selectedLibraryCount =
    selectedLibDocIds.length + selectedLibImageIds.length;
  const totalSelectedCount = selectedUploadedCount + selectedLibraryCount;

  return (
    <div className="h-full overflow-y-auto p-4 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-violet-500/10 to-fuchsia-500/10 border border-violet-500/20 rounded-xl p-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-violet-500/20 rounded-xl">
            <Shield className="w-6 h-6 text-violet-400" />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-2">
              Quick Compliance Check
            </h2>
            <p className="text-sm text-[var(--text-secondary)]">
              Upload new files or select from your library, then ask your
              compliance question.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Upload & Select */}
        <div className="space-y-4">
          {/* Upload Area */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-4">
            {/* Top Row: Single/Batch Toggle + Auto-describe option */}
            <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
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
              <div className="mb-4 p-4 bg-[var(--bg-tertiary)] rounded-xl border border-[var(--border-subtle)]">
                <div className="flex items-start gap-4">
                  <img
                    src={pendingImagePreview}
                    alt="Preview"
                    className="w-24 h-24 object-cover rounded-lg"
                  />
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-[var(--text-primary)]">
                        {pendingImageFile.name}
                      </p>
                      <button
                        onClick={cancelPendingUpload}
                        className="text-xs text-[var(--text-muted)] hover:text-red-400 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                    <textarea
                      value={manualDescription}
                      onChange={(e) => setManualDescription(e.target.value)}
                      placeholder="Enter image description (optional)..."
                      className="w-full px-3 py-2 text-sm bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg
                                 text-[var(--text-primary)] placeholder-[var(--text-muted)] resize-none
                                 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                      rows={2}
                      autoFocus
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleManualImageUpload(false)}
                        className="flex-1 px-3 py-2 rounded-lg text-sm font-medium bg-violet-500 hover:bg-violet-400 text-white transition-all"
                      >
                        {manualDescription.trim()
                          ? "Upload with Description"
                          : "Upload without Description"}
                      </button>
                      <button
                        onClick={() => handleManualImageUpload(true)}
                        className="px-3 py-2 rounded-lg text-sm font-medium bg-[var(--bg-secondary)] hover:bg-[var(--hover-bg)] 
                                   text-[var(--text-secondary)] transition-all border border-[var(--border-subtle)] flex items-center gap-1"
                      >
                        <Wand2 className="w-4 h-4" />
                        Use AI
                      </button>
                    </div>
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

          {/* Uploaded File Selection */}
          {totalUploadedFiles > 0 && (
            <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-[var(--text-primary)] flex items-center gap-2">
                  <Check className="w-4 h-4" />
                  Uploaded Files ({selectedUploadedCount}/{totalUploadedFiles})
                </h3>
                <div className="flex gap-2">
                  <button
                    onClick={selectAllUploaded}
                    className="text-xs px-2 py-1 text-violet-400 hover:bg-violet-500/10 rounded transition-colors"
                  >
                    Select All
                  </button>
                  <button
                    onClick={deselectAllUploaded}
                    className="text-xs px-2 py-1 text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)] rounded transition-colors"
                  >
                    Clear
                  </button>
                </div>
              </div>

              <div className="space-y-3 max-h-[300px] overflow-y-auto">
                {/* Documents */}
                {uploadedDocs.length > 0 && (
                  <div>
                    <p className="text-xs text-[var(--text-muted)] mb-2 flex items-center gap-1">
                      <FileText className="w-3 h-3" />
                      Documents ({uploadedDocs.length})
                    </p>
                    <div className="space-y-1">
                      {uploadedDocs.map((doc) => (
                        <div
                          key={doc.id}
                          className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                            selectedDocIds.includes(doc.id)
                              ? "bg-violet-500/20 border border-violet-500/30"
                              : "bg-[var(--bg-tertiary)] border border-transparent hover:border-[var(--border-subtle)]"
                          }`}
                          onClick={() => toggleDocSelection(doc.id)}
                        >
                          <div
                            className={`w-4 h-4 rounded border flex items-center justify-center ${
                              selectedDocIds.includes(doc.id)
                                ? "bg-violet-500 border-violet-500"
                                : "border-[var(--border-subtle)]"
                            }`}
                          >
                            {selectedDocIds.includes(doc.id) && (
                              <Check className="w-3 h-3 text-white" />
                            )}
                          </div>
                          <FileText className="w-4 h-4 text-blue-400 flex-shrink-0" />
                          <span className="text-sm text-[var(--text-primary)] flex-1 truncate">
                            {doc.name}
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              removeDoc(doc.id);
                            }}
                            className="p-1 hover:bg-red-500/20 rounded text-[var(--text-muted)] hover:text-red-400 transition-colors"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Images */}
                {uploadedImages.length > 0 && (
                  <div>
                    <p className="text-xs text-[var(--text-muted)] mb-2 flex items-center gap-1">
                      <ImageIcon className="w-3 h-3" />
                      Images ({uploadedImages.length})
                    </p>
                    <div className="grid grid-cols-3 gap-2">
                      {uploadedImages.map((img) => (
                        <div
                          key={img.id}
                          className={`relative group cursor-pointer rounded-lg overflow-hidden border-2 transition-colors ${
                            selectedImageIds.includes(img.id)
                              ? "border-violet-500"
                              : "border-transparent hover:border-[var(--border-subtle)]"
                          }`}
                          onClick={() => toggleImageSelection(img.id)}
                        >
                          <div className="aspect-square bg-[var(--bg-tertiary)]">
                            <img
                              src={img.preview}
                              alt={img.name}
                              className="w-full h-full object-cover"
                            />
                          </div>
                          {/* Selection indicator */}
                          <div
                            className={`absolute top-1 left-1 w-5 h-5 rounded border flex items-center justify-center ${
                              selectedImageIds.includes(img.id)
                                ? "bg-violet-500 border-violet-500"
                                : "bg-black/50 border-white/30"
                            }`}
                          >
                            {selectedImageIds.includes(img.id) && (
                              <Check className="w-3 h-3 text-white" />
                            )}
                          </div>
                          {/* Actions overlay */}
                          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setPreviewImage(img);
                              }}
                              className="p-1.5 bg-white/20 rounded hover:bg-white/30 transition-colors"
                            >
                              <Eye className="w-3 h-3 text-white" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                removeImage(img.id);
                              }}
                              className="p-1.5 bg-red-500/50 rounded hover:bg-red-500/70 transition-colors"
                            >
                              <Trash2 className="w-3 h-3 text-white" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Library Selection */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-4">
            <h3 className="text-sm font-medium text-[var(--text-primary)] mb-3 flex items-center gap-2">
              <Library className="w-4 h-4" />
              Select from Library
              {selectedLibraryCount > 0 && (
                <span className="ml-auto text-xs px-2 py-0.5 bg-violet-500/20 text-violet-400 rounded-full">
                  {selectedLibraryCount} selected
                </span>
              )}
            </h3>

            {isLoadingLibrary ? (
              <div className="flex items-center gap-2 text-sm text-[var(--text-muted)] py-4">
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading library...
              </div>
            ) : (
              <div className="space-y-3">
                {/* Library Documents Accordion */}
                <div className="border border-[var(--border-subtle)] rounded-lg overflow-hidden">
                  <button
                    onClick={() => setShowLibraryDocs(!showLibraryDocs)}
                    className="w-full flex items-center justify-between px-3 py-2 bg-[var(--bg-tertiary)] hover:bg-[var(--bg-tertiary)]/80 transition-colors"
                  >
                    <span className="text-sm text-[var(--text-primary)] flex items-center gap-2">
                      <FileText className="w-4 h-4 text-blue-400" />
                      Documents ({libraryDocuments.length})
                      {selectedLibDocIds.length > 0 && (
                        <span className="text-xs px-1.5 py-0.5 bg-violet-500/20 text-violet-400 rounded">
                          {selectedLibDocIds.length} selected
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
                        {filteredLibDocs.length === 0 ? (
                          <p className="text-xs text-[var(--text-muted)] py-2 text-center">
                            {libDocSearch
                              ? "No matching documents"
                              : "No documents in library"}
                          </p>
                        ) : (
                          filteredLibDocs.map((doc) => (
                            <div
                              key={doc.id}
                              className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer transition-colors ${
                                selectedLibDocIds.includes(doc.id)
                                  ? "bg-violet-500/20 border border-violet-500/30"
                                  : "hover:bg-[var(--bg-tertiary)] border border-transparent"
                              }`}
                              onClick={() => toggleLibDocSelection(doc.id)}
                            >
                              <div
                                className={`w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 ${
                                  selectedLibDocIds.includes(doc.id)
                                    ? "bg-violet-500 border-violet-500"
                                    : "border-[var(--border-subtle)]"
                                }`}
                              >
                                {selectedLibDocIds.includes(doc.id) && (
                                  <Check className="w-3 h-3 text-white" />
                                )}
                              </div>
                              <span className="text-xs text-[var(--text-primary)] truncate">
                                {doc.filename || doc.name}
                              </span>
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
                      <ImageIcon className="w-4 h-4 text-green-400" />
                      Images ({libraryImages.length})
                      {selectedLibImageIds.length > 0 && (
                        <span className="text-xs px-1.5 py-0.5 bg-violet-500/20 text-violet-400 rounded">
                          {selectedLibImageIds.length} selected
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
                        {filteredLibImages.length === 0 ? (
                          <p className="text-xs text-[var(--text-muted)] py-4 text-center">
                            {libImageSearch
                              ? "No matching images"
                              : "No images in library"}
                          </p>
                        ) : (
                          <div className="grid grid-cols-3 gap-2">
                            {filteredLibImages.map((img) => (
                              <div
                                key={img.id}
                                className={`relative group cursor-pointer rounded-lg overflow-hidden border-2 transition-colors ${
                                  selectedLibImageIds.includes(img.id)
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
                                      <ImageIcon className="w-6 h-6 text-[var(--text-muted)]" />
                                    </div>
                                  )}
                                </div>

                                {/* Selection indicator */}
                                <div
                                  className={`absolute top-1 left-1 w-5 h-5 rounded border flex items-center justify-center ${
                                    selectedLibImageIds.includes(img.id)
                                      ? "bg-violet-500 border-violet-500"
                                      : "bg-black/50 border-white/30"
                                  }`}
                                >
                                  {selectedLibImageIds.includes(img.id) && (
                                    <Check className="w-3 h-3 text-white" />
                                  )}
                                </div>

                                {/* Actions overlay */}
                                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1">
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setPreviewLibImage(img);
                                    }}
                                    className="p-1.5 bg-white/20 rounded hover:bg-white/30 transition-colors"
                                    title="Preview"
                                  >
                                    <Eye className="w-3 h-3 text-white" />
                                  </button>
                                  <button
                                    onClick={(e) =>
                                      handleDeleteLibImage(e, img.id)
                                    }
                                    disabled={deletingImageId === img.id}
                                    className="p-1.5 bg-red-500/50 rounded hover:bg-red-500/70 transition-colors disabled:opacity-50"
                                    title="Delete"
                                  >
                                    {deletingImageId === img.id ? (
                                      <Loader2 className="w-3 h-3 text-white animate-spin" />
                                    ) : (
                                      <Trash2 className="w-3 h-3 text-white" />
                                    )}
                                  </button>
                                </div>

                                {/* Filename tooltip on bottom */}
                                <div className="absolute bottom-0 left-0 right-0 bg-black/70 px-1 py-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                                  <p className="text-[10px] text-white truncate text-center">
                                    {img.filename || img.name}
                                  </p>
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
        </div>

        {/* Right Column: Query & Results */}
        <div className="space-y-4">
          {/* Query Section */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-4">
            <h3 className="text-sm font-medium text-[var(--text-primary)] mb-3 flex items-center gap-2">
              <Search className="w-4 h-4" />
              Ask a Question
            </h3>

            {/* Example queries */}
            <div className="flex flex-wrap gap-1.5 mb-3">
              {exampleQueries.map((q, i) => (
                <button
                  key={i}
                  onClick={() => setQuery(q)}
                  className="text-xs px-2.5 py-1 bg-[var(--bg-tertiary)] hover:bg-violet-500/10 border border-[var(--border-subtle)] hover:border-violet-500/30 rounded-full text-[var(--text-secondary)] hover:text-violet-400 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>

            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your compliance question..."
              rows={3}
              className="w-full px-3 py-2 bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500/50 resize-none text-sm transition-all"
            />

            {/* Check Button */}
            <button
              onClick={isChecking ? handleCancel : handleCheck}
              disabled={
                !isChecking && (!query.trim() || totalSelectedCount === 0)
              }
              className={`w-full mt-3 flex items-center justify-center gap-2 px-4 py-2.5 font-medium rounded-lg transition-all ${
                isChecking
                  ? "bg-red-500 hover:bg-red-600 text-white"
                  : "bg-gradient-to-r from-violet-500 to-fuchsia-500 hover:from-violet-600 hover:to-fuchsia-600 text-white disabled:opacity-50 disabled:cursor-not-allowed"
              }`}
            >
              {isChecking ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Cancel</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Check Compliance ({totalSelectedCount} files)</span>
                </>
              )}
            </button>

            {/* Status */}
            {status && isChecking && (
              <div className="mt-3 p-2 bg-violet-500/10 border border-violet-500/20 rounded-lg">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-3 h-3 text-violet-400 animate-spin" />
                  <span className="text-xs text-violet-400">
                    {status.message || "Processing..."}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-400">
                    Check Failed
                  </p>
                  <p className="text-xs text-red-400/80 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Results */}
          {(streamingText || report) && (
            <div
              ref={resultRef}
              className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-4"
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-[var(--text-primary)] flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  Results
                </h3>
                {report?.overall_status && (
                  <StatusBadge status={report.overall_status} />
                )}
              </div>

              {/* Summary */}
              <div className="text-sm text-[var(--text-secondary)] whitespace-pre-wrap leading-relaxed">
                {report?.summary || streamingText || "Analyzing..."}
              </div>

              {/* Findings */}
              {report?.findings && report.findings.length > 0 && (
                <div className="mt-4 space-y-2">
                  <h4 className="text-xs font-medium text-[var(--text-muted)]">
                    Findings
                  </h4>
                  {report.findings.map((finding, i) => {
                    const style =
                      statusStyles[finding.status] || statusStyles.needs_review;
                    const Icon = style.icon;
                    return (
                      <div
                        key={i}
                        className={`p-3 rounded-lg border ${style.border} ${style.bg}`}
                      >
                        <div className="flex items-start gap-2">
                          <Icon
                            className={`w-4 h-4 ${style.text} flex-shrink-0 mt-0.5`}
                          />
                          <div className="flex-1 min-w-0">
                            <p className={`text-sm font-medium ${style.text}`}>
                              {finding.title || `Finding ${i + 1}`}
                            </p>
                            <p className="text-xs text-[var(--text-secondary)] mt-1">
                              {finding.description}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Recommendations */}
              {report?.recommendations && report.recommendations.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-xs font-medium text-[var(--text-muted)] mb-2">
                    Recommendations
                  </h4>
                  <ul className="space-y-1">
                    {report.recommendations.map((rec, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2 text-xs text-[var(--text-secondary)]"
                      >
                        <span className="flex-shrink-0 w-4 h-4 flex items-center justify-center rounded-full bg-violet-500/20 text-violet-400 text-[10px] font-medium">
                          {i + 1}
                        </span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Image Preview Modal (uploaded images) */}
      {previewImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
          onClick={() => setPreviewImage(null)}
        >
          <div className="relative max-w-4xl max-h-[90vh]">
            <img
              src={previewImage.preview}
              alt={previewImage.name}
              className="max-w-full max-h-[90vh] object-contain rounded-lg"
            />
            <button
              onClick={() => setPreviewImage(null)}
              className="absolute top-2 right-2 p-2 bg-black/50 rounded-full hover:bg-black/70 transition-colors"
            >
              <X className="w-5 h-5 text-white" />
            </button>
            <p className="absolute bottom-2 left-2 px-3 py-1 bg-black/50 rounded-lg text-sm text-white">
              {previewImage.name}
            </p>
          </div>
        </div>
      )}

      {/* Library Image Preview Modal */}
      {previewLibImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
          onClick={() => setPreviewLibImage(null)}
        >
          <div className="relative max-w-4xl max-h-[90vh]">
            {previewLibImage.thumbnail_base64 ? (
              <img
                src={`data:image/png;base64,${previewLibImage.thumbnail_base64}`}
                alt={previewLibImage.filename || previewLibImage.name}
                className="max-w-full max-h-[90vh] object-contain rounded-lg"
              />
            ) : (
              <div className="w-64 h-64 bg-[var(--bg-tertiary)] rounded-lg flex items-center justify-center">
                <ImageIcon className="w-16 h-16 text-[var(--text-muted)]" />
              </div>
            )}
            <button
              onClick={() => setPreviewLibImage(null)}
              className="absolute top-2 right-2 p-2 bg-black/50 rounded-full hover:bg-black/70 transition-colors"
            >
              <X className="w-5 h-5 text-white" />
            </button>
            <p className="absolute bottom-2 left-2 px-3 py-1 bg-black/50 rounded-lg text-sm text-white">
              {previewLibImage.filename || previewLibImage.name}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
