/**
 * React Query hooks for data fetching and mutations.
 * Provides caching, loading states, and error handling.
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getDocuments,
  uploadDocument,
  deleteDocument,
  bulkDeleteDocuments,
  getDocumentContent,
  sendChatMessage,
  getChatHistory,
  clearChatHistory,
} from "../api/client";

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

/**
 * Hook to delete a document
 * Invalidates document list on success
 */
export const useDeleteDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      // Invalidate and refetch documents list
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
};

/**
 * Hook to bulk delete multiple documents
 * Invalidates document list on success
 */
export const useBulkDeleteDocuments = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: bulkDeleteDocuments,
    onSuccess: () => {
      // Invalidate and refetch documents list
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
};

/**
 * Hook to fetch document content
 * @param {string} docId - Document UUID
 * @param {boolean} enabled - Whether to fetch
 */
export const useDocumentContent = (docId, enabled = true) => {
  return useQuery({
    queryKey: ["documentContent", docId],
    queryFn: () => getDocumentContent(docId),
    enabled: enabled && !!docId,
    staleTime: 60000, // Cache for 1 minute
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

/**
 * Hook to fetch chat history for a user
 * @param {string} userId - User identifier
 * @param {number} limit - Max entries to fetch
 */
export const useChatHistory = (userId, limit = 50) => {
  return useQuery({
    queryKey: ["chatHistory", userId],
    queryFn: () => getChatHistory(userId, limit),
    enabled: !!userId, // Only fetch if userId is provided
    staleTime: 60000, // Consider fresh for 1 minute
  });
};

/**
 * Hook to clear chat history
 * Invalidates chat history cache on success
 */
export const useClearChatHistory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: clearChatHistory,
    onSuccess: (_, userId) => {
      // Invalidate chat history for this user
      queryClient.invalidateQueries({ queryKey: ["chatHistory", userId] });
    },
  });
};
