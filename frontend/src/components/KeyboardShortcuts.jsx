/**
 * Keyboard shortcuts help modal.
 * Shows available keyboard shortcuts when user presses "?".
 */
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { X, Keyboard, Command } from "lucide-react";

const shortcuts = [
  {
    category: "Chat",
    items: [
      { keys: ["Ctrl", "E"], description: "Export chat history" },
      { keys: ["Ctrl", "Shift", "C"], description: "Clear conversation" },
      { keys: ["Ctrl", "/"], description: "Toggle RAG options panel" },
      { keys: ["Esc"], description: "Close modals/panels" },
    ],
  },
  {
    category: "Navigation",
    items: [{ keys: ["?"], description: "Show keyboard shortcuts" }],
  },
  {
    category: "General",
    items: [
      { keys: ["Ctrl", "K"], description: "Focus search/input" },
      { keys: ["Enter"], description: "Send message" },
      { keys: ["Shift", "Enter"], description: "New line in input" },
    ],
  },
];

function KeyBadge({ children }) {
  return (
    <kbd className="px-2 py-1 text-xs font-mono bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border border-[var(--border-subtle)] rounded-md">
      {children}
    </kbd>
  );
}

export default function KeyboardShortcuts() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e) => {
      // Show help on "?" key (Shift + /)
      if (e.key === "?" && !e.ctrlKey && !e.altKey && !e.metaKey) {
        // Don't trigger if typing in an input
        const target = e.target;
        if (
          target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable
        ) {
          return;
        }
        e.preventDefault();
        setIsOpen(true);
      }
      // Close on Escape
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-md"
        onClick={() => setIsOpen(false)}
      />

      {/* Modal */}
      <div className="relative z-[10000] w-full max-w-lg mx-4 bg-[var(--bg-secondary)] rounded-2xl border border-[var(--border-subtle)] shadow-[0_0_60px_rgba(139,92,246,0.15)] animate-scaleIn">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-subtle)]">
          <div className="flex items-center">
            <div className="p-2 rounded-xl bg-violet-500/15 mr-3">
              <Keyboard className="h-5 w-5 text-violet-400" />
            </div>
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">
              Keyboard Shortcuts
            </h2>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--hover-bg)] rounded-lg transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[60vh] overflow-y-auto">
          <div className="space-y-6">
            {shortcuts.map((section) => (
              <div key={section.category}>
                <h3 className="text-sm font-semibold text-[var(--text-secondary)] mb-3 flex items-center">
                  <Command className="h-3.5 w-3.5 mr-2 text-violet-400" />
                  {section.category}
                </h3>
                <div className="space-y-2">
                  {section.items.map((shortcut, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between py-2 px-3 rounded-lg bg-[var(--bg-tertiary)]/50"
                    >
                      <span className="text-sm text-[var(--text-muted)]">
                        {shortcut.description}
                      </span>
                      <div className="flex items-center gap-1">
                        {shortcut.keys.map((key, keyIdx) => (
                          <span key={keyIdx} className="flex items-center">
                            <KeyBadge>{key}</KeyBadge>
                            {keyIdx < shortcut.keys.length - 1 && (
                              <span className="mx-1 text-xs text-[var(--text-muted)]">
                                +
                              </span>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[var(--border-subtle)]">
          <p className="text-xs text-[var(--text-muted)] text-center">
            Press <KeyBadge>?</KeyBadge> anytime to show this help
          </p>
        </div>
      </div>
    </div>,
    document.body,
  );
}
