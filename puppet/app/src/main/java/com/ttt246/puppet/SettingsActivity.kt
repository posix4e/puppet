package com.ttt246.puppet

import android.content.SharedPreferences
import android.os.Bundle
import android.preference.PreferenceManager
import android.provider.Settings
import android.widget.Button
import android.widget.EditText
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

class SettingsActivity : AppCompatActivity() {
    private lateinit var sharedPreferences: SharedPreferences

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        sharedPreferences = PreferenceManager.getDefaultSharedPreferences(this)
        val serverUrlEditText: EditText = findViewById(R.id.serverUrlEditText)
        val uuidEditText: EditText = findViewById(R.id.uuidEditText)
        val saveButton: Button = findViewById(R.id.saveButton)

        // Pre-fill the EditText with the current server URL.
        serverUrlEditText.setText(sharedPreferences.getString("SERVER_URL", ""))
        // Pre-fill the EditText with the UUID.
        uuidEditText.setText(sharedPreferences.getString("UUID", ""))

        saveButton.setOnClickListener {
            val serverUrl = serverUrlEditText.text.toString()
            val uuid = uuidEditText.text.toString()

            // Send a POST request to the server
            Thread {
                val url = URL("$serverUrl/add_command")
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json; utf-8")
                conn.doOutput = true
                val jsonInputString = "{\"uid\": \"$uuid\", \"command\": \"ping:ping\"}"
                try {
                    OutputStreamWriter(conn.outputStream).use { writer ->
                        writer.write(jsonInputString)
                    }

                    val responseCode = conn.responseCode
                    if (responseCode == HttpURLConnection.HTTP_OK) {
                        // Save the server URL and UUID if the POST request was successful
                        val editor = sharedPreferences.edit()
                        editor.putString("SERVER_URL", serverUrl)
                        editor.putString("UUID", uuid)
                        editor.apply()
                        finish() // Close the activity
                    } else {
                        throw Exception("Unable to connect to server $responseCode")
                    }
                } catch (e: Exception) {
                        runOnUiThread {
                        AlertDialog.Builder(this@SettingsActivity)
                            .setTitle("Error")
                            .setMessage("Unable to connect to server with correct uuid $e")
                            .setPositiveButton(android.R.string.ok, null)
                            .show()
                    }
                }
            }.start()
        }
    }
}
