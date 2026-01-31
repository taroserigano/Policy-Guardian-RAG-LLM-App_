/**
 * Compliance checking page.
 * Combines document and image analysis for thorough compliance assessment.
 */
import { useState, useMemo, useCallback } from "react";
import { AlertCircle, FileText, Package, Zap } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import ComplianceChecker from "../components/ComplianceChecker";
import BaggageDamageChecker from "../components/BaggageDamageChecker";
import CombinedComplianceChecker from "../components/CombinedComplianceChecker";
import ModelPicker from "../components/ModelPicker";
import { useDocuments, useImages } from "../hooks/useApi";

// Generate a simple session ID for user tracking - memoized
const useUserId = () => {
  return useMemo(() => {
    let userId = localStorage.getItem("user_id");
    if (!userId) {
      userId = `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem("user_id", userId);
    }
    return userId;
  }, []);
};

export default function CompliancePage() {
  const [selectedProvider, setSelectedProvider] = useState("openai");
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [selectedImageIds, setSelectedImageIds] = useState([]);
  const [activeTab, setActiveTab] = useState("quick"); // "quick", "general", or "baggage"

  const userId = useUserId();
  const queryClient = useQueryClient();

  // Fetch documents
  const {
    data: documents = [],
    isLoading: docsLoading,
    error: docsError,
  } = useDocuments();

  // Fetch images
  const {
    data: images = [],
    isLoading: imagesLoading,
    error: imagesError,
  } = useImages();

  const handleProviderChange = useCallback((newProvider) => {
    setSelectedProvider(newProvider);
    setSelectedModel("");
  }, []);

  // Callback when a library image is deleted
  const handleLibraryImageDeleted = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["images"] });
  }, [queryClient]);

  return (
    <div className="h-full flex flex-col">
      {/* Header with model picker */}
      <div className="bg-[var(--bg-secondary)] border-b border-[var(--border-subtle)] px-4 py-3 flex items-center justify-between rounded-t-xl transition-colors duration-300">
        <div>
          <h1 className="text-lg font-semibold text-[var(--text-primary)]">
            Compliance Checker
          </h1>
          <p className="text-sm text-[var(--text-secondary)]">
            Analyze documents and images for policy compliance
          </p>
        </div>
        <div className="flex items-center gap-4">
          <ModelPicker
            selectedProvider={selectedProvider}
            selectedModel={selectedModel}
            onProviderChange={handleProviderChange}
            onModelChange={setSelectedModel}
          />
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-[var(--bg-secondary)] border-b border-[var(--border-subtle)] px-4">
        <div className="flex gap-1">
          <button
            onClick={() => setActiveTab("quick")}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
              activeTab === "quick"
                ? "text-violet-400 border-violet-500"
                : "text-[var(--text-muted)] border-transparent hover:text-[var(--text-secondary)]"
            }`}
          >
            <Zap className="w-4 h-4" />
            Quick Check
          </button>
          <button
            onClick={() => setActiveTab("general")}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
              activeTab === "general"
                ? "text-violet-400 border-violet-500"
                : "text-[var(--text-muted)] border-transparent hover:text-[var(--text-secondary)]"
            }`}
          >
            <FileText className="w-4 h-4" />
            From Library
          </button>
          <button
            onClick={() => setActiveTab("baggage")}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
              activeTab === "baggage"
                ? "text-violet-400 border-violet-500"
                : "text-[var(--text-muted)] border-transparent hover:text-[var(--text-secondary)]"
            }`}
          >
            <Package className="w-4 h-4" />
            Baggage Claims
          </button>
        </div>
      </div>

      {/* Error display */}
      {(docsError || imagesError) && activeTab === "general" && (
        <div className="m-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-red-400">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">
            {docsError && `Documents: ${docsError.message}`}
            {docsError && imagesError && " | "}
            {imagesError && `Images: ${imagesError.message}`}
          </span>
        </div>
      )}

      {/* Loading state */}
      {(docsLoading || imagesLoading) && activeTab === "general" && (
        <div className="m-4 p-3 bg-violet-500/10 border border-violet-500/20 rounded-lg">
          <span className="text-sm text-violet-400">Loading resources...</span>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === "quick" ? (
          <CombinedComplianceChecker
            provider={selectedProvider}
            userId={userId}
            libraryDocuments={documents}
            libraryImages={images}
            isLoadingLibrary={docsLoading || imagesLoading}
            onLibraryImageDeleted={handleLibraryImageDeleted}
          />
        ) : activeTab === "general" ? (
          <ComplianceChecker
            documents={documents}
            images={images}
            selectedDocIds={selectedDocIds}
            selectedImageIds={selectedImageIds}
            provider={selectedProvider}
            model={selectedModel}
            userId={userId}
            onSelectDocuments={setSelectedDocIds}
            onSelectImages={setSelectedImageIds}
          />
        ) : (
          <BaggageDamageChecker visionProvider={selectedProvider} />
        )}
      </div>
    </div>
  );
}
