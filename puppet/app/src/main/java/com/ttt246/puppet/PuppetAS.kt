package com.ttt246.puppet

import android.accessibilityservice.AccessibilityService
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Intent
import android.os.Bundle
import android.preference.PreferenceManager
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import androidx.core.app.NotificationCompat
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.util.LinkedList
import java.util.Queue


open class PuppetAS : AccessibilityService() {
    private fun getServerUrl(): String =
        PreferenceManager.getDefaultSharedPreferences(this).getString("SERVER_URL", "") ?: ""

    private fun getUUID(): String =
        PreferenceManager.getDefaultSharedPreferences(this).getString("UUID", "") ?: ""

    private val logs: Queue<String> = LinkedList()

    private fun sendLogToServer(logMessage: String) {
        if (getServerUrl().isBlank() || getUUID().isBlank()) {
            Log.i("PuppetAS", "Settings not set yet, skipping: $logMessage")
            return
        }

        logs.add(logMessage)
    }

    private fun heartbeat() {
        Thread {
            while (true) {
                val uid = getUUID()
                if (logs.isNotEmpty()) {
                    try {
                        heartbeat(uid, logs.joinToString())
                    } catch (e: Exception) {
                        Log.e("PuppetAS", "Error in sending POST request: ${e.message}")
                    } finally {
                        logs.clear()
                    }
                }
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
            Log.i("PuppetAS", "uploaded report:")

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

     fun processCommands(commands: List<String>) {
        commands.forEach { command ->
            when {
                isIntentCommand(command) -> executeIntentCommand(command)
                isAccCommand(command) -> executeAccCommand(command)
                else -> Log.e("PuppetAS", "Invalid command: $command")
            }
        }
    }

    fun isIntentCommand(command: String): Boolean {
        return command.startsWith("intent:")
    }

     fun isAccCommand(command: String): Boolean {
        return command.startsWith("acc:")
    }

     fun executeAccCommand(command: String) {
        val accCommand = command.removePrefix("acc:")
        Log.i("PuppetAS", "Executing Acc command: $accCommand")

        when {
            accCommand.startsWith("UP") -> scrollAction(AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD)
            accCommand.startsWith("DOWN") -> scrollAction(AccessibilityNodeInfo.ACTION_SCROLL_FORWARD)
            accCommand.startsWith("CLICK") -> {
                if (accCommand == "CLICK FIRST") {
                    getFirstClickableNode()?.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                } else {
                    val id = accCommand.removePrefix("CLICK ").trim()
                    clickView(id)
                }
            }

            accCommand.startsWith("TYPE") -> {
                if (accCommand == "TYPE FIRST") {
                    val text = "default text"  // or whatever text you want to input
                    val arguments = Bundle()
                    arguments.putCharSequence(
                        AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text
                    )
                    getFirstTypeableNode()?.performAction(
                        AccessibilityNodeInfo.ACTION_SET_TEXT, arguments
                    )
                } else {
                    val id = accCommand.removePrefix("TYPE ").substringBefore("\"").trim()
                    val text = accCommand.substringAfter("\"").removeSuffix("\"")
                    typeInView(id, text)
                }
            }
        }
    }


    private fun scrollAction(action: Int) {
        val rootNode = rootInActiveWindow ?: return

        // Use a recursive function to find scrollable items
        fun findScrollableNode(node: AccessibilityNodeInfo?): AccessibilityNodeInfo? {
            if (node == null) return null

            // If current node is scrollable, return it
            if (node.isScrollable) return node

            // Otherwise, check its children
            for (i in 0 until node.childCount) {
                val scrollableChild = findScrollableNode(node.getChild(i))
                if (scrollableChild != null) return scrollableChild
            }

            return null
        }

        // Find a scrollable node and perform a scroll action on it
        val scrollableNode = findScrollableNode(rootNode)
        scrollableNode?.performAction(action)
    }

    private fun traverseNodeAndPrint(node: AccessibilityNodeInfo?, id: Int): String {
        if (node == null) return ""

        var output = ""

        for (i in 0 until node.childCount) {
            val child = node.getChild(i)
            if (child != null) {
                output += when {
                    child.isClickable -> "<link id=$id>${child.text}</link>"
                    child.isCheckable -> "<button id=$id>${child.text}</button>"
                    child.isEditable -> "<input id=$id>${child.text}</input>"
                    child.text != null -> "<text id=$id>${child.text}</text>"
                    else -> traverseNodeAndPrint(child, id + 1)
                }
                output += "\n"
            }
        }

        return output
    }

    private fun getFirstClickableNode(): AccessibilityNodeInfo? {
        val rootNode = rootInActiveWindow ?: return null
        return findFirstMatchingNode(rootNode) { it.isClickable }
    }

    private fun getFirstTypeableNode(): AccessibilityNodeInfo? {
        val rootNode = rootInActiveWindow ?: return null
        return findFirstMatchingNode(rootNode) { it.actionList.contains(AccessibilityNodeInfo.AccessibilityAction.ACTION_SET_TEXT) }
    }

    private fun findFirstMatchingNode(
        node: AccessibilityNodeInfo?, predicate: (AccessibilityNodeInfo) -> Boolean
    ): AccessibilityNodeInfo? {
        if (node == null) return null
        if (predicate(node)) return node

        for (i in 0 until node.childCount) {
            val matchingChild = findFirstMatchingNode(node.getChild(i), predicate)
            if (matchingChild != null) return matchingChild
        }

        return null
    }

    private fun clickView(id: String) {
        val rootNode = rootInActiveWindow ?: return
        val nodes = rootNode.findAccessibilityNodeInfosByViewId(id)
        nodes.forEach {
            it.performAction(AccessibilityNodeInfo.ACTION_CLICK)
        }
    }

    private fun typeInView(id: String, text: String) {
        val rootNode = rootInActiveWindow ?: return
        val nodes = rootNode.findAccessibilityNodeInfosByViewId(id)
        nodes.forEach {
            val arguments = Bundle()
            arguments.putCharSequence(
                AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text
            )
            it.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments)
        }
    }

    fun executeIntentCommand(command: String) {
        val intentCommand = command.removePrefix("intent:")

        Log.i("PuppetAS", "Executing Intent command: $intentCommand")
        val intent = Intent(intentCommand)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        startActivity(intent)
    }

    private var lastOutput: String? = null

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        event?.source?.let { rootNode ->
            val output = traverseNodeAndPrint(rootNode, 1)
            if (output.length > 5 && output != lastOutput) {
                Log.d("PuppetAS", "onAccessibilityEvent: $event")
                Log.d("PuppetAS", output)
                sendLogToServer("event: $event output: $output")
                lastOutput = output // store the new output
            }
        }
    }

    override fun onInterrupt() {
        Log.d("PuppetAS", "onInterrupt")
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        heartbeat()
        createNotificationChannel()

        val notification = NotificationCompat.Builder(this, "MyAccessibilityServiceChannel")
            .setContentTitle("My Accessibility Service").setContentText("Running...")
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