# Python/Pytest
from contextlib import contextmanager
import time
import unittest
import os

from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.remote.webdriver import WebDriver

APPIUM_PORT = 4723
APPIUM_HOST = "127.0.0.1"

SAUCE_USERNAME = os.getenv("SAUCE_USERNAME")
SAUCE_ACCESS_KEY = os.getenv("SAUCE_ACCESS_KEY")
TEST_UUID = os.getenv("TEST_UUID", "")


def create_android_driver(sauce_labs=False):
    capabilities = dict(
        platformName="Android",
        automationName="uiautomator2",
        deviceName="Android",
        appPackage="com.ttt246.puppet",
        appActivity=".ChatterAct",
        language="en",
        locale="US",
    )
    capabilities["appium:app"] = "app-release-unsigned.apk"
    capabilities["autoGrantPermissions"] = "true"
    connection_url = f"http://{APPIUM_HOST}:{APPIUM_PORT}"
    if sauce_labs:
        capabilities["platformName"] = "Android"
        capabilities["appium:app"] = "storage:filename=app-release-unsigned.apk"
        capabilities["appium:deviceName"] = "Android GoogleAPI Emulator"
        capabilities["appium:deviceOrientation"] = "portrait"
        capabilities["appium:platformVersion"] = "13.0"
        capabilities["appium:automationName"] = "uiautomator2"
        capabilities["appPackage"] = "com.ttt246.puppet"
        capabilities["appActivity"] = ".ChatterAct"
        capabilities["appium:autoGrantPermissions"] = "true"
        capabilities["sauce:options"] = {}
        capabilities["sauce:options"]["username"] = SAUCE_USERNAME
        capabilities["sauce:options"]["accessKey"] = SAUCE_ACCESS_KEY
        capabilities["sauce:options"]["build"] = "appium-build-HGNZD"
        capabilities["sauce:options"]["name"] = "Automate Tests"
        capabilities["appium:app"] = "storage:filename=app-release-unsigned.apk"
        capabilities["appium:deviceName"] = "Android GoogleAPI Emulator"

        connection_url = "https://ondemand.us-west-1.saucelabs.com:443/wd/hub"

    return webdriver.Remote(connection_url, capabilities)


@contextmanager
def android_driver(options):
    # prefer this fixture if there is no need to customize driver options in tests
    driver = create_android_driver(sauce_labs=True)
    yield driver
    driver.quit()


def save_server_settings(driver: WebDriver):
    el8 = driver.find_element(
        by=AppiumBy.ID, value="com.ttt246.puppet:id/settingsButton"
    )
    el8.click()
    el9 = driver.find_element(
        by=AppiumBy.ID, value="com.ttt246.puppet:id/serverUrlEditText"
    )
    el9.send_keys("https://posix4e-puppet.hf.space")
    el10 = driver.find_element(
        by=AppiumBy.ID, value="com.ttt246.puppet:id/uuidEditText"
    )
    el10.send_keys("1608052e-b294-4a6f-a69f-e18c9bedf5c8")
    el11 = driver.find_element(by=AppiumBy.ID, value="com.ttt246.puppet:id/saveButton")
    el11.click()


def enable_privacy_settings(driver: WebDriver):
    driver.find_element(by=AppiumBy.XPATH, value='//*[@text="puppet"]').click()
    primary_checkbox = driver.find_element(
        by=AppiumBy.ID, value="android:id/switch_widget"
    )

    # Use Puppet button
    if not primary_checkbox.get_attribute("checked") == "true":
        primary_checkbox.click()
        try:
            driver.find_element(by=AppiumBy.XPATH, value="//*[@text='Allow']").click()
        except Exception as e:
            pass

    # Puppet shortcut button
    secondary_checkbox = driver.find_element(
        by=AppiumBy.ID, value="com.android.settings:id/switchWidget"
    )
    if not secondary_checkbox.get_attribute("checked") == "true":
        secondary_checkbox.click()
        try:
            driver.find_element(by=AppiumBy.XPATH, value="//*[@text='Got it']").click()
        except Exception as e:
            pass

    time.sleep(2)
    driver.back()
    time.sleep(2)
    driver.back()


class TestAppium(unittest.TestCase):
    def test_tab_4(self):
        import time

        # Usage of the context manager ensures the driver session is closed properly
        # after the test completes. Otherwise, make sure to call `driver.quit()` on teardown.
        with android_driver({}) as driver:
            driver.implicitly_wait(10)

            enable_privacy_settings(driver)

            driver.activate_app("com.ttt246.puppet")
            driver.wait_activity(".ChatterAct", 5)
            time.sleep(2)

            save_server_settings(driver)

            el14 = driver.find_element(by=AppiumBy.XPATH, value='//*[@text="Tab 4"]')
            el14.click()
            el15 = driver.find_element(
                by=AppiumBy.XPATH, value="//android.widget.EditText[@hint='UID']"
            )
            el15.send_keys(TEST_UUID)
            el16 = driver.find_element(
                by=AppiumBy.XPATH, value="//android.widget.EditText[@hint='Command']"
            )
            el16.send_keys("test")
            el17 = driver.find_element(by=AppiumBy.XPATH, value='//*[@text="Submit"]')
            el17.click()
            time.sleep(5)


if __name__ == "__main__":
    unittest.main()
