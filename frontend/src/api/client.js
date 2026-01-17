/**
 * API client for backend communication.
 * Uses axios for HTTP requests.
 */
import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";

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
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error("API Error:", error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error("Network Error:", error.message);
    } else {
      // Something else happened
      console.error("Error:", error.message);
    }
    return Promise.reject(error);
  },
);

// ============================================================================
// Document API
// ============================================================================

/**
 * Upload a document file
 * @param {File} file - File object to upload
 * @returns {Promise} - Upload response with doc_id
 */
export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/api/docs/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};

/**
 * Get list of all documents
 * @returns {Promise} - Array of document metadata
 */
export const getDocuments = async () => {
  const response = await api.get("/api/docs");
  return response.data.documents || [];
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

export default api;
