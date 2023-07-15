package com.ttt246.puppet
import android.annotation.SuppressLint
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.View
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.google.android.gms.tasks.OnCompleteListener
import com.google.firebase.messaging.FirebaseMessaging
import java.io.File
import java.io.IOException


@Suppress("DEPRECATION")
class ChatterAct : AppCompatActivity() {
    private var fcmToken: String = String()
    private var uuid: String = String()

    @SuppressLint("HardwareIds")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Hide the status bar (system toolbar)
        window.decorView.systemUiVisibility = View.SYSTEM_UI_FLAG_FULLSCREEN
        supportActionBar?.hide()

        initToken()
        // on below line we are getting device id.
        uuid = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID)
        val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
        startActivity(intent)

    }

    private fun initToken() {
        FirebaseMessaging.getInstance().token.addOnCompleteListener(OnCompleteListener { task ->
            if (!task.isSuccessful) {
                return@OnCompleteListener
            }

            fcmToken = task.result
        })
    }

    fun getFCMToken(): String {
        return this.fcmToken
    }

    fun getUUID(): String {
        return this.uuid
    }
}