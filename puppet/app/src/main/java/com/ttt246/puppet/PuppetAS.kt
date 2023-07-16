package com.ttt246.puppet

import android.accessibilityservice.AccessibilityService
import android.app.NotificationChannel
import android.app.NotificationManager
import android.preference.PreferenceManager
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import androidx.core.app.NotificationCompat
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

class PuppetAS : AccessibilityService() {
    private fun getServerUrl(): String = PreferenceManager.getDefaultSharedPreferences(this).getString("SERVER_URL", "") ?: ""
    private fun getUUID(): String = PreferenceManager.getDefaultSharedPreferences(this).getString("UUID", "") ?: ""

    // Other functions remain the same

    private fun sendLogToServer(logMessage: String) {
        if(getServerUrl().isBlank() || getUUID().isBlank()) {
            Log.i("PuppetAS", "Settings not set yet, skipping: $logMessage")
            return
        }

        Thread {
            try {
                val serverUrl = getServerUrl()
                val url = URL("$serverUrl/send_event")
                val jsonObject = JSONObject().apply {
                    put("uid", getUUID())
                    put("event", logMessage)
                }

                sendRequest(url, jsonObject)

            } catch (e: Exception) {
                Log.e("PuppetAS", "Error in sending POST request: ${e.message}")
            }
        }.start()
    }

    private fun sendRequest(url: URL, jsonObject: JSONObject) {
        val conn = url.openConnection() as HttpURLConnection
        conn.requestMethod = "POST"
        conn.setRequestProperty("Content-Type", "application/json; utf-8")
        conn.setRequestProperty("Accept", "application/json")
        conn.doOutput = true
        conn.doInput = true

        val writer = OutputStreamWriter(conn.outputStream, "UTF-8")
        writer.use {
            it.write(jsonObject.toString())
        }

        val responseCode = conn.responseCode
        Log.i("PuppetAS", "POST Response Code :: $responseCode")
        if (responseCode == HttpURLConnection.HTTP_OK) {
            Log.i("PuppetAS","uploaded report")
        } else {
            Log.e("PuppetAS", "Request did not work.")
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        Log.d("MyAccessibilityService", "onAccessibilityEvent: $event")
        sendLogToServer("$event")
    }

    override fun onInterrupt() {
        Log.d("MyAccessibilityService", "onInterrupt")
    }
    override fun onServiceConnected() {
        super.onServiceConnected()
        createNotificationChannel()

        val notification = NotificationCompat.Builder(this, "MyAccessibilityServiceChannel")
            .setContentTitle("My Accessibility Service")
            .setContentText("Running...")
            .setSmallIcon(R.drawable.ic_launcher_foreground) // replace with your own small icon
            .build()

        startForeground(1, notification)
    }

    private fun createNotificationChannel() {
        val serviceChannel = NotificationChannel(
            "MyAccessibilityServiceChannel",
            "My Accessibility Service Channel",
            NotificationManager.IMPORTANCE_DEFAULT
        )

        val manager: NotificationManager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(serviceChannel)
    }

}
