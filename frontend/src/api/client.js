/**
 * API client for backend communication.
 * Uses axios for HTTP requests.
 */
import axios from "axios";

// Use relative URLs to leverage Vite's proxy in development
// In production, this should be configured via VITE_API_BASE_URL env var
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 120000, // 2 minutes for long-running requests
});

// Request interceptor for adding auth headers if needed
api.interceptors.request.use(
  (config) => {
    // Add API key if stored in localStorage
    const apiKey = localStorage.getItem("api_key");
    if (apiKey) {
      config.headers["X-API-Key"] = apiKey;
    }

    // Add JWT auth token if available
    const accessToken = localStorage.getItem("access_token");
    if (accessToken) {
      config.headers["Authorization"] = `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error),
);

// ============================================================================
// Document API
// ============================================================================

/**
 * Upload a document file
 * @param {File} file - File object to upload
 * @param {string} category - Optional category for the document
 * @returns {Promise} - Upload response with doc_id
 */
export const uploadDocument = async (file, category = null) => {
  const formData = new FormData();
  formData.append("file", file);
  if (category) {
    formData.append("category", category);
  }

  const response = await api.post("/api/docs/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};

/**
 * Upload multiple documents at once
 * @param {File[]} files - Array of File objects to upload
 * @returns {Promise} - Batch upload response with results
 */
export const uploadDocumentsBatch = async (files) => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await api.post("/api/docs/upload/batch", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};

/**
 * Upload multiple documents with per-file progress tracking
 * @param {File[]} files - Array of File objects to upload
 * @param {Function} onProgress - Callback with progress info (fileIndex, filename, status, percent)
 * @returns {Promise} - Array of upload results
 */
export const uploadDocumentsWithProgress = async (files, onProgress) => {
  const results = [];

  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    onProgress?.(i, file.name, "uploading", 0);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await api.post("/api/docs/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total,
          );
          onProgress?.(i, file.name, "uploading", percent);
        },
      });

      onProgress?.(i, file.name, "success", 100);
      results.push({
        filename: file.name,
        status: "success",
        data: response.data,
      });
    } catch (error) {
      onProgress?.(i, file.name, "error", 0);
      results.push({
        filename: file.name,
        status: "error",
        error: error.response?.data?.detail || error.message,
      });
    }
  }

  return results;
};

/**
 * Get list of all documents
 * @returns {Promise} - Array of document metadata
 */
export const getDocuments = async () => {
  const response = await api.get("/api/docs");
  // Backend returns array directly
  return Array.isArray(response.data) ? response.data : [];
};

/**
 * Get available document categories
 * @returns {Promise} - Categories with counts
 */
export const getDocumentCategories = async () => {
  const response = await api.get("/api/docs/categories/list");
  return response.data?.categories || [];
};

/**
 * Update document metadata (category, tags)
 * @param {string} docId - Document UUID
 * @param {Object} updates - { category?: string, tags?: string[] }
 * @returns {Promise} - Updated document
 */
export const updateDocument = async (docId, updates) => {
  const response = await api.patch(`/api/docs/${docId}`, updates);
  return response.data;
};

/**
 * Get specific document by ID
 * @param {string} docId - Document UUID
 * @returns {Promise} - Document metadata
 */
export const getDocument = async (docId) => {
  const response = await api.get(`/api/docs/${docId}`);
  return response.data;
};

/**
 * Get document content (full text) by ID
 * @param {string} docId - Document UUID
 * @returns {Promise} - Document content and metadata
 */
export const getDocumentContent = async (docId) => {
  const response = await api.get(`/api/docs/${docId}/content`);
  return response.data;
};

/**
 * Delete a document by ID
 * @param {string} docId - Document UUID
 * @returns {Promise} - Delete confirmation
 */
export const deleteDocument = async (docId) => {
  const response = await api.delete(`/api/docs/${docId}`);
  return response.data;
};

/**
 * Bulk delete multiple documents
 * @param {string[]} docIds - Array of document UUIDs
 * @returns {Promise} - Bulk delete result with deleted/failed counts
 */
export const bulkDeleteDocuments = async (docIds) => {
  const response = await api.post("/api/docs/bulk-delete", docIds);
  return response.data;
};

// ============================================================================
// Chat API
// ============================================================================

/**
 * Send a chat question and get RAG-based answer
 * @param {Object} chatRequest - Chat request payload
 * @param {string} chatRequest.user_id - User/session identifier
 * @param {string} chatRequest.provider - LLM provider (ollama/openai/anthropic)
 * @param {string} chatRequest.question - User's question
 * @param {string[]} [chatRequest.doc_ids] - Optional document IDs to filter
 * @param {number} [chatRequest.top_k=5] - Number of chunks to retrieve
 * @param {string} [chatRequest.model] - Optional specific model name
 * @returns {Promise} - Chat response with answer and citations
 */
export const sendChatMessage = async (chatRequest) => {
  const response = await api.post("/api/chat", chatRequest);
  return response.data;
};

/**
 * Stream a chat response using Server-Sent Events
 * @param {Object} chatRequest - Chat request payload
 * @param {Function} onToken - Callback for each token received
 * @param {Function} onCitations - Callback for citations data
 * @param {Function} onDone - Callback when streaming is complete
 * @param {Function} onError - Callback for errors
 * @returns {Function} - Cleanup function to abort the stream
 */
export const streamChatMessage = (
  chatRequest,
  { onToken, onCitations, onDone, onError },
) => {
  const controller = new AbortController();

  const fetchStream = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(chatRequest),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Append decoded chunk to buffer
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        // Process complete lines (SSE events end with double newline)
        const lines = buffer.split("\n\n");

        // Keep the last incomplete chunk in buffer
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data: ")) {
            try {
              const event = JSON.parse(trimmed.slice(6));

              switch (event.type) {
                case "token":
                  onToken?.(event.data);
                  break;
                case "citations":
                  onCitations?.(event.data);
                  break;
                case "done":
                  onDone?.(event.data);
                  break;
                case "error":
                  onError?.(new Error(event.data));
                  break;
              }
            } catch (e) {
              // Skip malformed JSON
            }
          }
        }
      }

      // Process any remaining buffer
      if (buffer.trim().startsWith("data: ")) {
        try {
          const event = JSON.parse(buffer.trim().slice(6));
          if (event.type === "done") onDone?.(event.data);
        } catch (e) {
          // Ignore
        }
      }
    } catch (error) {
      if (error.name !== "AbortError") {
        onError?.(error);
      }
    }
  };

  fetchStream();

  // Return cleanup function
  return () => controller.abort();
};

/**
 * Get chat history for a user
 * @param {string} userId - User identifier
 * @param {number} [limit=50] - Max number of entries to return
 * @returns {Promise} - Array of chat history entries
 */
export const getChatHistory = async (userId, limit = 50) => {
  const response = await api.get(`/api/chat/history/${userId}`, {
    params: { limit },
  });
  return response.data;
};

/**
 * Clear chat history for a user
 * @param {string} userId - User identifier
 * @returns {Promise} - Delete confirmation
 */
export const clearChatHistory = async (userId) => {
  const response = await api.delete(`/api/chat/history/${userId}`);
  return response.data;
};

/**
 * Export chat history for a user
 * @param {string} userId - User identifier
 * @param {string} format - Export format ('json' or 'markdown')
 */
export const exportChatHistory = async (userId, format = "json") => {
  try {
    const response = await api.get(`/api/chat/history/${userId}/export`, {
      params: { format },
      responseType: "blob",
    });

    // Check if response is actually a blob
    if (!(response.data instanceof Blob)) {
      throw new Error("Invalid response format");
    }

    // Check if it's an error response (JSON instead of the expected format)
    if (response.data.type === "application/json") {
      const text = await response.data.text();
      const error = JSON.parse(text);
      throw new Error(error.detail || "Failed to export chat history");
    }

    // Create download link
    const extension = format === "markdown" ? "md" : "json";
    const blob = new Blob([response.data], {
      type: format === "markdown" ? "text/markdown" : "application/json",
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `chat_history_${userId}_${new Date().toISOString().split("T")[0]}.${extension}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Export chat history error:", error);
    throw error;
  }
};

// ============================================================================
// Health Check
// ============================================================================

/**
 * Check API health status
 * @returns {Promise} - Health status
 */
export const healthCheck = async () => {
  const response = await api.get("/health");
  return response.data;
};

// ============================================================================
// Image API (Multimodal)
// ============================================================================

/**
 * Upload an image file
 * @param {File} file - Image file to upload
 * @param {string} [description] - Optional description
 * @param {boolean} [generateDescription=true] - Auto-generate description using vision model
 * @returns {Promise} - Upload response with image_id
 */
export const uploadImage = async (
  file,
  description = "",
  generateDescription = true,
) => {
  const formData = new FormData();
  formData.append("file", file);
  if (description) {
    formData.append("description", description);
  }
  // Convert boolean to string "true" or "false" for FastAPI Form field
  formData.append("generate_description", generateDescription.toString());
  // Use ollama for free local vision model (LLaVA)
  formData.append("vision_provider", "ollama");

  const response = await api.post("/api/images/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};

/**
 * Get list of all uploaded images
 * @param {number} [skip=0] - Number of items to skip
 * @param {number} [limit=50] - Max number of items to return
 * @returns {Promise} - Array of image metadata
 */
export const getImages = async (skip = 0, limit = 50) => {
  const response = await api.get("/api/images/", {
    params: { skip, limit },
  });
  // Ensure we always return an array
  const data = response.data;
  if (Array.isArray(data)) return data;
  if (data?.images) return data.images;
  return [];
};

/**
 * Get specific image by ID
 * @param {string} imageId - Image UUID
 * @returns {Promise} - Image metadata
 */
export const getImage = async (imageId) => {
  const response = await api.get(`/api/images/${imageId}`);
  return response.data;
};

/**
 * Delete an image by ID
 * @param {string} imageId - Image UUID
 * @returns {Promise} - Delete confirmation
 */
export const deleteImage = async (imageId) => {
  const response = await api.delete(`/api/images/${imageId}`);
  return response.data;
};

/**
 * Search images using text query (multimodal search)
 * @param {Object} searchRequest - Search request payload
 * @param {string} searchRequest.query - Text query for semantic image search
 * @param {number} [searchRequest.top_k=5] - Number of results to return
 * @returns {Promise} - Array of matching images with scores
 */
export const searchImages = async (searchRequest) => {
  const response = await api.post("/api/images/search", searchRequest);
  return response.data;
};

/**
 * Get supported image formats
 * @returns {Promise} - List of supported formats
 */
export const getSupportedImageFormats = async () => {
  const response = await api.get("/api/images/formats/supported");
  return response.data;
};

/**
 * Stream a multimodal chat response (with image context)
 * @param {Object} chatRequest - Chat request payload with optional images
 * @param {string} chatRequest.user_id - User/session identifier
 * @param {string} chatRequest.provider - LLM provider (openai/anthropic for vision)
 * @param {string} chatRequest.question - User's question
 * @param {string[]} [chatRequest.image_ids] - Optional image IDs to include in context
 * @param {Function} onToken - Callback for each token received
 * @param {Function} onCitations - Callback for citations data
 * @param {Function} onDone - Callback when streaming is complete
 * @param {Function} onError - Callback for errors
 * @returns {Function} - Cleanup function to abort the stream
 */
export const streamMultimodalChat = (
  chatRequest,
  { onToken, onCitations, onImages, onDone, onError },
) => {
  const controller = new AbortController();

  const fetchStream = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(chatRequest),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data: ")) {
            try {
              const event = JSON.parse(trimmed.slice(6));

              switch (event.type) {
                case "token":
                  onToken?.(event.data);
                  break;
                case "citations":
                  onCitations?.(event.data);
                  break;
                case "images":
                  onImages?.(event.data);
                  break;
                case "done":
                  onDone?.(event.data);
                  break;
                case "error":
                  onError?.(new Error(event.data));
                  break;
              }
            } catch (e) {
              // Skip malformed JSON
            }
          }
        }
      }
    } catch (error) {
      if (error.name !== "AbortError") {
        onError?.(error);
      }
    }
  };

  fetchStream();

  return () => controller.abort();
};

// ============================================================================
// Compliance API
// ============================================================================

/**
 * Perform a compliance check combining documents and images
 * @param {Object} request - Compliance check request
 * @param {string} request.user_id - User identifier
 * @param {string} request.query - Compliance question
 * @param {string} request.provider - LLM provider
 * @param {string[]} [request.doc_ids] - Document IDs to check against
 * @param {string[]} [request.image_ids] - Image IDs to analyze
 * @returns {Promise} - Compliance report
 */
export const checkCompliance = async (request) => {
  const response = await api.post("/api/compliance/check", request);
  return response.data;
};

/**
 * Stream a compliance check with progress updates
 * @param {Object} request - Compliance check request
 * @param {Object} callbacks - Event callbacks
 * @returns {Function} - Cleanup function to abort
 */
export const streamComplianceCheck = (
  request,
  { onStatus, onCitations, onToken, onReport, onDone, onError },
) => {
  const controller = new AbortController();

  const fetchStream = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/compliance/check/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(request),
          signal: controller.signal,
        },
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data: ")) {
            try {
              const event = JSON.parse(trimmed.slice(6));

              switch (event.type) {
                case "status":
                  onStatus?.(event.data);
                  break;
                case "citations":
                  onCitations?.(event.data);
                  break;
                case "token":
                  onToken?.(event.data);
                  break;
                case "report":
                  onReport?.(event.data);
                  break;
                case "done":
                  onDone?.();
                  break;
                case "error":
                  onError?.(new Error(event.data));
                  break;
              }
            } catch (e) {
              // Skip malformed JSON
            }
          }
        }
      }
    } catch (error) {
      if (error.name !== "AbortError") {
        onError?.(error);
      }
    }
  };

  fetchStream();

  return () => controller.abort();
};

/**
 * Get compliance check history for a user
 * @param {string} userId - User identifier
 * @param {number} [limit=20] - Max results
 * @returns {Promise} - Array of compliance history items
 */
export const getComplianceHistory = async (userId, limit = 20) => {
  const response = await api.get(`/api/compliance/history/${userId}`, {
    params: { limit },
  });
  return response.data;
};

/**
 * Get a specific compliance report
 * @param {string} reportId - Report ID
 * @param {string} [format="json"] - Output format (json or markdown)
 * @returns {Promise} - Compliance report
 */
export const getComplianceReport = async (reportId, format = "json") => {
  const response = await api.get(`/api/compliance/report/${reportId}`, {
    params: { format },
  });
  return response.data;
};

/**
 * Delete a compliance report
 * @param {string} reportId - Report ID
 * @returns {Promise} - Delete confirmation
 */
export const deleteComplianceReport = async (reportId) => {
  const response = await api.delete(`/api/compliance/report/${reportId}`);
  return response.data;
};

/**
 * Get available compliance status options
 * @returns {Promise} - Status and severity options
 */
export const getComplianceStatusOptions = async () => {
  const response = await api.get("/api/compliance/status-options");
  return response.data;
};

/**
 * Check baggage damage refund eligibility using vision model
 * @param {File} imageFile - Image file of damaged suitcase
 * @param {number|null} reportedWithinHours - Hours since baggage pickup/delivery
 * @param {string} [provider="openai"] - Vision provider (openai, anthropic, ollama)
 * @returns {Promise} - Eligibility decision with damage assessment
 */
export const checkBaggageDamageEligibility = async (
  imageFile,
  reportedWithinHours = null,
  provider = "openai",
) => {
  const formData = new FormData();
  formData.append("file", imageFile); // Backend expects "file" not "image_file"
  if (reportedWithinHours !== null) {
    formData.append("reported_within_hours", String(reportedWithinHours));
  }
  formData.append("vision_provider", provider); // Backend expects "vision_provider"

  console.log("Sending baggage damage check request:", {
    fileName: imageFile.name,
    fileSize: imageFile.size,
    provider,
    reportedWithinHours,
  });

  const response = await api.post(
    "/api/compliance/baggage/damage-refund/check",
    formData,
    {
      headers: {
        // Let axios set the Content-Type with boundary automatically
        "Content-Type": undefined,
      },
    },
  );

  console.log("Baggage damage check response:", response.data);
  return response.data;
};

export default api;
