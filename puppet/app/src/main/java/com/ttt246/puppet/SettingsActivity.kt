package com.ttt246.puppet

import android.content.SharedPreferences
import android.os.Bundle
import android.preference.PreferenceManager
import android.widget.Button
import android.widget.EditText
import androidx.appcompat.app.AppCompatActivity

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
            val editor = sharedPreferences.edit()
            editor.putString("SERVER_URL", serverUrlEditText.text.toString())
            editor.putString("UUID", uuidEditText.text.toString())
            editor.apply()
            finish() // Close the activity
        }
    }
}
