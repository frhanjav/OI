import undetected_chromedriver as uc
import time
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import chromedriver_autoinstaller

def test_selenium():
    print("Starting test...")
    try:
        # Install matching ChromeDriver version
        print("Installing matching ChromeDriver...")
        chromedriver_autoinstaller.install()
        
        # Create Chrome options
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        
        # Initialize driver with version specification
        print("Initializing Chrome driver...")
        driver = uc.Chrome(
            options=options,
            version_main=131  # Specify your Chrome version
        )
        
        # Navigate to a simple website
        print("Navigating to website...")
        driver.get("https://example.com")
        
        # Wait a bit
        print("Waiting for 10 seconds...")
        time.sleep(10)
        
        # Print page title
        print(f"Page title: {driver.title}")
        
        # Close driver
        print("Closing driver...")
        driver.quit()
        
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    test_selenium()