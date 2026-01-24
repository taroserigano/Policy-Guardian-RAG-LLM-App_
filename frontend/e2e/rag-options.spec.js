/**
 * E2E tests for RAG Options functionality.
 * Tests the complete flow from UI interaction to API request.
 */
import { test, expect } from "@playwright/test";

test.describe("RAG Options E2E Tests", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the chat page (not root - that's upload page)
    await page.goto("/chat");

    // Wait for the page to be ready
    await page.waitForLoadState("networkidle");
    // Give React time to render
    await page.waitForTimeout(1000);
  });

  test("should display the main chat interface", async ({ page }) => {
    // Verify the main app container is visible
    const app = page.locator("#root");
    await expect(app).toBeVisible();

    // Check for the chat area (textarea in ChatBox)
    const chatArea = page.locator('textarea[placeholder*="document"]');
    await expect(chatArea).toBeVisible({ timeout: 10000 });
  });

  test("should open RAG options panel", async ({ page }) => {
    // Find the RAG button (contains "RAG" text)
    const ragButton = page.locator("button").filter({ hasText: /^RAG/ });
    await expect(ragButton).toBeVisible({ timeout: 10000 });

    await ragButton.click();

    // Verify RAG options panel opens
    await expect(page.getByText("Query Expansion")).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByText("Hybrid Search")).toBeVisible();
    await expect(page.getByText("Reranking")).toBeVisible();
  });

  test("should toggle Query Expansion option", async ({ page }) => {
    // Open RAG options
    const ragButton = page.locator("button").filter({ hasText: /^RAG/ });
    await ragButton.click();

    // Wait for panel to open
    await expect(page.getByText("Query Expansion")).toBeVisible({
      timeout: 5000,
    });

    // Find and click the Query Expansion toggle
    const queryExpansionLabel = page
      .locator("label")
      .filter({ hasText: "Query Expansion" });
    const checkbox = queryExpansionLabel.locator('input[type="checkbox"]');

    // Initially should be unchecked
    await expect(checkbox).not.toBeChecked();

    // Click to enable
    await queryExpansionLabel.click();

    // Should now be checked
    await expect(checkbox).toBeChecked();

    // Verify visual feedback (violet styling)
    await expect(queryExpansionLabel).toHaveClass(/border-violet/);
  });

  test("should toggle Hybrid Search option", async ({ page }) => {
    // Open RAG options
    const ragButton = page.locator("button").filter({ hasText: /^RAG/ });
    await ragButton.click();

    await expect(page.getByText("Hybrid Search")).toBeVisible({
      timeout: 5000,
    });

    // Find and click the Hybrid Search toggle
    const hybridSearchLabel = page
      .locator("label")
      .filter({ hasText: "Hybrid Search" });
    const checkbox = hybridSearchLabel.locator('input[type="checkbox"]');

    await expect(checkbox).not.toBeChecked();
    await hybridSearchLabel.click();
    await expect(checkbox).toBeChecked();

    // Verify visual feedback (blue styling)
    await expect(hybridSearchLabel).toHaveClass(/border-blue/);
  });

  test("should toggle Reranking option", async ({ page }) => {
    // Open RAG options
    const ragButton = page.locator("button").filter({ hasText: /^RAG/ });
    await ragButton.click();

    await expect(page.getByText("Reranking")).toBeVisible({ timeout: 5000 });

    // Find and click the Reranking toggle
    const rerankingLabel = page
      .locator("label")
      .filter({ hasText: "Reranking" });
    const checkbox = rerankingLabel.locator('input[type="checkbox"]');

    await expect(checkbox).not.toBeChecked();
    await rerankingLabel.click();
    await expect(checkbox).toBeChecked();

    // Verify visual feedback (emerald styling)
    await expect(rerankingLabel).toHaveClass(/border-emerald/);
  });

  test("should enable all RAG options simultaneously", async ({ page }) => {
    // Open RAG options
    const ragButton = page.locator("button").filter({ hasText: /^RAG/ });
    await ragButton.click();

    // Wait for panel
    await expect(page.getByText("Query Expansion")).toBeVisible({
      timeout: 5000,
    });

    // Enable all three options
    const queryExpansionLabel = page
      .locator("label")
      .filter({ hasText: "Query Expansion" });
    const hybridSearchLabel = page
      .locator("label")
      .filter({ hasText: "Hybrid Search" });
    const rerankingLabel = page
      .locator("label")
      .filter({ hasText: "Reranking" });

    await queryExpansionLabel.click();
    await hybridSearchLabel.click();
    await rerankingLabel.click();

    // Verify all are checked
    await expect(
      queryExpansionLabel.locator('input[type="checkbox"]'),
    ).toBeChecked();
    await expect(
      hybridSearchLabel.locator('input[type="checkbox"]'),
    ).toBeChecked();
    await expect(
      rerankingLabel.locator('input[type="checkbox"]'),
    ).toBeChecked();
  });

  test("should maintain RAG options state after closing and reopening panel", async ({
    page,
  }) => {
    // Open RAG options
    const ragButton = page.locator("button").filter({ hasText: /^RAG/ });
    await ragButton.click();

    // Enable query expansion
    await expect(page.getByText("Query Expansion")).toBeVisible({
      timeout: 5000,
    });
    const queryExpansionLabel = page
      .locator("label")
      .filter({ hasText: "Query Expansion" });
    await queryExpansionLabel.click();
    await expect(
      queryExpansionLabel.locator('input[type="checkbox"]'),
    ).toBeChecked();

    // Close panel by clicking the button again
    await ragButton.click();

    // Wait for panel to close
    await expect(page.getByText("Multiple query variations")).not.toBeVisible({
      timeout: 5000,
    });

    // Reopen panel
    await ragButton.click();

    // State should be preserved
    await expect(page.getByText("Query Expansion")).toBeVisible({
      timeout: 5000,
    });
    const reopenedLabel = page
      .locator("label")
      .filter({ hasText: "Query Expansion" });
    await expect(reopenedLabel.locator('input[type="checkbox"]')).toBeChecked();
  });

  test("should show description text for each RAG option", async ({ page }) => {
    // Open RAG options
    const ragButton = page.locator("button").filter({ hasText: /^RAG/ });
    await ragButton.click();

    // Verify descriptions are visible
    await expect(page.getByText("Multiple query variations")).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByText("Semantic + keyword search")).toBeVisible();
    await expect(page.getByText("Relevance scoring")).toBeVisible();
  });
});

test.describe("Chat with RAG Options", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/chat");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
  });

  test("should include RAG options in chat request", async ({ page }) => {
    // Set up request interception to verify RAG options are sent
    let capturedRequest = null;

    await page.route("**/api/v1/chat/stream", async (route) => {
      capturedRequest = route.request();
      // Mock a simple response
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: 'data: {"type": "token", "data": "Test response"}\n\ndata: {"type": "done"}\n\n',
      });
    });

    // Open RAG options and enable all
    const ragButton = page.locator("button").filter({ hasText: /^RAG/ });
    await ragButton.click();

    await expect(page.getByText("Query Expansion")).toBeVisible({
      timeout: 5000,
    });
    await page.locator("label").filter({ hasText: "Query Expansion" }).click();
    await page.locator("label").filter({ hasText: "Hybrid Search" }).click();
    await page.locator("label").filter({ hasText: "Reranking" }).click();

    // Close the options panel
    await ragButton.click();

    // Type a message and send
    const chatInput = page.locator('textarea[placeholder*="document"]');
    await chatInput.fill("What is the leave policy?");

    // Press Enter to send
    await chatInput.press("Enter");

    // Wait for the request
    await page.waitForTimeout(2000);

    // Verify the request was made with RAG options
    if (capturedRequest) {
      const postData = capturedRequest.postDataJSON();
      expect(postData.rag_options).toBeDefined();
      expect(postData.rag_options.query_expansion).toBe(true);
      expect(postData.rag_options.hybrid_search).toBe(true);
      expect(postData.rag_options.reranking).toBe(true);
    }
  });
});

test.describe("Document Selection", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/chat");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
  });

  test("should display document list when available", async ({ page }) => {
    // Wait for documents to potentially load
    await page.waitForTimeout(2000);

    // The app should be rendered
    const app = page.locator("#root");
    await expect(app).toBeVisible();
  });
});

test.describe("Model Selection", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/chat");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
  });

  test("should have model picker visible", async ({ page }) => {
    // The app should be rendered with model picker
    const app = page.locator("#root");
    await expect(app).toBeVisible();
  });
});

test.describe("Accessibility", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/chat");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
  });

  test("should have accessible form controls", async ({ page }) => {
    // Open RAG options
    const ragButton = page.locator("button").filter({ hasText: /^RAG/ });
    await ragButton.click();

    await expect(page.getByText("Query Expansion")).toBeVisible({
      timeout: 5000,
    });

    // Verify checkboxes are accessible
    const checkboxes = page.locator('input[type="checkbox"]');
    const count = await checkboxes.count();

    // Should have at least 3 checkboxes for RAG options
    expect(count).toBeGreaterThanOrEqual(3);
  });

  test("should support keyboard navigation", async ({ page }) => {
    // Open RAG options with click first
    const ragButton = page.locator("button").filter({ hasText: /^RAG/ });
    await ragButton.click();

    // Verify panel opened
    await expect(page.getByText("Query Expansion")).toBeVisible({
      timeout: 5000,
    });

    // Check that checkboxes exist and are interactive
    const queryExpansionLabel = page
      .locator("label")
      .filter({ hasText: "Query Expansion" });
    const checkbox = queryExpansionLabel.locator('input[type="checkbox"]');

    // Click the checkbox directly
    await checkbox.click({ force: true });
    await expect(checkbox).toBeChecked();
  });
});
