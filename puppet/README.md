# Puppet Android App Readme
Checkout
- https://github.com/posix4e/puppet/blob/main/.github/workflows/android.yml
To understand tests or
- https://github.com/posix4e/puppet/blob/main/.github/workflows/release_ci.yml
To understand how to build an apk. This is where our releases are generated
## Description

Puppet is an Android app that allows users to automate and control various actions on their device using an Accessibility Service. The app is designed to interact with the device's user interface, perform clicks, scroll, type, and execute custom intents based on the commands received from a remote server. Puppet is useful for automating repetitive tasks, testing applications, and more.

## Development


## Features

- **Accessibility Service:** Puppet uses an Accessibility Service to gain access to the device's user interface and perform various actions.
- **Remote Control:** The app communicates with a remote server to receive commands and send event logs.
- **Click, Scroll, and Type:** Puppet can simulate clicks, scroll up and down, and type text into input fields based on the commands received from the server.
- **Custom Intents:** The app can execute custom intents sent from the server, allowing users to control other applications on the device.
- **Heartbeat Mechanism:** Puppet sends event logs and retrieves commands from the server periodically using a heartbeat mechanism.
- **Notification:** The app runs in the background and shows a persistent notification to indicate that the service is active.

## Permissions

- `android.permission.INTERNET`: Required to communicate with the remote server.
- `android.permission.BIND_ACCESSIBILITY_SERVICE`: Needed to use the Accessibility Service.
- `android.permission.FOREGROUND_SERVICE`: Required to run the service in the foreground with a persistent notification.

## Usage

1. After installing the app, grant it the necessary permissions, including the Accessibility Service.
2. Launch the app, and it will automatically open the Accessibility Settings for the user to enable the service.
3. The app's main activity (`ChatterAct`) will display a WebView that loads the URL specified in the app's settings. The URL is fetched from the server settings.
4. To change the server URL, click on the "Settings" button in the app's main activity. The `SettingsActivity` allows users to update the server URL.
5. The app will periodically send event logs to the server using a heartbeat mechanism. These logs contain information about the device's user interface.
6. The server can send commands to the app, which will be executed by the Accessibility Service. Supported commands include click, scroll, type, and custom intents.

## Important Notes

- The app requires a server to send commands and receive event logs. Ensure that the server is properly set up and accessible from the app.
- The app's Accessibility Service may require additional permissions depending on the target application's UI elements.
- Be cautious while using this app, as it can perform actions automatically on the device, and incorrect commands can cause unintended consequences.

## Disclaimer

This app is intended for educational and testing purposes only. The developers are not responsible for any misuse or damage caused by the app. Use it responsibly and in compliance with all applicable laws and regulations.

## Credits

Puppet app is developed by TTT246.

## License

The Puppet app is distributed under the [MIT License](https://opensource.org/licenses/MIT). Feel free to modify and use it as per the terms of the license.
