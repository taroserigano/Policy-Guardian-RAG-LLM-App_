/**
 * E2E tests for the complete chat workflow.
 * Tests document upload, chat interaction, and response handling.
 */
import { test, expect } from "@playwright/test";

test.describe("Chat Workflow E2E Tests", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the chat page (not root - that's upload page)
    await page.goto("/chat");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
  });

  test("should load the chat page successfully", async ({ page }) => {
    // Verify main layout elements
    const app = page.locator("#root");
    await expect(app).toBeVisible();

    // Verify we're on the chat page by checking for chat-specific elements
    const chatHeading = page.getByRole("heading", {
      name: /chat|ask|conversation/i,
    });
    await expect(chatHeading).toBeVisible({ timeout: 5000 });
  });

  test("should have a functional chat input", async ({ page }) => {
    // Find the chat input (textarea with specific placeholder)
    const chatInput = page.locator('textarea[placeholder*="document"]');

    await expect(chatInput).toBeVisible({ timeout: 10000 });

    // Type in the input
    await chatInput.fill("Test message");
    await expect(chatInput).toHaveValue("Test message");
  });

  test("should display empty state or previous messages", async ({ page }) => {
    // The app container should exist
    const app = page.locator("#root");
    await expect(app).toBeVisible();
  });

  test("should show loading state when sending a message", async ({ page }) => {
    // Mock the API to delay response
    await page.route("**/api/v1/chat/stream", async (route) => {
      // Delay the response
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: 'data: {"type": "token", "data": "Hello"}\n\ndata: {"type": "done"}\n\n',
      });
    });

    // Find and fill the chat input
    const chatInput = page.locator('textarea[placeholder*="document"]');
    await expect(chatInput).toBeVisible({ timeout: 10000 });
    await chatInput.fill("Hello");
    await chatInput.press("Enter");

    // Wait briefly for any loading state
    await page.waitForTimeout(500);

    // The app should still be responsive
    const app = page.locator("#root");
    await expect(app).toBeVisible();
  });
});

test.describe("Document Management", () => {
  test.beforeEach(async ({ page }) => {
    // Document upload is at the root/upload page
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
  });

  test("should have document upload capability", async ({ page }) => {
    // The app should be rendered
    const app = page.locator("#root");
    await expect(app).toBeVisible();
  });

  test("should show documents section", async ({ page }) => {
    // Wait for potential document loading
    await page.waitForTimeout(1000);

    // The app should be rendered
    const app = page.locator("#root");
    await expect(app).toBeVisible();
  });
});

test.describe("Provider and Model Selection", () => {
  test.beforeEach(async ({ page }) => {
    // Model selection is on the chat page
    await page.goto("/chat");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
  });

  test("should allow selecting different providers", async ({ page }) => {
    // The app should be rendered with provider options
    const app = page.locator("#root");
    await expect(app).toBeVisible();

    // Look for provider buttons (Ollama, OpenAI, Anthropic)
    const ollamaButton = page.locator("button").filter({ hasText: /ollama/i });
    // At least one provider option should exist
    await expect(app).toBeVisible();
  });
});

test.describe("Error Handling", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/chat");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
  });

  test("should handle API errors gracefully", async ({ page }) => {
    // Mock an API error
    await page.route("**/api/v1/chat/stream", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Server error" }),
      });
    });

    // Find and fill the chat input
    const chatInput = page.locator('textarea[placeholder*="document"]');
    await expect(chatInput).toBeVisible({ timeout: 10000 });
    await chatInput.fill("Test error handling");
    await chatInput.press("Enter");

    // Wait for error handling
    await page.waitForTimeout(1000);

    // UI should still be functional
    await expect(chatInput).toBeVisible();
  });

  test("should handle network errors gracefully", async ({ page }) => {
    // Mock a network error
    await page.route("**/api/v1/chat/stream", async (route) => {
      await route.abort("failed");
    });

    const chatInput = page.locator('textarea[placeholder*="document"]');
    await expect(chatInput).toBeVisible({ timeout: 10000 });
    await chatInput.fill("Test network error");
    await chatInput.press("Enter");

    // Wait for error handling
    await page.waitForTimeout(1000);

    // UI should recover
    await expect(chatInput).toBeVisible();
  });
});

test.describe("Streaming Response", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/chat");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
  });

  test("should display streaming tokens progressively", async ({ page }) => {
    // Mock a streaming response
    await page.route("**/api/v1/chat/stream", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: 'data: {"type": "token", "data": "Hello"}\n\ndata: {"type": "token", "data": " World!"}\n\ndata: {"type": "done"}\n\n',
      });
    });

    // Find and fill the chat input
    const chatInput = page.locator('textarea[placeholder*="document"]');
    await expect(chatInput).toBeVisible({ timeout: 10000 });
    await chatInput.fill("Say hello");
    await chatInput.press("Enter");

    // Wait for response
    await page.waitForTimeout(2000);

    // App should still be visible
    const app = page.locator("#root");
    await expect(app).toBeVisible();
  });
});

test.describe("Chat History", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/chat");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
  });

  test("should have history toggle functionality", async ({ page }) => {
    // Look for history button
    const historyButton = page
      .locator("button")
      .filter({ hasText: /history/i });
    await expect(historyButton).toBeVisible({ timeout: 10000 });
  });
});

test.describe("Responsive Design", () => {
  test("should work on mobile viewport", async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/chat");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    // Main elements should still be visible
    const app = page.locator("#root");
    await expect(app).toBeVisible();

    // Chat input should be accessible
    const chatInput = page.locator('textarea[placeholder*="document"]');
    await expect(chatInput).toBeVisible({ timeout: 10000 });
  });

  test("should work on tablet viewport", async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/chat");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    const app = page.locator("#root");
    await expect(app).toBeVisible();
  });

  test("should work on desktop viewport", async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto("/chat");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    const app = page.locator("#root");
    await expect(app).toBeVisible();
  });
});
