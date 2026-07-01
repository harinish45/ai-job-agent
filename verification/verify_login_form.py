import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Go to the local Next.js frontend login page
            await page.goto("http://localhost:3000/login")

            # Wait for the login form to load
            await page.wait_for_selector('form')

            # Interact with the input to make sure it's functional
            # We are testing the accessibility attributes, which aren't necessarily visual,
            # but we can take a screenshot of the form and check its structure in the DOM.
            email_input = page.locator('input#email')
            password_input = page.locator('input#password')

            await email_input.fill('test@example.com')
            await password_input.fill('password123')

            # Take a screenshot to prove the form loads and inputs work
            await page.screenshot(path="/app/verification/login_form.png")
            print("Screenshot saved to /app/verification/login_form.png")

            # Verify the HTML structure
            html = await page.content()
            if 'id="email"' in html and 'htmlFor="email"' in html:
                print("Email input accessibility attributes verified.")
            if 'id="password"' in html and 'htmlFor="password"' in html:
                print("Password input accessibility attributes verified.")

        except Exception as e:
            print(f"Verification failed: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
