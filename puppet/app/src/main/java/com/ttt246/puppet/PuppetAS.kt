package com.ttt246.puppet
import android.accessibilityservice.AccessibilityService
import android.app.NotificationChannel
import android.app.NotificationManager
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import androidx.core.app.NotificationCompat
import java.io.File

class PuppetAS : AccessibilityService() {

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        Log.d("MyAccessibilityService", "onAccessibilityEvent: $event")
        writeLogToFile("$event")
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
    private fun writeLogToFile(logMessage: String) {
        val logFile = File(filesDir, "accessibility.log")
        logFile.appendText("$logMessage\n")
    }

}
