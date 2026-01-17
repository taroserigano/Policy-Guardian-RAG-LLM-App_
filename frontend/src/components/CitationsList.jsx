/**
 * Citations list component showing source documents.
 */
import { FileText, ExternalLink } from "lucide-react";

export default function CitationsList({ citations }) {
  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex items-center mb-3">
        <ExternalLink className="h-4 w-4 text-gray-600 mr-2" />
        <h4 className="text-sm font-semibold text-gray-700">
          Sources ({citations.length})
        </h4>
      </div>

      <div className="space-y-2">
        {citations.map((citation, index) => (
          <div
            key={index}
            className="flex items-start p-3 bg-gray-50 rounded-md border border-gray-200 hover:bg-gray-100 transition-colors"
          >
            <FileText className="h-4 w-4 text-gray-500 mr-2 mt-0.5 flex-shrink-0" />

            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {citation.filename}
              </p>

              <div className="flex items-center space-x-3 mt-1 text-xs text-gray-600">
                {citation.page_number && (
                  <span>Page {citation.page_number}</span>
                )}
                <span>Chunk {citation.chunk_index}</span>
                <span className="text-primary-600 font-medium">
                  Score: {(citation.score * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
