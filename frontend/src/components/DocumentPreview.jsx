/**
 * Document preview modal component.
 * Displays full document content in a modal overlay with search and navigation.
 * Uses React Portal to render at document body level.
 */
import { useEffect, useState, useMemo, useRef } from "react";
import { createPortal } from "react-dom";
import {
  X,
  FileText,
  Calendar,
  Layers,
  Loader2,
  AlertCircle,
  Copy,
  Check,
  Search,
  ChevronUp,
  ChevronDown,
  Download,
  Maximize2,
  Minimize2,
  Hash,
  Tag,
} from "lucide-react";
import { useDocumentContent } from "../hooks/useApi";

export default function DocumentPreview({ docId, filename, isOpen, onClose }) {
  const [copied, setCopied] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchMatches, setSearchMatches] = useState([]);
  const [currentMatchIndex, setCurrentMatchIndex] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showLineNumbers, setShowLineNumbers] = useState(true);
  const contentRef = useRef(null);
  const {
    data: docContent,
    isLoading,
    error,
  } = useDocumentContent(docId, isOpen);

  // Search within document
  useEffect(() => {
    if (!searchQuery || !docContent?.content) {
      setSearchMatches([]);
      setCurrentMatchIndex(0);
      return;
    }

    const content = docContent.content.toLowerCase();
    const query = searchQuery.toLowerCase();
    const matches = [];
    let pos = 0;

    while ((pos = content.indexOf(query, pos)) !== -1) {
      matches.push(pos);
      pos += query.length;
    }

    setSearchMatches(matches);
    setCurrentMatchIndex(0);
  }, [searchQuery, docContent?.content]);

  // Navigate to current match
  useEffect(() => {
    if (searchMatches.length > 0 && contentRef.current) {
      const highlights =
        contentRef.current.querySelectorAll(".search-highlight");
      if (highlights[currentMatchIndex]) {
        highlights[currentMatchIndex].scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }
    }
  }, [currentMatchIndex, searchMatches]);

  // Highlight search matches in content
  const highlightedContent = useMemo(() => {
    if (!docContent?.content || !searchQuery) return docContent?.content;

    const parts = [];
    let lastIndex = 0;
    const content = docContent.content;
    const lowerContent = content.toLowerCase();
    const lowerQuery = searchQuery.toLowerCase();
    let pos = 0;
    let matchIdx = 0;

    while ((pos = lowerContent.indexOf(lowerQuery, lastIndex)) !== -1) {
      if (pos > lastIndex) {
        parts.push({ type: "text", content: content.slice(lastIndex, pos) });
      }
      parts.push({
        type: "match",
        content: content.slice(pos, pos + searchQuery.length),
        isCurrent: matchIdx === currentMatchIndex,
      });
      lastIndex = pos + searchQuery.length;
      matchIdx++;
    }

    if (lastIndex < content.length) {
      parts.push({ type: "text", content: content.slice(lastIndex) });
    }

    return parts;
  }, [docContent?.content, searchQuery, currentMatchIndex]);

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === "Escape") {
        if (isFullscreen) {
          setIsFullscreen(false);
        } else {
          onClose();
        }
      }
      // Ctrl+F for search
      if ((e.ctrlKey || e.metaKey) && e.key === "f" && isOpen) {
        e.preventDefault();
        document.getElementById("doc-search-input")?.focus();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose, isFullscreen]);

  const handleCopy = async () => {
    if (docContent?.content) {
      await navigator.clipboard.writeText(docContent.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (docContent?.content) {
      const blob = new Blob([docContent.content], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename || "document.txt";
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const goToNextMatch = () => {
    if (searchMatches.length > 0) {
      setCurrentMatchIndex((prev) => (prev + 1) % searchMatches.length);
    }
  };

  const goToPrevMatch = () => {
    if (searchMatches.length > 0) {
      setCurrentMatchIndex(
        (prev) => (prev - 1 + searchMatches.length) % searchMatches.length,
      );
    }
  };

  // Calculate line count
  const lineCount = docContent?.content?.split("\n").length || 0;
  const wordCount =
    docContent?.content?.split(/\s+/).filter(Boolean).length || 0;

  if (!isOpen) return null;

  // Use Portal to render modal at body level, escaping any parent overflow constraints
  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-2 sm:p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-md"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={`relative z-[10000] bg-[var(--bg-secondary)] rounded-xl sm:rounded-2xl border border-[var(--border-subtle)] shadow-[0_0_60px_rgba(139,92,246,0.15)] flex flex-col animate-scaleIn transition-all duration-300 ${
          isFullscreen
            ? "w-full h-full max-w-none max-h-none m-0 rounded-none"
            : "w-full max-w-5xl max-h-[95vh] sm:max-h-[90vh]"
        }`}
      >
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between px-4 sm:px-6 py-3 sm:py-4 border-b border-[var(--border-subtle)] gap-3 sm:gap-0">
          <div className="flex items-center min-w-0 flex-1">
            <div className="p-2 rounded-xl bg-violet-500/15 mr-3 flex-shrink-0">
              <FileText className="h-4 w-4 sm:h-5 sm:w-5 text-violet-400" />
            </div>
            <div className="min-w-0 flex-1">
              <h2 className="text-base sm:text-lg font-semibold text-[var(--text-primary)] truncate">
                {filename}
              </h2>
              {docContent && (
                <div className="flex items-center gap-2 sm:gap-3 mt-1 sm:mt-1.5 flex-wrap">
                  <span className="text-xs text-[var(--text-secondary)] flex items-center px-1.5 sm:px-2 py-0.5 bg-[var(--bg-tertiary)] rounded-md">
                    <Layers className="h-3 w-3 mr-1 sm:mr-1.5 text-violet-400" />
                    {docContent.chunk_count}{" "}
                    <span className="hidden xs:inline ml-0.5">chunks</span>
                  </span>
                  <span className="text-xs text-[var(--text-secondary)] items-center px-1.5 sm:px-2 py-0.5 bg-[var(--bg-tertiary)] rounded-md hidden sm:flex">
                    <Hash className="h-3 w-3 mr-1 sm:mr-1.5 text-blue-400" />
                    {lineCount} lines • {wordCount.toLocaleString()} words
                  </span>
                  <span className="text-xs text-[var(--text-secondary)] items-center px-1.5 sm:px-2 py-0.5 bg-[var(--bg-tertiary)] rounded-md hidden sm:flex">
                    <Calendar className="h-3 w-3 mr-1 sm:mr-1.5 text-emerald-400" />
                    {new Date(docContent.created_at).toLocaleDateString()}
                  </span>
                  {docContent.category && (
                    <span className="text-xs text-violet-300 flex items-center px-2 sm:px-2.5 py-0.5 bg-violet-500/15 rounded-full border border-violet-500/30">
                      <Tag className="h-3 w-3 mr-1 sm:mr-1.5" />
                      {docContent.category}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Toolbar - stacks on mobile */}
          <div className="flex items-center gap-1 sm:ml-4 justify-end">
            {/* Search bar - collapses on mobile */}
            {docContent?.content && (
              <div className="relative flex items-center mr-1 sm:mr-2">
                <div className="relative">
                  <Search className="absolute left-2.5 sm:left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-secondary)]" />
                  <input
                    id="doc-search-input"
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search..."
                    className="pl-8 sm:pl-9 pr-2 sm:pr-3 py-1.5 sm:py-2 w-28 sm:w-52 text-sm bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20"
                  />
                </div>
                {searchMatches.length > 0 && (
                  <div className="flex items-center ml-1 sm:ml-2 gap-0.5 sm:gap-1">
                    <span className="text-xs text-[var(--text-secondary)] font-medium px-1.5 sm:px-2 py-0.5 sm:py-1 bg-violet-500/15 rounded">
                      {currentMatchIndex + 1}/{searchMatches.length}
                    </span>
                    <button
                      onClick={goToPrevMatch}
                      className="p-1 sm:p-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--hover-bg)] rounded-lg transition-colors border border-transparent hover:border-[var(--border-subtle)]"
                    >
                      <ChevronUp className="h-4 w-4" />
                    </button>
                    <button
                      onClick={goToNextMatch}
                      className="p-1 sm:p-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--hover-bg)] rounded-lg transition-colors border border-transparent hover:border-[var(--border-subtle)]"
                    >
                      <ChevronDown className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Line numbers toggle - hidden on mobile */}
            <button
              onClick={() => setShowLineNumbers(!showLineNumbers)}
              className={`p-1.5 sm:p-2 rounded-lg transition-all duration-200 border hidden sm:block ${showLineNumbers ? "text-violet-300 bg-violet-500/15 border-violet-500/30" : "text-[var(--text-secondary)] border-transparent hover:text-[var(--text-primary)] hover:bg-[var(--hover-bg)] hover:border-[var(--border-subtle)]"}`}
              title="Toggle line numbers"
            >
              <Hash className="h-4 w-4" />
            </button>

            {/* Download button */}
            {docContent?.content && (
              <button
                onClick={handleDownload}
                className="p-1.5 sm:p-2 text-[var(--text-secondary)] hover:text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-colors border border-transparent hover:border-emerald-500/30"
                title="Download"
              >
                <Download className="h-4 w-4" />
              </button>
            )}

            {/* Copy button */}
            {docContent?.content && (
              <button
                onClick={handleCopy}
                className="p-1.5 sm:p-2 text-[var(--text-secondary)] hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors border border-transparent hover:border-blue-500/30"
                title="Copy content"
              >
                {copied ? (
                  <Check className="h-4 w-4 text-emerald-400" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </button>
            )}

            {/* Fullscreen toggle - hidden on mobile (already fullscreen-ish) */}
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className={`p-1.5 sm:p-2 rounded-lg transition-all duration-200 border hidden sm:block ${isFullscreen ? "text-amber-300 bg-amber-500/15 border-amber-500/30" : "text-[var(--text-secondary)] border-transparent hover:text-amber-400 hover:bg-amber-500/10 hover:border-amber-500/30"}`}
              title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
            >
              {isFullscreen ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </button>

            {/* Close button */}
            <button
              onClick={onClose}
              className="p-1.5 sm:p-2 text-[var(--text-secondary)] hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors border border-transparent hover:border-red-500/30"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div
          ref={contentRef}
          className="flex-1 overflow-y-auto custom-scrollbar"
        >
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12 sm:py-20">
              <Loader2 className="h-6 w-6 sm:h-8 sm:w-8 text-violet-400 animate-spin mb-3 sm:mb-4" />
              <p className="text-sm text-[var(--text-secondary)]">
                Loading document content...
              </p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12 sm:py-20 px-4">
              <div className="p-3 rounded-xl bg-red-500/15 mb-4">
                <AlertCircle className="h-6 w-6 sm:h-8 sm:w-8 text-red-400" />
              </div>
              <p className="text-sm text-red-400 font-medium text-center">
                Failed to load document
              </p>
              <p className="text-xs text-[var(--text-muted)] mt-1 text-center">
                {error.message}
              </p>
            </div>
          ) : docContent?.content ? (
            <div className="relative">
              {showLineNumbers ? (
                <div className="flex">
                  {/* Line numbers */}
                  <div className="flex-shrink-0 select-none text-right pr-4 py-6 pl-4 bg-[var(--bg-primary)]/30 border-r border-[var(--border-subtle)]">
                    {docContent.content.split("\n").map((_, i) => (
                      <div
                        key={i}
                        className="text-xs text-[var(--text-muted)] leading-relaxed font-mono"
                      >
                        {i + 1}
                      </div>
                    ))}
                  </div>
                  {/* Content with highlights */}
                  <pre className="flex-1 whitespace-pre-wrap text-sm text-[var(--text-secondary)] font-mono leading-relaxed p-6 overflow-x-auto">
                    {Array.isArray(highlightedContent)
                      ? highlightedContent.map((part, i) =>
                          part.type === "match" ? (
                            <mark
                              key={i}
                              className={`search-highlight rounded px-0.5 ${part.isCurrent ? "bg-yellow-400 text-black" : "bg-yellow-400/30 text-[var(--text-primary)]"}`}
                            >
                              {part.content}
                            </mark>
                          ) : (
                            <span key={i}>{part.content}</span>
                          ),
                        )
                      : highlightedContent}
                  </pre>
                </div>
              ) : (
                <pre className="whitespace-pre-wrap text-sm text-[var(--text-secondary)] font-mono leading-relaxed p-6">
                  {Array.isArray(highlightedContent)
                    ? highlightedContent.map((part, i) =>
                        part.type === "match" ? (
                          <mark
                            key={i}
                            className={`search-highlight rounded px-0.5 ${part.isCurrent ? "bg-yellow-400 text-black" : "bg-yellow-400/30 text-[var(--text-primary)]"}`}
                          >
                            {part.content}
                          </mark>
                        ) : (
                          <span key={i}>{part.content}</span>
                        ),
                      )
                    : highlightedContent}
                </pre>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="p-3 rounded-xl bg-[var(--bg-secondary)]/50 mb-4">
                <FileText className="h-8 w-8 text-[var(--text-muted)]" />
              </div>
              <p className="text-sm text-[var(--text-secondary)]">
                No content available
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-[var(--border-subtle)] flex items-center justify-between bg-[var(--bg-primary)]/30">
          <div className="flex items-center gap-4">
            <p className="text-xs text-[var(--text-muted)]">
              <kbd className="px-1.5 py-0.5 bg-[var(--bg-secondary)] rounded text-[var(--text-secondary)] font-mono">
                Esc
              </kbd>{" "}
              close
            </p>
            <p className="text-xs text-[var(--text-muted)]">
              <kbd className="px-1.5 py-0.5 bg-[var(--bg-secondary)] rounded text-[var(--text-secondary)] font-mono">
                Ctrl+F
              </kbd>{" "}
              search
            </p>
          </div>
          <div className="flex items-center gap-2">
            {searchMatches.length > 0 && (
              <span className="text-xs text-violet-400">
                {searchMatches.length} match
                {searchMatches.length !== 1 ? "es" : ""} found
              </span>
            )}
            <button
              onClick={onClose}
              className="px-4 py-1.5 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] bg-[var(--bg-secondary)] hover:bg-[var(--hover-bg)] rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
}
