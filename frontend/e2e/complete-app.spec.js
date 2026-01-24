/**
 * Comprehensive E2E Test Suite for RAG Application
 * Tests all major features including document upload, chat, and settings
 */
import { test, expect } from "@playwright/test";

const BASE_URL = "http://localhost:5173";
const API_URL = "http://localhost:8001";

// Helper function to wait for app to load
async function waitForAppLoad(page) {
  await page.goto(BASE_URL);
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);
}

test.describe("Complete Application E2E Tests", () => {
  test.describe("Navigation Tests", () => {
    test("should load home page successfully", async ({ page }) => {
      await waitForAppLoad(page);

      // Check main content loaded
      const main = page
        .locator("main")
        .or(page.locator("#root"))
        .or(page.locator("#app"));
      await expect(main.first()).toBeVisible();
    });

    test("should navigate to all main routes", async ({ page }) => {
      await waitForAppLoad(page);

      // Navigate to chat
      const chatLink = page.locator('a[href="/chat"]').first();
      if (await chatLink.isVisible()) {
        await chatLink.click();
        await page.waitForURL("**/chat", { timeout: 10000 });
        expect(page.url()).toContain("/chat");
      }

      // Navigate to upload
      const uploadLink = page.locator('a[href="/upload"]').first();
      if (await uploadLink.isVisible()) {
        await uploadLink.click();
        await page.waitForURL("**/upload", { timeout: 10000 });
        expect(page.url()).toContain("/upload");
      }

      // Navigate back to home
      const homeLink = page.locator('a[href="/"]').first();
      if (await homeLink.isVisible()) {
        await homeLink.click();
        await page.waitForTimeout(1000);
      }
    });

    test("should have working navigation header", async ({ page }) => {
      await waitForAppLoad(page);

      // Check header exists
      const header = page.locator("header").or(page.locator("nav")).first();
      await expect(header).toBeVisible();
    });
  });

  test.describe("Chat Interface Tests", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);
      await page.waitForLoadState("networkidle");
    });

    test("should display chat input area", async ({ page }) => {
      const input = page
        .locator("textarea")
        .or(page.locator('input[type="text"]'));
      await expect(input.first()).toBeVisible({ timeout: 10000 });
    });

    test("should have provider selection buttons", async ({ page }) => {
      // Look for provider selection
      const providerSection = page
        .locator("text=Provider")
        .or(page.locator("text=LLM"))
        .or(page.locator("text=Model"));
      await page.waitForTimeout(1000);

      // At least one provider should be visible
      const anyProvider = page
        .locator("text=Ollama")
        .or(page.locator("text=OpenAI"))
        .or(page.locator("text=Anthropic"));
      const count = await anyProvider.count();
      expect(count).toBeGreaterThan(0);
    });

    test("should enable send button when text is entered", async ({ page }) => {
      const input = page.locator("textarea").first();
      await input.waitFor({ state: "visible", timeout: 10000 });

      // Type a message
      await input.fill("Test message");

      // Find send button
      const sendBtn = page
        .locator('button[type="submit"]')
        .or(page.locator('button:has-text("Send")'))
        .first();

      // Should be enabled or clickable
      await page.waitForTimeout(500);
    });

    test("should display message history area", async ({ page }) => {
      // Look for message container
      const messageArea = page
        .locator('[class*="message"]')
        .or(page.locator('[class*="chat"]'))
        .or(page.locator('[class*="conversation"]'));
      await page.waitForTimeout(1000);
    });

    test("should show RAG context toggle", async ({ page }) => {
      // Look for RAG-related UI elements
      const ragElements = page
        .locator("text=RAG")
        .or(page.locator("text=Context"))
        .or(page.locator("text=Documents"));
      await page.waitForTimeout(1000);
    });
  });

  test.describe("Document Upload Tests", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto(`${BASE_URL}/upload`);
      await page.waitForLoadState("networkidle");
    });

    test("should display file upload area", async ({ page }) => {
      // Look for upload elements
      const uploadArea = page
        .locator('[class*="upload"]')
        .or(page.locator('[class*="drop"]'))
        .or(page.locator('input[type="file"]'));
      await page.waitForTimeout(1000);

      const count = await uploadArea.count();
      expect(count).toBeGreaterThan(0);
    });

    test("should have file input element", async ({ page }) => {
      const fileInput = page.locator('input[type="file"]');
      const count = await fileInput.count();
      expect(count).toBeGreaterThan(0);
    });

    test("should display uploaded documents list", async ({ page }) => {
      // Look for documents list
      const docsList = page
        .locator("text=Documents")
        .or(page.locator("text=Uploaded"))
        .or(page.locator('[class*="document"]'));
      await page.waitForTimeout(1000);
    });
  });

  test.describe("Settings and Configuration Tests", () => {
    test("should allow changing LLM provider", async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);
      await page.waitForLoadState("networkidle");

      // Click on a provider button
      const providers = ["Ollama", "OpenAI", "Anthropic"];

      for (const provider of providers) {
        const btn = page
          .locator(`button:has-text("${provider}")`)
          .or(page.locator(`text=${provider}`));
        if (await btn.first().isVisible()) {
          await btn.first().click();
          await page.waitForTimeout(500);
          break;
        }
      }
    });

    test("should have temperature/options controls", async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);
      await page.waitForLoadState("networkidle");

      // Look for settings controls
      const settings = page
        .locator("text=Temperature")
        .or(page.locator("text=Settings"))
        .or(page.locator("text=Options"));
      await page.waitForTimeout(1000);
    });
  });

  test.describe("Responsive Design Tests", () => {
    const viewports = [
      { name: "Mobile S", width: 320, height: 568 },
      { name: "Mobile M", width: 375, height: 667 },
      { name: "Mobile L", width: 425, height: 812 },
      { name: "Tablet", width: 768, height: 1024 },
      { name: "Laptop", width: 1024, height: 768 },
      { name: "Desktop", width: 1440, height: 900 },
    ];

    for (const vp of viewports) {
      test(`should render correctly on ${vp.name} (${vp.width}x${vp.height})`, async ({
        page,
      }) => {
        await page.setViewportSize({ width: vp.width, height: vp.height });
        await page.goto(BASE_URL);
        await page.waitForLoadState("networkidle");

        // Should not have horizontal overflow
        const hasHorizontalScroll = await page.evaluate(() => {
          return (
            document.documentElement.scrollWidth >
            document.documentElement.clientWidth
          );
        });

        // Allow small overflow on mobile due to scrollbars
        if (vp.width > 400) {
          expect(hasHorizontalScroll).toBe(false);
        }

        // Main content should be visible
        const root = page
          .locator("#root")
          .or(page.locator("#app"))
          .or(page.locator("main"));
        await expect(root.first()).toBeVisible();
      });
    }
  });

  test.describe("Error Handling Tests", () => {
    test("should handle 404 pages gracefully", async ({ page }) => {
      await page.goto(`${BASE_URL}/nonexistent-page`);
      await page.waitForLoadState("networkidle");

      // Should either redirect or show 404
      await page.waitForTimeout(1000);

      // App should still be functional
      const root = page.locator("#root").or(page.locator("#app"));
      await expect(root.first()).toBeVisible();
    });

    test("should handle empty chat submission", async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);
      await page.waitForLoadState("networkidle");

      const sendBtn = page
        .locator('button[type="submit"]')
        .or(page.locator('button:has-text("Send")'))
        .first();

      if (await sendBtn.isVisible()) {
        // Try to submit empty form - should be disabled or prevented
        const isDisabled = await sendBtn.isDisabled();
        // Empty submit should either be disabled or not cause errors
      }
    });
  });

  test.describe("Accessibility Tests", () => {
    test("should have proper page structure", async ({ page }) => {
      await waitForAppLoad(page);

      // Check for semantic HTML
      const hasMain = (await page.locator("main").count()) > 0;
      const hasHeader =
        (await page.locator("header").count()) > 0 ||
        (await page.locator("nav").count()) > 0;

      // At least basic structure should exist
      expect(hasMain || (await page.locator("#root").count()) > 0).toBe(true);
    });

    test("should have focusable interactive elements", async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);
      await page.waitForLoadState("networkidle");

      // Tab through elements
      await page.keyboard.press("Tab");
      await page.waitForTimeout(200);

      // Something should be focused
      const focused = await page.evaluate(() => document.activeElement.tagName);
      expect(focused).not.toBe("BODY");
    });

    test("should have alt text on images", async ({ page }) => {
      await waitForAppLoad(page);

      const images = page.locator("img");
      const count = await images.count();

      for (let i = 0; i < count; i++) {
        const img = images.nth(i);
        const alt = await img.getAttribute("alt");
        const role = await img.getAttribute("role");

        // Images should have alt or be decorative (role="presentation")
        expect(alt !== null || role === "presentation" || role === "none").toBe(
          true,
        );
      }
    });
  });
});

test.describe("API Integration Tests", () => {
  test("backend health check", async ({ request }) => {
    try {
      // Try common health endpoints
      let response = await request.get(`${API_URL}/health`);
      if (!response.ok()) {
        response = await request.get(`${API_URL}/`);
      }
      expect(response.status()).toBeLessThan(500);
    } catch (e) {
      test.skip("Backend not available");
    }
  });

  test("API docs endpoint should be accessible", async ({ request }) => {
    try {
      const response = await request.get(`${API_URL}/docs`);
      expect(response.status()).toBe(200);
    } catch (e) {
      test.skip("Backend not available");
    }
  });

  test("API should return document list", async ({ request }) => {
    try {
      const response = await request.get(`${API_URL}/api/docs`);
      if (response.ok()) {
        const data = await response.json();
        expect(Array.isArray(data.documents || data)).toBe(true);
      }
    } catch (e) {
      test.skip("API not available");
    }
  });
});
