import asyncio
from playwright.async_api import async_playwright

async def verify_job_list():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Mock API responses
        await page.route("**/api/dashboard/stats", lambda route: route.fulfill(status=200, json={}))

        # Mock API response for jobs
        await page.route("**/api/jobs*", lambda route: route.fulfill(status=200, json={
            "jobs": [
                {
                    "id": 1,
                    "title": "AI Engineer",
                    "company": "Tech Corp",
                    "location": "Remote",
                    "work_mode": "remote",
                    "salary_min": 120000,
                    "salary_max": 180000,
                    "source_platform": "linkedin",
                    "apply_url": "https://example.com/apply",
                    "is_ai_role": True,
                    "ai_role_category": "engineering",
                    "posted_at": "2024-04-25",
                    "match_score": 0.95,
                    "is_strong_match": True
                },
                {
                    "id": 2,
                    "title": "Machine Learning Scientist",
                    "company": "Data Inc",
                    "location": "New York",
                    "work_mode": "hybrid",
                    "salary_min": 150000,
                    "salary_max": 200000,
                    "source_platform": "indeed",
                    "apply_url": "https://example.com/apply",
                    "is_ai_role": True,
                    "ai_role_category": "research",
                    "posted_at": "2024-04-24",
                    "match_score": 0.85,
                    "is_strong_match": True
                }
            ]
        }))

        # Mock analyze match API response, with a small delay
        async def handle_match_route(route):
            await asyncio.sleep(2)  # Delay to see the loading state
            await route.fulfill(status=200, json={"success": True})

        await page.route("**/api/jobs/1/match", handle_match_route)

        # Set token to bypass login
        await page.goto("http://localhost:3000")
        await page.evaluate("localStorage.setItem('token', 'dummy');")
        await page.goto("http://localhost:3000")

        # Navigate to Jobs tab
        await page.get_by_role("button", name="Jobs").click()

        # Wait for job list to load
        await page.wait_for_selector("text=AI Engineer")

        # Take a screenshot before click to debug
        await page.screenshot(path="/app/verification/before_click.png", full_page=True)

        # Click the "Analyze Match" button for the first job
        # Since ARIA labels on buttons are treated as the name in get_by_role
        analyze_button = page.get_by_role("button", name="Analyze match for AI Engineer at Tech Corp")
        await analyze_button.click()

        # Small wait for React Query to start mutation
        await asyncio.sleep(0.5)

        # Take screenshot while the first button is in "Analyzing..." state
        # but the second button should still say "Analyze Match"
        await page.screenshot(path="/app/verification/job_list_loading_state.png", full_page=True)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_job_list())
