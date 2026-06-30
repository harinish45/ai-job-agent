import asyncio
from playwright.async_api import async_playwright

async def verify_joblist():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to a generic route to set localStorage
        await page.goto("http://localhost:3000/login", wait_until="networkidle")
        await page.evaluate("localStorage.setItem('token', 'dummy');")

        # Mock API response for jobs
        async def handle_jobs(route):
            await route.fulfill(
                status=200,
                content_type="application/json",
                body='{"jobs": [{"id": 1, "title": "AI Engineer", "company": "Tech Corp", "location": "Remote", "work_mode": "remote", "salary_min": 150000, "salary_max": 200000, "source_platform": "LinkedIn", "apply_url": "https://example.com/apply", "is_ai_role": true, "ai_role_category": "engineering", "posted_at": "2024-06-30", "match_score": 0.95, "is_strong_match": true}, {"id": 2, "title": "Data Scientist", "company": "Data Inc", "location": "New York", "work_mode": "hybrid", "salary_min": 130000, "salary_max": 180000, "source_platform": "Indeed", "apply_url": "https://example.com/apply2", "is_ai_role": false, "ai_role_category": "", "posted_at": "2024-06-29", "match_score": 0.75, "is_strong_match": false}]}'
            )

        # Mock API responses for user and dashboard requests
        async def handle_generic(route):
            await route.fulfill(
                status=200,
                content_type="application/json",
                body='{}'
            )

        await page.route("**/api/jobs*", handle_jobs)
        await page.route("**/api/dashboard*", handle_generic)
        await page.route("**/api/profile*", handle_generic)

        # Go to Dashboard and switch to Jobs tab
        await page.goto("http://localhost:3000/")

        jobs_tab = page.get_by_role("button", name="Jobs")
        await jobs_tab.click()

        # Wait for job list to render
        await page.wait_for_selector("text=AI-curated opportunities")

        # We need to simulate the loading state for one of the jobs. Let's mock the match API for the first job with a delay.
        async def handle_match(route):
            await asyncio.sleep(2)
            await route.fulfill(status=200, body='{}')

        await page.route("**/api/jobs/1/match*", handle_match)

        # Click "Analyze Match" on the first job
        analyze_buttons = page.get_by_role("button", name="Analyze Match")
        # Ensure there are two analyze buttons
        await analyze_buttons.nth(0).wait_for()

        await analyze_buttons.nth(0).click()

        # Wait a tiny bit for the loading state to apply
        await page.wait_for_timeout(100)

        # Take a screenshot to show the first is loading but the second is not
        await page.screenshot(path="/app/verification/joblist_scoped_loading.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_joblist())
