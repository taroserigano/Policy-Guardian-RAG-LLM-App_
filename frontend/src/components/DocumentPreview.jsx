/**
 * Document preview modal component.
 * Displays full document content in a modal overlay.
 * Uses React Portal to render at document body level.
 */
import { useEffect } from "react";
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
} from "lucide-react";
import { useState } from "react";
import { useDocumentContent } from "../hooks/useApi";

export default function DocumentPreview({ docId, filename, isOpen, onClose }) {
  const [copied, setCopied] = useState(false);
  const {
    data: docContent,
    isLoading,
    error,
  } = useDocumentContent(docId, isOpen);

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === "Escape") onClose();
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  const handleCopy = async () => {
    if (docContent?.content) {
      await navigator.clipboard.writeText(docContent.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!isOpen) return null;

  // Use Portal to render modal at body level, escaping any parent overflow constraints
  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-md"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-[10000] w-full max-w-4xl max-h-[85vh] mx-4 bg-zinc-900 rounded-2xl border border-zinc-700 shadow-[0_0_60px_rgba(139,92,246,0.15)] flex flex-col animate-scaleIn">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
          <div className="flex items-center min-w-0">
            <div className="p-2 rounded-xl bg-violet-500/15 mr-3 flex-shrink-0">
              <FileText className="h-5 w-5 text-violet-400" />
            </div>
            <div className="min-w-0">
              <h2 className="text-lg font-semibold text-white truncate">
                {filename}
              </h2>
              {docContent && (
                <div className="flex items-center gap-4 mt-1">
                  <span className="text-xs text-zinc-500 flex items-center">
                    <Layers className="h-3 w-3 mr-1" />
                    {docContent.chunk_count} chunks
                  </span>
                  <span className="text-xs text-zinc-500 flex items-center">
                    <Calendar className="h-3 w-3 mr-1" />
                    {new Date(docContent.created_at).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Copy button */}
            {docContent?.content && (
              <button
                onClick={handleCopy}
                className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
                title="Copy content"
              >
                {copied ? (
                  <Check className="h-5 w-5 text-emerald-400" />
                ) : (
                  <Copy className="h-5 w-5" />
                )}
              </button>
            )}

            {/* Close button */}
            <button
              onClick={onClose}
              className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader2 className="h-8 w-8 text-violet-400 animate-spin mb-4" />
              <p className="text-sm text-zinc-400">
                Loading document content...
              </p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="p-3 rounded-xl bg-red-500/15 mb-4">
                <AlertCircle className="h-8 w-8 text-red-400" />
              </div>
              <p className="text-sm text-red-400 font-medium">
                Failed to load document
              </p>
              <p className="text-xs text-zinc-500 mt-1">{error.message}</p>
            </div>
          ) : docContent?.content ? (
            <div className="prose prose-invert prose-zinc max-w-none">
              <pre className="whitespace-pre-wrap text-sm text-zinc-300 font-sans leading-relaxed bg-zinc-800/50 rounded-xl p-6 border border-zinc-700/50">
                {docContent.content}
              </pre>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="p-3 rounded-xl bg-zinc-800/50 mb-4">
                <FileText className="h-8 w-8 text-zinc-600" />
              </div>
              <p className="text-sm text-zinc-400">No content available</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-zinc-800 flex items-center justify-between">
          <p className="text-xs text-zinc-500">
            Press{" "}
            <kbd className="px-1.5 py-0.5 bg-zinc-800 rounded text-zinc-400">
              Esc
            </kbd>{" "}
            to close
          </p>
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-zinc-300 hover:text-white bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
