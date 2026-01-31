/**
 * PDF Viewer component using iframe with Google Docs Viewer as fallback
 * Displays PDFs in their native format for better readability
 */
import { useState, useEffect, memo } from "react";
import { createPortal } from "react-dom";
import {
  X,
  Download,
  AlertCircle,
  Loader2,
  ZoomIn,
  ZoomOut,
  RotateCw,
} from "lucide-react";

function PdfViewer({ docId, filename, isOpen, onClose }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [zoom, setZoom] = useState(100);

  const pdfUrl = `http://localhost:8001/api/docs/${docId}/file`;

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      setError(null);
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }

    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen, onClose]);

  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = pdfUrl;
    link.download = filename;
    link.click();
  };

  const handleIframeLoad = () => {
    setLoading(false);
  };

  const handleIframeError = () => {
    setError("Failed to load PDF. Please try downloading instead.");
    setLoading(false);
  };

  if (!isOpen) return null;

  const modalContent = (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full h-full max-w-7xl max-h-[95vh] m-4 bg-[var(--bg-secondary)] rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-modalIn">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-subtle)] bg-[var(--bg-tertiary)]">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="p-2 rounded-xl bg-blue-500/15">
              <svg
                className="h-5 w-5 text-blue-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-base font-semibold text-[var(--text-primary)] truncate">
                {filename}
              </h2>
              <p className="text-xs text-[var(--text-muted)]">PDF Document</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleDownload}
              className="p-2.5 rounded-xl hover:bg-[var(--hover-bg)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
              title="Download PDF"
            >
              <Download className="h-5 w-5" />
            </button>
            <button
              onClick={onClose}
              className="p-2.5 rounded-xl hover:bg-[var(--hover-bg)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* PDF Viewer Container */}
        <div className="flex-1 relative bg-gray-900">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-[var(--bg-primary)]">
              <div className="text-center">
                <Loader2 className="h-8 w-8 text-blue-400 animate-spin mx-auto mb-3" />
                <p className="text-sm text-[var(--text-muted)]">
                  Loading PDF...
                </p>
              </div>
            </div>
          )}

          {error ? (
            <div className="absolute inset-0 flex items-center justify-center bg-[var(--bg-primary)]">
              <div className="text-center max-w-md px-6">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-500/10 mb-4">
                  <AlertCircle className="h-8 w-8 text-red-400" />
                </div>
                <p className="text-sm text-[var(--text-secondary)] mb-4">
                  {error}
                </p>
                <button
                  onClick={handleDownload}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors flex items-center gap-2 mx-auto"
                >
                  <Download className="h-4 w-4" />
                  Download PDF
                </button>
              </div>
            </div>
          ) : (
            <iframe
              src={`${pdfUrl}#toolbar=1&navpanes=1&scrollbar=1`}
              className="w-full h-full border-0"
              title={filename}
              onLoad={handleIframeLoad}
              onError={handleIframeError}
            />
          )}
        </div>

        {/* Footer with tips */}
        <div className="px-6 py-3 border-t border-[var(--border-subtle)] bg-[var(--bg-tertiary)]">
          <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
            <span>Use your browser's PDF controls to navigate and zoom</span>
            <span>Press ESC to close</span>
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}

export default memo(PdfViewer);
