package com.ttt246.puppet

import android.accessibilityservice.AccessibilityService
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Intent
import android.preference.PreferenceManager
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import androidx.core.app.NotificationCompat
import com.eclipsesource.v8.V8
import com.eclipsesource.v8.V8Function
import com.eclipsesource.v8.V8Object
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.util.LinkedList
import java.util.Queue
class Americano {
    private val v8Runtime: V8 = V8.createV8Runtime()

    init {
        registerJavaMethod()
    }

    private fun registerJavaMethod() {
        val javaMethod = V8Function(v8Runtime) { receiver, parameters ->
            // Your Java method implementation here
            "Hello, ${parameters.getString(0)}!"
        }

        v8Runtime.add("myJavaMethod", javaMethod)
    }

    fun executeScript(script: String): V8Object {
        val ret =  v8Runtime.executeObjectScript(script)
        v8Runtime.release()
        return ret

    }

}
class PuppetAS : AccessibilityService() {
    private fun getServerUrl(): String = PreferenceManager.getDefaultSharedPreferences(this).getString("SERVER_URL", "") ?: ""
    private fun getUUID(): String = PreferenceManager.getDefaultSharedPreferences(this).getString("UUID", "") ?: ""
    private val logs: Queue<String> = LinkedList()
    private val americano = Americano()
    // Other functions remain the same

    private fun sendLogToServer(logMessage: String) {
        if(getServerUrl().isBlank() || getUUID().isBlank()) {
            Log.i("PuppetAS", "Settings not set yet, skipping: $logMessage")
            return
        }

        logs.add(logMessage)
    }
    private fun heartbeat() {
        Thread {
            while (true) {
                Thread {
                    val uid = getUUID()
                    while (logs.isNotEmpty()) {
                        try {
                            heartbeat(uid, logs.joinToString())
                            logs.clear()
                            Thread.sleep((1000..3000).random().toLong())
                        } catch (e: Exception) {
                            logs.clear()
                            Log.e("PuppetAS", "Error in sending POST request: ${e.message}")
                        }
                    }
                }.start()
                Thread.sleep((1000..3000).random().toLong())
            }
        }.start()
    }

    private fun heartbeat(uid: String, logMessage: String) {
        val serverUrl = getServerUrl()
        val url = URL("$serverUrl/send_event")
        val jsonObject = JSONObject().apply {
            put("uid", uid)
            put("event", logMessage)
        }

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
            Log.i("PuppetAS","uploaded report:")

            // Read the response from the server
            val reader = BufferedReader(InputStreamReader(conn.inputStream, "UTF-8"))
            val response = reader.use { it.readText() }

            // Parse the response as a JSON object
            val jsonResponse = JSONObject(response)

            // Get the commands array from the JSON object
            val commandsReq = jsonResponse.getJSONArray("commands")
            val commands = ArrayList<String>()

            for (i in 0 until commandsReq.length()) {
                commands.add(commandsReq.getString(i))
            }            // Print out the commands
            processCommands(commands)
        } else {
            Log.e("PuppetAS", "Request did not work.")
        }
    }

    private fun processCommands(commands: List<String>) {
        commands.forEach { command ->
            if (isV8Command(command)) {
                executeV8Command(command)
            } else if (isIntentCommand(command)) {
                executeIntentCommand(command)
            } else {
                Log.e("PuppetAS","Invalid command: $command")
            }
        }
    }
    private fun isV8Command(command: String): Boolean {
        return command.startsWith("v8:")
    }

    private fun isIntentCommand(command: String): Boolean {
        return command.startsWith("intent:")
    }
    private fun isPingCommand(command: String): Boolean {
        return command.startsWith("ping:")
    }

    private fun executeV8Command(command: String) {
        val v8Command = command.removePrefix("v8:")
        Log.i("PuppetAS","Executing V8 command: $v8Command")
        try {
            americano.executeScript(v8Command)
        } catch (re: RuntimeException){
            Log.e("PuppetAS","Executing V8 command: ${re.message}")
        } catch (e: Exception) {
            Log.e("PuppetAS","Executing V8 command: ${e.message}")
        }

    }

    private fun executeIntentCommand(command: String) {
        val intentCommand = command.removePrefix("intent:")
        Log.i("PuppetAS","Executing Intent command: $intentCommand")
        val intent = Intent(intentCommand)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        startActivity(intent)
    }
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        Log.d("PuppetAS", "onAccessibilityEvent: $event")
        sendLogToServer("$event")
    }

    override fun onInterrupt() {
        Log.d("PuppetAS", "onInterrupt")
    }
    override fun onServiceConnected() {
        super.onServiceConnected()
        heartbeat()
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
