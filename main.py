"""
Selenium based scraper to extract data from WhatsApp chats.
"""

import time
import csv
import os
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Setup and return configured Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    # Add user data directory to maintain session
    user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
    chrome_options.add_argument(f"user-data-dir={user_data_dir}")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        print("Chrome driver initialized successfully")
    except Exception as e:
        print(f"Error initializing Chrome driver: {e}")
        raise
    return driver

def output_to_csv(data, filename):
    """Output data to CSV file with proper encoding"""
    os.makedirs('scraped_data', exist_ok=True)
    with open(filename, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)

def locate_chat(driver, wait, name):
    """Find the chat with a given name in WhatsApp web and click on that chat"""
    try:
        print("Using keyboard shortcut to open search...")
        # Use Command/Ctrl + F to open search
        if os.name == 'posix':  # macOS
            actions = webdriver.ActionChains(driver)
            actions.key_down(Keys.COMMAND).send_keys('f').key_up(Keys.COMMAND).perform()
        else:  # Windows/Linux
            actions = webdriver.ActionChains(driver)
            actions.key_down(Keys.CONTROL).send_keys('f').key_up(Keys.CONTROL).perform()
        time.sleep(1)
        
        print(f"Typing group name: {name}")
        # Type the group name
        actions = webdriver.ActionChains(driver)
        actions.send_keys(name)
        actions.perform()
        time.sleep(2)
        
        print("Looking for chat in search results...")
        # Try to find the chat by its title
        try:
            chat = wait.until(EC.presence_of_element_located((By.XPATH, f"//span[contains(@title, '{name}')]")))
            print(f"Found chat: {chat.get_attribute('title')}")
            chat.click()
            print("Chat clicked")
            time.sleep(2)
            return True
        except:
            print("Chat not found by title, trying alternative method...")
            # Press Enter to select the first result
            actions = webdriver.ActionChains(driver)
            actions.send_keys(Keys.ENTER)
            actions.perform()
            time.sleep(2)
            return True
            
    except Exception as e:
        print(f"Error in locate_chat: {e}")
        return False

def scroll_to_top(driver):
    """Scrolls to the top of the chat currently open in the WhatsApp Web interface"""
    try:
        # Find the main chat container
        chat_container = driver.find_element(By.CSS_SELECTOR, 'div[role="application"]')
        print("Found chat container, starting scroll...")
        
        # Keep track of the number of messages before and after scrolling
        last_message_count = 0
        same_count = 0  # Counter for when message count doesn't change
        
        while True:
            # Get current message count
            messages = chat_container.find_elements(By.CSS_SELECTOR, 'div[class*="message-"]')
            current_message_count = len(messages)
            print(f"Current message count: {current_message_count}")
            
            # Stop if we have loaded around 50 messages
            if current_message_count >= 50:
                print("Reached target message count (50)")
                break
                
            if current_message_count == last_message_count:
                same_count += 1
                if same_count >= 3:  # If count hasn't changed for 3 iterations, we're at the top
                    print("Message count stable, reached the top")
                    break
            else:
                same_count = 0
            
            # Scroll to the first message
            if messages:
                print("Scrolling to first message...")
                driver.execute_script("arguments[0].scrollIntoView(true)", messages[0])
                time.sleep(3)  # Wait for messages to load
            
            last_message_count = current_message_count
                
        return True
    except Exception as e:
        print(f"Error scrolling to top: {e}")
        return False

def wait_for_user():
    """Wait for user to press Enter to continue"""
    input("Press Enter to continue...")

def run_scraper(group_name):
    """Main function to run the WhatsApp scraper"""
    try:
        print("Step 1: Initializing Chrome driver...")
        driver = setup_driver()
        wait = WebDriverWait(driver, 60)
        wait_for_user()
        
        print("\nStep 2: Opening WhatsApp Web...")
        driver.get("https://web.whatsapp.com/")
        print("Press Enter when you see the chat list...")
        wait_for_user()

        print("\nStep 3: Starting chat search...")
        print(f"Searching for chat: {group_name}")
        print("Press Enter when ready to search...")
        wait_for_user()
        
        chat_found = locate_chat(driver, wait, group_name)
        print("Press Enter after the chat is opened...")
        wait_for_user()
        
        if not chat_found:
            print("Failed to locate chat, trying alternative method...")
            try:
                # Use keyboard shortcut to focus search
                if os.name == 'posix':  # macOS
                    actions = webdriver.ActionChains(driver)
                    actions.key_down(Keys.COMMAND).send_keys('f').key_up(Keys.COMMAND).perform()
                else:  # Windows/Linux
                    actions = webdriver.ActionChains(driver)
                    actions.key_down(Keys.CONTROL).send_keys('f').key_up(Keys.CONTROL).perform()
                time.sleep(1)
                
                # Type group name and press enter
                actions = webdriver.ActionChains(driver)
                actions.send_keys(group_name + Keys.ENTER)
                actions.perform()
                time.sleep(3)
                
                # Verify we're in a chat
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "header[data-testid='conversation-header']")))
                print("Alternative method successful")
            except Exception as e:
                print(f"Alternative method failed: {e}")
                raise Exception("Could not locate the specified group chat")
        
        print("\nStep 4: Loading chat history...")
        print("Waiting for conversation panel to load...")
        try:
            chat_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="application"]')))
            print("Conversation panel loaded successfully")
            print("Press Enter to start scrolling to top...")
            wait_for_user()
            
            print("Scrolling to top to load all messages...")
            if not scroll_to_top(driver):
                raise Exception("Error scrolling to top of chat")
            wait_for_user()
        except Exception as e:
            print(f"Error loading chat history: {e}")
            raise
        
        print("\nStep 5: Processing messages...")
        print("Waiting for chat interface to load completely...")
        time.sleep(5)  # Give extra time for the interface to stabilize
        
        print("Looking for group header...")
        try:
            print("Checking if page is ready...")
            # Wait for the chat interface to be fully loaded
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="application"]')))
            print("Chat interface detected")
            
            # Try multiple possible header selectors with explicit waits
            print("Looking for header element...")
            try:
                # First try a generic header selector
                print("Trying generic header selector...")
                group_header = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "header")))
                print("Found header using generic selector")
            except Exception as e:
                print(f"Generic header selector failed: {str(e)}")
                print("Trying XPath selector...")
                try:
                    # Try finding header by its position in the DOM
                    group_header = wait.until(EC.presence_of_element_located(
                        (By.XPATH, "//div[@role='application']//header")
                    ))
                    print("Found header using XPath selector")
                except Exception as e:
                    print(f"XPath header selector failed: {str(e)}")
                    print("Trying to find any header-like element...")
                    # Try finding any element that looks like a header
                    group_header = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[role='heading'], [aria-label*='Chat'], [aria-label*='Conversation']")
                    ))
                    print("Found header-like element")
            
            # Try multiple possible title selectors with explicit waits
            print("Looking for title element...")
            try:
                # First try to find any text-containing element in the header
                print("Trying to find any text element in header...")
                title_elements = group_header.find_elements(By.XPATH, ".//*[text()]")
                if title_elements:
                    # Find the element with the longest text (likely the title)
                    title_element = max(title_elements, key=lambda e: len(e.text))
                    print("Found title using text content")
                else:
                    raise Exception("No text elements found in header")
            except Exception as e:
                print(f"Text content search failed: {str(e)}")
                print("Trying alternative selectors...")
                try:
                    # Try common title attributes
                    title_element = group_header.find_element(By.CSS_SELECTOR, 
                        "[title], [aria-label], [data-testid*='title'], [data-testid*='name'], span[dir='auto']"
                    )
                    print("Found title using attribute selector")
                except Exception as e:
                    print(f"Attribute selector failed: {str(e)}")
                    # Last resort: get all visible text from header
                    title_element = group_header
                    print("Using header element itself for text")
            
            # Try different ways to get the text
            try:
                actual_group_name = title_element.get_attribute('title') or \
                                  title_element.get_attribute('aria-label') or \
                                  title_element.text
                if not actual_group_name:
                    raise Exception("No text content found")
                print(f"Found group: {actual_group_name}")
            except Exception as e:
                print(f"Error getting group name: {str(e)}")
                actual_group_name = "Unknown Group"
        except Exception as e:
            print(f"Error finding group header: {str(e)}")
            print("Attempting to get HTML structure...")
            try:
                body_html = driver.find_element(By.TAG_NAME, "body").get_attribute('outerHTML')
                print(f"Page HTML structure: {body_html[:500]}...")  # Print first 500 chars
            except Exception as e2:
                print(f"Could not get HTML structure: {str(e2)}")
            raise
        
        # Wait for messages to be visible after scrolling
        print("Waiting for messages to be visible...")
        time.sleep(2)
        
        print("Looking for chat container...")
        chat_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="application"]')))
        print("Chat container found")
        
        print("Looking for message elements...")
        messages = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class*="message-"]')))
        print(f"Found {len(messages)} messages")
        
        # Process messages
        chat_data = []
        for index, message in enumerate(messages, 1):
            print(f"\nProcessing message {index}/{len(messages)}")
            try:
                # Get message metadata
                try:
                    print(f"  Waiting for message visibility...")
                    wait.until(EC.visibility_of(message))
                    
                    print("  Looking for metadata element...")
                    # Look for metadata within this specific message element
                    metadata = message.find_element(By.CSS_SELECTOR, 'div[data-pre-plain-text]')
                    print("  Found metadata element")
                    
                    print("  Getting metadata text...")
                    metadata_text = metadata.get_attribute('data-pre-plain-text')
                    print(f"  Metadata text: {metadata_text}")
                    
                    if metadata_text:
                        # Extract timestamp and sender from metadata (format: [timestamp] sender: )
                        parts = metadata_text.split(']')
                        if len(parts) >= 2:
                            timestamp = parts[0].strip('[')
                            sender = parts[1].split(':')[0].strip()
                            print(f"  Extracted - Timestamp: {timestamp}, Sender: {sender}")
                        else:
                            print("  Invalid metadata format")
                            timestamp = "NA"
                            sender = "Unknown"
                    else:
                        print("  No metadata text found")
                        timestamp = "NA"
                        sender = "System Message"
                except Exception as e:
                    print(f"  Error getting metadata for message: {str(e)}")
                    print(f"  Message HTML: {message.get_attribute('outerHTML')}")
                    timestamp = "NA"
                    sender = "System Message"
                
                # Get message content
                try:
                    print("  Looking for message content...")
                    # Wait for and find the message content with a more specific selector
                    content_element = message.find_element(By.CSS_SELECTOR, 'div[class*="copyable-text"] span[class*="selectable-text"]')
                    message_text = content_element.text if content_element else ""
                    print(f"  Message content: {message_text[:50]}..." if len(message_text) > 50 else f"  Message content: {message_text}")
                except Exception as e:
                    print(f"  Error getting message content: {str(e)}")
                    print(f"  Message HTML: {message.get_attribute('outerHTML')}")
                    message_text = ""
                
                # Determine message type
                print("  Determining message type...")
                message_type = "text"
                try:
                    if message.find_element(By.CSS_SELECTOR, 'img[data-testid*="image"]'):
                        message_type = "image"
                        print("  Type: image")
                except Exception as e:
                    pass
                
                try:
                    if message.find_element(By.CSS_SELECTOR, '*[data-testid*="video"]'):
                        message_type = "video"
                        print("  Type: video")
                except Exception as e:
                    pass
                
                try:
                    if message.find_element(By.CSS_SELECTOR, '*[data-testid*="audio"]'):
                        message_type = "audio"
                        print("  Type: audio")
                except Exception as e:
                    pass
                
                try:
                    if message.find_element(By.CSS_SELECTOR, '*[data-testid*="document"]'):
                        message_type = "document"
                        print("  Type: document")
                except Exception as e:
                    pass
                
                # Get URLs if any
                print("  Looking for URLs...")
                try:
                    urls = [a.get_attribute('href') for a in message.find_elements(By.TAG_NAME, 'a')]
                    if urls:
                        print(f"  Found URLs: {urls}")
                except Exception as e:
                    print(f"  Error getting URLs: {str(e)}")
                    urls = []
                
                chat_data.append([
                    actual_group_name,
                    message_type,
                    message_text,
                    sender,
                    timestamp,
                    str(urls)
                ])
                
            except Exception as e:
                print(f"Error processing message: {e}")
                continue
        
        print("\nStep 6: Saving data...")
        output_filename = f'scraped_data/{actual_group_name.replace(" ", "_")}.csv'
        headers = ['Group Name', 'Message Type', 'Message Text', 'Sender', 'Timestamp', 'URLs']
        output_to_csv([headers] + chat_data, output_filename)
        
        print(f"Scraping completed. Data saved to {output_filename}")
        wait_for_user()
        
    except Exception as e:
        print(f"Error during scraping: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    run_scraper("Chupitos en Politiek")
