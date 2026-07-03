import asyncio
from playwright.async_api import async_playwright

async def verify_focus():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # We need to mock the API calls so the frontend renders correctly without backend
        await page.route("**/api/dashboard/stats", lambda route: route.fulfill(status=200, json={"jobs": 0}))
        await page.route("**/api/jobs", lambda route: route.fulfill(status=200, json=[]))

        async def handle_applications(route):
            await route.fulfill(status=200, json={
                "applications": [
                    {
                        "id": 1,
                        "job_title": "AI Engineer",
                        "company": "Tech Corp",
                        "status": "new",
                        "applied_at": "2024-07-01",
                        "auto_applied": False,
                        "next_follow_up": "2024-07-10",
                        "source_platform": "linkedin"
                    }
                ],
                "total": 1,
                "pages": 1
            })

        await page.route("**/api/applications*", handle_applications)
        await page.route("**/api/profile", lambda route: route.fulfill(status=200, json={}))
        await page.route("**/api/auth/session", lambda route: route.fulfill(status=200, json={"user": "test"}))

        # Load the application tracker tab
        await page.goto("http://localhost:3000/login")

        # Bypass auth
        await page.evaluate("localStorage.setItem('token', 'dummy');")
        await page.goto("http://localhost:3000")

        # Click Applications tab
        await page.get_by_role("button", name="Applications").click()

        # wait a bit
        await page.wait_for_timeout(2000)

        # Focus the update button using Keyboard (Tab)
        # Note we use evaluate to avoid playwright getting stuck if it can't find it exactly as it expects
        await page.evaluate("""
            const buttons = document.querySelectorAll('button');
            for (const btn of buttons) {
                if (btn.textContent.includes('Update')) {
                    btn.focus();
                    break;
                }
            }
        """)

        # Wait for a brief moment to let the focus within styles apply and the dropdown to appear
        await page.wait_for_timeout(500)

        # Take a screenshot
        await page.screenshot(path="/app/verification/verification.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_focus())
