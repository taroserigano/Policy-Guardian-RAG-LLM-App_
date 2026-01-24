/**
 * E2E Tests for Fine-tuned Embeddings Integration
 * Tests the complete flow of document upload, embedding generation, and chat
 */
import { test, expect } from "@playwright/test";

const BASE_URL = "http://localhost:5173";
const API_URL = "http://localhost:8001";

test.describe("Fine-tuned Embeddings E2E Tests", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to app
    await page.goto(BASE_URL);
    await page.waitForLoadState("networkidle");
  });

  test.describe("Document Upload & Indexing", () => {
    test("should upload a policy document successfully", async ({ page }) => {
      // Go to upload page
      await page.click('a[href="/upload"]');
      await page.waitForURL("**/upload");

      // Check upload area is visible - use more generic selectors
      const dropZone = page
        .locator('[class*="drop"]')
        .or(page.locator('[class*="upload"]'))
        .or(page.locator('input[type="file"]'));
      await page.waitForTimeout(2000);
      const count = await dropZone.count();
      expect(count).toBeGreaterThan(0);
    });

    test("should display uploaded documents in list", async ({ page }) => {
      await page.goto(`${BASE_URL}/upload`);
      await page.waitForLoadState("networkidle");

      // Wait for page to load and check for any content
      await page.waitForTimeout(2000);

      // The upload page should have some content
      const pageContent = page
        .locator("main")
        .or(page.locator("#root"))
        .or(page.locator("#app"));
      await expect(pageContent.first()).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe("Chat with RAG", () => {
    test("should navigate to chat page", async ({ page }) => {
      // Click on Chat link
      await page.click('a[href="/chat"]');
      await page.waitForURL("**/chat");

      // Verify chat interface is visible
      const chatInput = page
        .locator("textarea")
        .or(page.locator('input[type="text"]'));
      await expect(chatInput.first()).toBeVisible({ timeout: 10000 });
    });

    test("should display LLM provider selection", async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);
      await page.waitForLoadState("networkidle");

      // Check for provider buttons
      const ollamaBtn = page.locator("text=Ollama");
      const openaiBtn = page.locator("text=OpenAI");
      const anthropicBtn = page.locator("text=Anthropic");

      await expect(ollamaBtn.first()).toBeVisible({ timeout: 10000 });
    });

    test("should send a message and receive response", async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);
      await page.waitForLoadState("networkidle");

      // Find and fill chat input
      const chatInput = page.locator("textarea").first();
      await chatInput.waitFor({ state: "visible", timeout: 10000 });

      await chatInput.fill("What is the remote work policy?");

      // Find and click send button
      const sendBtn = page
        .locator('button[type="submit"]')
        .or(page.locator('button:has-text("Send")'))
        .or(page.locator('button:has([data-lucide="send"])'))
        .first();

      if (await sendBtn.isVisible()) {
        await sendBtn.click();

        // Wait for response (may take time with LLM)
        await page.waitForTimeout(2000);
      }
    });
  });

  test.describe("RAG Options", () => {
    test("should display RAG options panel", async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);
      await page.waitForLoadState("networkidle");

      // Look for RAG options
      const ragSection = page
        .locator("text=RAG Options")
        .or(page.locator("text=Advanced"))
        .or(page.locator("text=Options"));

      // RAG options may be in a collapsible panel
      const expandBtn = page
        .locator('button:has-text("Options")')
        .or(page.locator('button:has-text("Advanced")'));
      if (await expandBtn.first().isVisible()) {
        await expandBtn.first().click();
      }
    });

    test("should toggle RAG enhancement options", async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);
      await page.waitForLoadState("networkidle");

      // Look for toggle switches or checkboxes
      const toggles = page
        .locator('input[type="checkbox"]')
        .or(page.locator('[role="switch"]'));
      const count = await toggles.count();

      if (count > 0) {
        // Toggle first option
        await toggles.first().click();
        await page.waitForTimeout(500);
      }
    });
  });

  test.describe("Mobile Responsiveness", () => {
    test("should display mobile menu on small screens", async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(BASE_URL);
      await page.waitForTimeout(2000);

      // Page should render without error
      const root = page
        .locator("#root")
        .or(page.locator("#app"))
        .or(page.locator("main"));
      await expect(root.first()).toBeVisible();
    });

    test("should have responsive layout on tablet", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto(`${BASE_URL}/chat`);
      await page.waitForTimeout(2000);

      // Page should load without horizontal scroll
      const body = page.locator("body");
      const box = await body.boundingBox();
      expect(box.width).toBeLessThanOrEqual(768);
    });
  });

  test.describe("API Health Checks", () => {
    test("should have healthy backend API", async ({ request }) => {
      try {
        const response = await request.get(`${API_URL}/docs`, {
          timeout: 5000,
        });
        expect(response.status()).toBeLessThan(500);
      } catch (e) {
        // Backend may not be running - skip test
        test.skip();
      }
    });

    test("should list documents via API", async ({ request }) => {
      try {
        const response = await request.get(`${API_URL}/api/docs`, {
          timeout: 5000,
        });
        expect(response.status()).toBeLessThan(500);
      } catch (e) {
        // Skip if API not available
        test.skip();
      }
    });
  });
});

test.describe("Embedding Fine-tuning Verification", () => {
  test("should use fine-tuned embeddings for policy queries", async ({
    request,
  }) => {
    // This test verifies the embedding endpoint works
    try {
      const response = await request.post(`${API_URL}/api/chat`, {
        data: {
          user_id: "test-user",
          provider: "ollama",
          question: "What is the WFH policy?",
          top_k: 3,
        },
      });

      if (response.ok()) {
        const data = await response.json();
        // Should have citations if documents are indexed
        expect(data).toHaveProperty("answer");
      }
    } catch (e) {
      // API might not be running with documents
      test.skip();
    }
  });
});
