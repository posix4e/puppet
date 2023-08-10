package com.ttt246.puppet

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.preference.PreferenceManager
import android.provider.Settings
import android.webkit.WebView
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity

class ChatterAct : AppCompatActivity() {
    private lateinit var webView: WebView
    private val TAG = "ChatterActLog"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        supportActionBar?.hide()

        val accessibilitySettingsBtn: Button = findViewById(R.id.accessibilitySettings)
        accessibilitySettingsBtn.setOnClickListener {
            val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
            startActivity(intent)
        }

        val settingsButton: Button = findViewById(R.id.settingsButton)
        webView = findViewById(R.id.webView)

        val sharedPreferences = PreferenceManager.getDefaultSharedPreferences(this)
        val serverUrl = sharedPreferences.getString("SERVER_URL", "https://default-url-if-not-set.com")
        if (serverUrl != null) {
            webView.loadUrl(serverUrl)
            webView.settings.javaScriptEnabled = true
            webView.settings.domStorageEnabled = true
        }

        settingsButton.setOnClickListener {
            val settingsIntent = Intent(this, SettingsActivity::class.java)
            startActivity(settingsIntent)
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onResume() {
        super.onResume()
        val sharedPreferences = PreferenceManager.getDefaultSharedPreferences(this)
        val serverUrl = sharedPreferences.getString("SERVER_URL", "https://default-url-if-not-set.com")
        if (serverUrl != null) {
            webView.settings.javaScriptEnabled = true
            webView.settings.domStorageEnabled = true
            webView.loadUrl(serverUrl)
        }
    }
}