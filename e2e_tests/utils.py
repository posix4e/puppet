from selenium.webdriver.remote.webdriver import WebDriver


def wait_for_element(
    driver: WebDriver, by_selector: str, selector_value: str, timeout: int = 2
):
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by_selector, selector_value))
        )

    except:
        element = None
    finally:
        return element


def find_and_click(driver: WebDriver, by_selector: str, selector_value: str):
    element = driver.find_element(by=by_selector, value=selector_value)
    element.click()
    return element
