import asyncio
import logging
from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)

async def join_google_meet(page: Page, meeting_url: str, bot_name: str = "HJAI Notetaker"):
    logger.info(f"Navigating to {meeting_url}")
    await page.goto(meeting_url)

    # Google Meet specific join logic
    # Wait for the name input field (when joining without being signed in)
    try:
        name_input = page.locator("input[aria-label='Your name']")
        await name_input.wait_for(state="visible", timeout=15000)
        await name_input.fill(bot_name)
        
        # Click the "Ask to join" button
        join_button = page.locator("button:has-text('Ask to join')")
        if await join_button.count() == 0:
            join_button = page.locator("button:has-text('Join now')")
        
        await join_button.click()
        logger.info("Requested to join the meeting.")
        
        # Wait until we are inside the meeting (the meeting interface appears)
        await page.wait_for_selector("div[data-meeting-title]", timeout=60000)
        logger.info("Successfully joined the meeting.")
        
    except Exception as e:
        logger.error(f"Failed to join Google Meet: {e}")
        raise e

async def launch_bot(meeting_url: str, meeting_type: str = "google_meet"):
    async with async_playwright() as p:
        # Launch Chromium with specific flags to fake media devices and disable sounds
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--disable-notifications",
                "--mute-audio", # We don't want the bot to output audio to the host, we want pulse audio to capture it
                "--autoplay-policy=no-user-gesture-required"
            ]
        )
        
        context = await browser.new_context()
        
        # Grant permissions for microphone and camera automatically
        await context.grant_permissions(['microphone', 'camera'])
        
        page = await context.new_page()
        
        try:
            if meeting_type == "google_meet":
                await join_google_meet(page, meeting_url)
            else:
                logger.warning(f"Meeting type {meeting_type} is not fully supported yet.")
                await page.goto(meeting_url)
                
            # Keep the browser open until the meeting ends
            # In a real scenario, we'd wait for a "meeting ended" event or signal
            await asyncio.sleep(3600) # Wait up to 1 hour
            
        finally:
            await browser.close()
            logger.info("Left the meeting and closed browser.")

if __name__ == "__main__":
    # Test script locally
    logging.basicConfig(level=logging.INFO)
    test_url = "https://meet.google.com/xxx-xxxx-xxx"
    # asyncio.run(launch_bot(test_url))
