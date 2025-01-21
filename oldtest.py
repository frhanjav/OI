import undetected_chromedriver as uc
import time

def test_selenium():
    print("Starting test...")
    try:
        # Create Chrome options
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        
        # Initialize driver
        print("Initializing Chrome driver...")
        driver = uc.Chrome(options=options)
        
        # Navigate to a simple website first
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