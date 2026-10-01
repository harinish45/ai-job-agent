import asyncio
from playwright.async_api import async_playwright, Page, expect

async def test_dropdown_accessibility(page: Page):
    # Go to app
    await page.goto("http://localhost:3000")

    # Bypass auth by mocking local storage
    await page.evaluate("localStorage.setItem('token', 'dummy');")

    # Mock backend applications response so it doesn't hang
    await page.route("**/api/applications*", lambda route: route.fulfill(
        status=200,
        json={
            "applications": [
                {
                    "id": 1,
                    "job_title": "AI Engineer",
                    "company": "Tech Corp",
                    "status": "applied",
                    "applied_at": "2023-10-27T10:00:00Z",
                    "auto_applied": False,
                    "next_follow_up": None,
                    "source_platform": "linkedin"
                }
            ]
        }
    ))

    # Reload to apply token and route
    await page.goto("http://localhost:3000")

    # Click on Applications tab
    applications_tab = page.get_by_role("button", name="Applications")
    await applications_tab.click()

    # Wait for the mocked application to load
    await expect(page.get_by_text("Tech Corp")).to_be_visible()

    # Focus the Update button
    update_button = page.get_by_role("button", name="Update")
    await update_button.focus()

    # Take screenshot while button is focused (menu should be visible)
    await page.screenshot(path="/app/verification/dropdown_focus.png")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await test_dropdown_accessibility(page)
            print("Verification complete.")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
