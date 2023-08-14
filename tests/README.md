Running Tests

This serves as a framework to build regression tests for puppet android app.
Currently the test supports running the tests against the built android package in dev machine or in sauce labs.

Common code to enable/activate privacy setting for puppet app exists in the same file.
Which can be abstracted away in future to make it reusable across other test files.
This uses Appium to drive the android app and send instructions.

For SauceLabs test assumes the username, accesskey and UUID is available as environment variable.

By altering the device name, the tests can be run against an emulator or real android device in saucelabs.

For local machine, an appium server, android emulator and Java SDK is required.

`pip install -r requirements.txt`

`python test_sauce_labs.py`

While running locally, you can create a .env file inside e2e_tests folder and place your environment variables.
