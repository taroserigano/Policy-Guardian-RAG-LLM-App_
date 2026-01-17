/**
 * Comprehensive tests for API client
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import api from "../api/client";

describe("API Client", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  describe("Health Check", () => {
    it("should fetch health status", async () => {
      const mockResponse = { status: "healthy" };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await api.health();
      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8001/health"
      );
    });

    it("should handle health check errors", async () => {
      global.fetch.mockRejectedValueOnce(new Error("Network error"));

      await expect(api.health()).rejects.toThrow("Network error");
    });
  });

  describe("Document Management", () => {
    it("should fetch documents list", async () => {
      const mockDocs = { documents: [{ id: "1", filename: "test.txt" }] };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockDocs,
      });

      const result = await api.listDocuments();
      expect(result).toEqual(mockDocs);
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8001/api/docs"
      );
    });

    it("should upload document", async () => {
      const file = new File(["content"], "test.txt", { type: "text/plain" });
      const mockResponse = { success: true, id: "doc-123" };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await api.uploadDocument(file);
      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8001/api/docs/upload",
        expect.objectContaining({
          method: "POST",
          body: expect.any(FormData),
        })
      );
    });

    it("should handle upload errors", async () => {
      const file = new File(["content"], "test.txt", { type: "text/plain" });
      
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ error: "Invalid file" }),
      });

      await expect(api.uploadDocument(file)).rejects.toThrow();
    });
  });

  describe("Chat", () => {
    it("should send chat message", async () => {
      const mockResponse = {
        answer: "Test answer",
        citations: [],
        model: { provider: "ollama", name: "llama3.1" },
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await api.chat({
        question: "Test question",
        provider: "ollama",
        user_id: "test-user",
      });

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8001/api/chat",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: expect.stringContaining("Test question"),
        })
      );
    });

    it("should include model in request", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ answer: "test", citations: [] }),
      });

      await api.chat({
        question: "Test",
        provider: "openai",
        model: "gpt-4",
        user_id: "test-user",
      });

      const callArgs = global.fetch.mock.calls[0][1];
      const body = JSON.parse(callArgs.body);
      expect(body.model).toBe("gpt-4");
    });

    it("should handle chat errors", async () => {
      global.fetch.mockRejectedValueOnce(new Error("Server error"));

      await expect(
        api.chat({
          question: "Test",
          provider: "ollama",
          user_id: "test-user",
        })
      ).rejects.toThrow("Server error");
    });
  });

  describe("Error Handling", () => {
    it("should handle 404 errors", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ error: "Not found" }),
      });

      await expect(api.listDocuments()).rejects.toThrow();
    });

    it("should handle 500 errors", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: "Server error" }),
      });

      await expect(api.health()).rejects.toThrow();
    });

    it("should handle network timeout", async () => {
      global.fetch.mockImplementationOnce(
        () =>
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error("Timeout")), 100)
          )
      );

      await expect(api.health()).rejects.toThrow("Timeout");
    });
  });
});
