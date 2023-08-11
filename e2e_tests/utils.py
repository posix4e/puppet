from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException


def wait_for_element(
    driver: WebDriver, by_selector: str, selector_value: str, timeout: int = 2
):
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    element = None

    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by_selector, selector_value))
        )

    except TimeoutException:
        element = None
    finally:
        return element


def find_and_click(driver: WebDriver, by_selector: str, selector_value: str):
    element = driver.find_element(by=by_selector, value=selector_value)
    element.click()
