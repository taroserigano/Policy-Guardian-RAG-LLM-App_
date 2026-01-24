/**
 * Document category editor component.
 * Allows selecting category and adding tags to documents.
 */
import { useState } from "react";
import { Tag, X, Check, Folder, Plus } from "lucide-react";

const CATEGORIES = [
  { id: "policy", name: "Policy", color: "violet" },
  { id: "legal", name: "Legal", color: "blue" },
  { id: "hr", name: "HR", color: "emerald" },
  { id: "compliance", name: "Compliance", color: "amber" },
  { id: "technical", name: "Technical", color: "cyan" },
  { id: "other", name: "Other", color: "gray" },
];

const CATEGORY_COLORS = {
  policy: "bg-violet-500/20 text-violet-300 border-violet-500/40",
  legal: "bg-blue-500/20 text-blue-300 border-blue-500/40",
  hr: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
  compliance: "bg-amber-500/20 text-amber-300 border-amber-500/40",
  technical: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40",
  other: "bg-gray-500/20 text-gray-300 border-gray-500/40",
};

export function CategoryBadge({ category, size = "sm" }) {
  if (!category) return null;

  const categoryInfo = CATEGORIES.find((c) => c.id === category);
  const colorClass = CATEGORY_COLORS[category] || CATEGORY_COLORS.other;

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full border ${colorClass} ${
        size === "sm" ? "text-xs" : "text-sm"
      }`}
    >
      <Folder className={`mr-1 ${size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5"}`} />
      {categoryInfo?.name || category}
    </span>
  );
}

export function TagBadge({ tag, onRemove, size = "sm" }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-1 bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-full ${
        size === "sm" ? "text-xs" : "text-sm"
      } text-[var(--text-secondary)] font-medium`}
    >
      <Tag
        className={`${size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5"} text-violet-400`}
      />
      {tag}
      {onRemove && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRemove(tag);
          }}
          className="hover:text-red-400 transition-colors ml-0.5"
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  );
}

export default function DocumentCategoryEditor({
  category,
  tags = [],
  onCategoryChange,
  onTagsChange,
  compact = false,
}) {
  const [newTag, setNewTag] = useState("");
  const [isAddingTag, setIsAddingTag] = useState(false);

  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      onTagsChange?.([...tags, newTag.trim()]);
      setNewTag("");
      setIsAddingTag(false);
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    onTagsChange?.(tags.filter((t) => t !== tagToRemove));
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddTag();
    } else if (e.key === "Escape") {
      setIsAddingTag(false);
      setNewTag("");
    }
  };

  if (compact) {
    return (
      <div className="flex items-center gap-2 flex-wrap">
        {/* Category Dropdown */}
        <select
          value={category || ""}
          onChange={(e) => onCategoryChange?.(e.target.value || null)}
          className="text-xs px-2 py-1 bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg text-[var(--text-secondary)] focus:outline-none focus:border-violet-500/50"
        >
          <option value="">No Category</option>
          {CATEGORIES.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.name}
            </option>
          ))}
        </select>

        {/* Tags */}
        {tags.map((tag) => (
          <TagBadge key={tag} tag={tag} onRemove={handleRemoveTag} />
        ))}

        {/* Add Tag */}
        {isAddingTag ? (
          <div className="flex items-center gap-1">
            <input
              type="text"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Tag..."
              className="w-20 text-xs px-2 py-1 bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-violet-500/50"
              autoFocus
            />
            <button
              onClick={handleAddTag}
              className="p-1 text-emerald-400 hover:bg-emerald-500/10 rounded"
            >
              <Check className="h-3 w-3" />
            </button>
            <button
              onClick={() => {
                setIsAddingTag(false);
                setNewTag("");
              }}
              className="p-1 text-[var(--text-muted)] hover:text-red-400 rounded"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => setIsAddingTag(true)}
            className="text-xs px-2 py-1 text-[var(--text-muted)] hover:text-violet-400 hover:bg-violet-500/10 rounded-lg transition-colors"
          >
            <Plus className="h-3 w-3 inline mr-1" />
            Tag
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Category Selection */}
      <div>
        <label className="text-sm font-medium text-[var(--text-primary)] mb-2 block">
          Category
        </label>
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() =>
                onCategoryChange?.(cat.id === category ? null : cat.id)
              }
              className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-all duration-200 ${
                category === cat.id
                  ? CATEGORY_COLORS[cat.id]
                  : "bg-[var(--bg-tertiary)]/50 text-[var(--text-secondary)] border-[var(--border-subtle)] hover:border-violet-500/40 hover:text-[var(--text-primary)] hover:bg-[var(--hover-bg)]"
              }`}
            >
              <Folder className="h-3 w-3 inline mr-1.5" />
              {cat.name}
            </button>
          ))}
        </div>
      </div>

      {/* Tags */}
      <div>
        <label className="text-sm font-medium text-[var(--text-secondary)] mb-2 block">
          Tags
        </label>
        <div className="flex flex-wrap gap-2 items-center">
          {tags.map((tag) => (
            <TagBadge key={tag} tag={tag} onRemove={handleRemoveTag} />
          ))}

          {isAddingTag ? (
            <div className="flex items-center gap-1">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter tag..."
                className="w-24 text-xs px-2 py-1.5 bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-violet-500/50"
                autoFocus
              />
              <button
                onClick={handleAddTag}
                className="p-1.5 text-emerald-400 hover:bg-emerald-500/10 rounded-lg"
              >
                <Check className="h-4 w-4" />
              </button>
              <button
                onClick={() => {
                  setIsAddingTag(false);
                  setNewTag("");
                }}
                className="p-1.5 text-[var(--text-muted)] hover:text-red-400 hover:bg-red-500/10 rounded-lg"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setIsAddingTag(true)}
              className="flex items-center gap-1 px-3 py-1.5 text-xs text-[var(--text-muted)] hover:text-violet-400 bg-[var(--bg-secondary)]/50 hover:bg-violet-500/10 border border-dashed border-[var(--border-subtle)] hover:border-violet-500/30 rounded-lg transition-all"
            >
              <Plus className="h-3 w-3" />
              Add Tag
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
