/**
 * Unit tests for API client functions
 * Tests named exports from the client module
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import axios from "axios";
import * as apiClient from "../api/client";

// Mock axios
vi.mock("axios", () => {
  const mockAxios = {
    create: vi.fn(() => mockAxios),
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  };
  return { default: mockAxios };
});

describe("API Client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Health Check", () => {
    it("should have API_BASE configured", () => {
      expect(apiClient.API_BASE).toBeDefined();
      expect(typeof apiClient.API_BASE).toBe("string");
    });
  });

  describe("Document Functions", () => {
    it("should export uploadDocument function", () => {
      expect(typeof apiClient.uploadDocument).toBe("function");
    });

    it("should export uploadDocumentsBatch function", () => {
      expect(typeof apiClient.uploadDocumentsBatch).toBe("function");
    });

    it("should export getDocuments function", () => {
      expect(typeof apiClient.getDocuments).toBe("function");
    });

    it("should export getDocument function", () => {
      expect(typeof apiClient.getDocument).toBe("function");
    });

    it("should export deleteDocument function", () => {
      expect(typeof apiClient.deleteDocument).toBe("function");
    });
  });

  describe("Chat Functions", () => {
    it("should export sendChatMessage function", () => {
      expect(typeof apiClient.sendChatMessage).toBe("function");
    });

    it("should export getChatHistory function", () => {
      expect(typeof apiClient.getChatHistory).toBe("function");
    });

    it("should export exportChatHistory function", () => {
      expect(typeof apiClient.exportChatHistory).toBe("function");
    });

    it("should export clearChatHistory function", () => {
      expect(typeof apiClient.clearChatHistory).toBe("function");
    });
  });

  describe("Health Functions", () => {
    it("should export healthCheck function", () => {
      expect(typeof apiClient.healthCheck).toBe("function");
    });
  });

  describe("Streaming Functions", () => {
    it("should export streamChatMessage function", () => {
      expect(typeof apiClient.streamChatMessage).toBe("function");
    });

    it("should export streamMultimodalChat function", () => {
      expect(typeof apiClient.streamMultimodalChat).toBe("function");
    });
  });

  describe("Image Functions", () => {
    it("should export uploadImage function", () => {
      expect(typeof apiClient.uploadImage).toBe("function");
    });

    it("should export getImages function", () => {
      expect(typeof apiClient.getImages).toBe("function");
    });

    it("should export deleteImage function", () => {
      expect(typeof apiClient.deleteImage).toBe("function");
    });

    it("should export searchImages function", () => {
      expect(typeof apiClient.searchImages).toBe("function");
    });
  });
});
