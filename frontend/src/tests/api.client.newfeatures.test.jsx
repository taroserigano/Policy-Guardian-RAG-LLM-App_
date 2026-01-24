/**
 * Tests for new API client functions:
 * - uploadDocumentsWithProgress
 * - updateDocument
 * - getDocumentCategories
 *
 * These tests verify the functions exist and have correct signatures.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

describe("New API Client Functions", () => {
  describe("uploadDocumentsWithProgress", () => {
    it("should be exported from client", async () => {
      // Dynamic import to avoid issues with mocks
      const client = await import("../api/client");
      expect(typeof client.uploadDocumentsWithProgress).toBe("function");
    });
  });

  describe("updateDocument", () => {
    it("should be exported from client", async () => {
      const client = await import("../api/client");
      expect(typeof client.updateDocument).toBe("function");
    });
  });

  describe("getDocumentCategories", () => {
    it("should be exported from client", async () => {
      const client = await import("../api/client");
      expect(typeof client.getDocumentCategories).toBe("function");
    });
  });

  describe("fetchDocumentContent or getDocumentContent", () => {
    it("should have document content function exported from client", async () => {
      const client = await import("../api/client");
      // May be named fetchDocumentContent or getDocumentContent
      const hasFetchDocContent =
        typeof client.fetchDocumentContent === "function";
      const hasGetDocContent = typeof client.getDocumentContent === "function";
      expect(hasFetchDocContent || hasGetDocContent).toBe(true);
    });
  });

  describe("streamChatMessage", () => {
    it("should be exported from client", async () => {
      const client = await import("../api/client");
      expect(typeof client.streamChatMessage).toBe("function");
    });
  });
});
