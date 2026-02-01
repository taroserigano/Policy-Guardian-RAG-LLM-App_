/**
 * Citations list component showing source documents with visual score indicators.
 */
import { useState, useCallback, memo } from "react";
import {
  FileText,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from "lucide-react";

// Get color based on relevance score
const getScoreColor = (score) => {
  if (score >= 0.8)
    return {
      bg: "bg-emerald-500/20",
      text: "text-emerald-400",
      border: "border-emerald-500/30",
    };
  if (score >= 0.6)
    return {
      bg: "bg-violet-500/20",
      text: "text-violet-400",
      border: "border-violet-500/30",
    };
  if (score >= 0.4)
    return {
      bg: "bg-amber-500/20",
      text: "text-amber-400",
      border: "border-amber-500/30",
    };
  return {
    bg: "bg-zinc-500/20",
    text: "text-zinc-400",
    border: "border-zinc-500/30",
  };
};

// Get relevance label
const getRelevanceLabel = (score) => {
  if (score >= 0.8) return "High";
  if (score >= 0.6) return "Good";
  if (score >= 0.4) return "Fair";
  return "Low";
};

function CitationsList({ citations }) {
  const [expandedIndex, setExpandedIndex] = useState(null);
  const [showAll, setShowAll] = useState(false);

  const toggleExpand = useCallback((index) => {
    setExpandedIndex((prev) => (prev === index ? null : index));
  }, []);

  const toggleShowAll = useCallback(() => {
    setShowAll((prev) => !prev);
  }, []);

  if (!citations || citations.length === 0) {
    return null;
  }

  // Show only top 3 by default
  const displayedCitations = showAll ? citations : citations.slice(0, 3);
  const hasMore = citations.length > 3;

  return (
    <div className="bg-gradient-to-br from-[var(--bg-secondary)]/80 to-[var(--bg-secondary)]/60 rounded-xl border border-[var(--border-subtle)] p-4 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <div className="p-1.5 rounded-lg bg-violet-500/15 mr-2">
            <Sparkles className="h-3.5 w-3.5 text-violet-400" />
          </div>
          <h4 className="text-sm font-semibold text-[var(--text-primary)]">
            Sources
          </h4>
          <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-violet-500/15 text-violet-300 border border-violet-500/30 font-medium">
            {citations.length}
          </span>
        </div>
      </div>

      <div className="space-y-2">
        {displayedCitations.map((citation, index) => {
          const scoreColors = getScoreColor(citation.score);
          return (
            <div
              key={index}
              className={`bg-[var(--bg-secondary)]/50 rounded-lg border ${scoreColors.border} hover:bg-[var(--hover-bg)] transition-all duration-200 overflow-hidden`}
            >
              <button
                onClick={() => toggleExpand(index)}
                className="w-full flex items-start p-3 text-left group"
              >
                {/* Score indicator bar */}
                <div className="relative mr-3 flex-shrink-0">
                  <div
                    className={`w-1 h-full absolute left-0 top-0 rounded-full ${scoreColors.bg}`}
                  />
                  <FileText className={`h-4 w-4 ${scoreColors.text} ml-2`} />
                </div>

                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[var(--text-primary)] truncate group-hover:text-violet-300 transition-colors">
                    {citation.filename}
                  </p>

                  {/* Show text preview */}
                  {citation.text && (
                    <p className="text-xs text-[var(--text-secondary)] mt-1 line-clamp-2 leading-relaxed">
                      {citation.text}
                    </p>
                  )}

                  <div className="flex items-center flex-wrap gap-2 mt-1.5">
                    {citation.page_number && (
                      <span className="text-xs px-2 py-0.5 rounded-md bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border border-[var(--border-subtle)]">
                        Page {citation.page_number}
                      </span>
                    )}
                  </div>
                </div>

                {citation.text && (
                  <div className="ml-2 flex-shrink-0">
                    {expandedIndex === index ? (
                      <ChevronUp className="h-4 w-4 text-[var(--text-muted)] group-hover:text-[var(--text-secondary)]" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-[var(--text-muted)] group-hover:text-[var(--text-secondary)]" />
                    )}
                  </div>
                )}
              </button>

              {/* Expandable full text */}
              {citation.text && expandedIndex === index && (
                <div className="px-3 pb-3 pt-0 animate-slideUp">
                  <div
                    className={`text-xs text-[var(--text-secondary)] bg-[var(--bg-primary)]/60 p-3 rounded-lg border ${scoreColors.border}`}
                  >
                    <p className="leading-relaxed">{citation.text}</p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Show more/less toggle */}
      {hasMore && (
        <button
          onClick={toggleShowAll}
          className="w-full mt-3 py-2 text-xs text-[var(--text-secondary)] hover:text-violet-400 transition-colors flex items-center justify-center gap-1 font-medium"
        >
          {showAll ? (
            <>
              <ChevronUp className="h-3 w-3" />
              Show less
            </>
          ) : (
            <>
              <ChevronDown className="h-3 w-3" />
              Show {citations.length - 3} more sources
            </>
          )}
        </button>
      )}
    </div>
  );
}

export default memo(CitationsList);
