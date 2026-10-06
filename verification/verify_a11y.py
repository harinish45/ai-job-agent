from playwright.async_api import async_playwright
import asyncio
import os
import glob

async def run_cuj(page):
    # Mock backend API response for applications
    await page.route("**/api/applications*", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"applications": [{"id": 1, "job_title": "Frontend Engineer", "company": "Tech Corp", "status": "new", "applied_at": "2023-10-27T10:00:00Z", "auto_applied": false, "next_follow_up": "", "source_platform": "linkedin"}]}'
    ))

    # Mock stats endpoint too, just in case
    await page.route("**/api/dashboard/stats*", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{}'
    ))

    # Mock login bypass
    await page.goto("http://localhost:3000/login")
    await page.evaluate("localStorage.setItem('token', 'dummy');")

    await page.goto("http://localhost:3000")
    await page.wait_for_timeout(1000)

    # Click the Applications tab
    await page.get_by_role("button", name="Applications").click()
    await page.wait_for_timeout(1000)

    # Find the Update button
    update_button = page.get_by_role("button", name="Update")

    # 1. Hover state
    await update_button.hover()
    await page.wait_for_timeout(1000)
    await page.screenshot(path="/app/verification/screenshots/hover_state.png")

    # Move mouse away to close dropdown
    await page.mouse.move(0, 0)
    await page.wait_for_timeout(500)

    # 2. Keyboard Focus state
    await update_button.focus()
    await page.wait_for_timeout(1000)
    await page.screenshot(path="/app/verification/screenshots/focus_state.png")

    # Keyboard navigate inside menu
    await page.keyboard.press("Tab")
    await page.wait_for_timeout(1000)
    await page.screenshot(path="/app/verification/screenshots/focus_menu_item.png")

    await page.wait_for_timeout(1000)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            record_video_dir="/app/verification/videos"
        )
        page = await context.new_page()
        try:
            await run_cuj(page)
        finally:
            await context.close()
            await browser.close()

            # Print the video path so we can capture it
            videos = glob.glob("/app/verification/videos/*.webm")
            if videos:
                print(f"VIDEO_PATH={videos[0]}")

if __name__ == "__main__":
    asyncio.run(main())
