/**
 * React Query hooks for data fetching and mutations.
 * Provides caching, loading states, and error handling.
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getDocuments, uploadDocument, sendChatMessage } from "../api/client";

// ============================================================================
// Document Hooks
// ============================================================================

/**
 * Hook to fetch all documents
 * Automatically refetches and caches data
 */
export const useDocuments = () => {
  return useQuery({
    queryKey: ["documents"],
    queryFn: getDocuments,
    staleTime: 30000, // Consider data fresh for 30 seconds
    refetchOnWindowFocus: true,
  });
};

/**
 * Hook to upload a document
 * Invalidates document list on success
 */
export const useUploadDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      // Invalidate and refetch documents list
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
};

// ============================================================================
// Chat Hooks
// ============================================================================

/**
 * Hook to send chat messages
 * Does not cache chat responses
 */
export const useChatMutation = () => {
  return useMutation({
    mutationFn: sendChatMessage,
    // Don't cache chat responses
    gcTime: 0,
  });
};
