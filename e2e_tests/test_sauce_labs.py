# Python/Pytest
from contextlib import contextmanager
import time
import unittest
import os

from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.remote.webdriver import WebDriver
from dotenv import load_dotenv
from utils import wait_for_element, find_and_click

load_dotenv()

# SAUCE LABS Specific configuration
SAUCE_USERNAME = os.getenv("SAUCE_USERNAME")
SAUCE_ACCESS_KEY = os.getenv("SAUCE_ACCESS_KEY")
TEST_UUID = os.getenv("TEST_UUID", "")
BUILD_STAGE = os.getenv("BUILD_STAGE", "DEV")

# Sauce labs URL
APPIUM_SERVER_URL = "http://127.0.0.1:4723"
SAUCE_LABS_URL = "https://ondemand.us-west-1.saucelabs.com:443/wd/hub"

# Android specific application
APP_PACKAGE_NAME = "com.ttt246.puppet"
APP_ACTIVITY_NAME = ".ChatterAct"


def create_android_driver(sauce_labs=False):
    capabilities = dict(
        platformName="Android",
        automationName="uiautomator2",
        deviceName="Android",
        appPackage=APP_PACKAGE_NAME,
        appActivity=APP_ACTIVITY_NAME,
        language="en",
        locale="US",
    )

    capabilities["appium:autoGrantPermissions"] = "true"
    capabilities["appium:autoAcceptAlerts"] = "true"
    capabilities["appium:automationName"] = "uiautomator2"

    if sauce_labs:
        capabilities["appium:deviceOrientation"] = "portrait"
        capabilities["appium:platformVersion"] = "13.0"
        capabilities["sauce:options"] = {}
        capabilities["sauce:options"]["username"] = SAUCE_USERNAME
        capabilities["sauce:options"]["accessKey"] = SAUCE_ACCESS_KEY
        capabilities["sauce:options"]["build"] = f"puppet-build-{BUILD_STAGE}"
        capabilities["sauce:options"]["name"] = "Test Android"
        capabilities["appium:app"] = "storage:filename=app-release-unsigned.apk"
        capabilities["appium:deviceName"] = "Android GoogleAPI Emulator"

        connection_url = "https://ondemand.us-west-1.saucelabs.com:443/wd/hub"
    else:
        connection_url = APPIUM_SERVER_URL

    return webdriver.Remote(connection_url, capabilities)


@contextmanager
def android_driver(options):
    driver = create_android_driver(sauce_labs=True)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


def save_server_settings(driver: WebDriver):
    element = find_and_click(
        driver,
        by_selector=AppiumBy.ID,
        selector_value=f"{APP_PACKAGE_NAME}:id/settingsButton",
    )
    element = driver.find_element(
        by=AppiumBy.ID, value=f"{APP_PACKAGE_NAME}:id/serverUrlEditText"
    )
    element.send_keys("https://posix4e-puppet.hf.space")
    element = driver.find_element(
        by=AppiumBy.ID, value=f"{APP_PACKAGE_NAME}:id/uuidEditText"
    )
    element.send_keys(TEST_UUID)
    element = find_and_click(
        driver,
        by_selector=AppiumBy.ID,
        selector_value=f"{APP_PACKAGE_NAME}:id/saveButton",
    )


def enable_privacy_settings(driver: WebDriver):
    element = find_and_click(
        driver,
        by_selector=AppiumBy.XPATH,
        selector_value=f"//*[@text='puppet']",
    )
    primary_checkbox = driver.find_element(
        by=AppiumBy.ID, value="android:id/switch_widget"
    )

    # Use Puppet button
    if not primary_checkbox.get_attribute("checked") == "true":
        primary_checkbox.click()
        element = wait_for_element(driver, AppiumBy.XPATH, "//*[@text='Allow']")
        if element:
            element.click()

    # Puppet shortcut button
    secondary_checkbox = driver.find_element(
        by=AppiumBy.ID, value="com.android.settings:id/switchWidget"
    )
    if not secondary_checkbox.get_attribute("checked") == "true":
        secondary_checkbox.click()

    # driver.start_activity(APP_PACKAGE_NAME, APP_ACTIVITY_NAME)
    # driver.activate_app(f"{APP_PACKAGE_NAME}")
    # These sleeps are harsh, however are now needed till will fix the activity which brings up settings by default
    # Once thats fixed, we can activate the app back it should resume as is, without the back button

    driver.back()
    time.sleep(1)
    driver.back()
    time.sleep(1)


class TestAppium(unittest.TestCase):
    def test_tab_4(self):
        # Usage of the context manager ensures the driver session is closed properly
        # after the test completes. Otherwise, make sure to call `driver.quit()` on teardown.
        with android_driver({}) as driver:
            enable_privacy_settings(driver)

            driver.wait_activity(APP_ACTIVITY_NAME, 5)

            save_server_settings(driver)

            element = driver.find_element(by=AppiumBy.XPATH, value='//*[@text="Tab 4"]')
            element.click()
            element = driver.find_element(
                by=AppiumBy.XPATH, value="//android.widget.EditText[@hint='UID']"
            )
            element.send_keys(TEST_UUID)
            element = driver.find_element(
                by=AppiumBy.XPATH, value="//android.widget.EditText[@hint='Command']"
            )
            element.send_keys("test")
            element = driver.find_element(
                by=AppiumBy.XPATH, value='//*[@text="Submit"]'
            )
            element.click()


if __name__ == "__main__":
    unittest.main()
