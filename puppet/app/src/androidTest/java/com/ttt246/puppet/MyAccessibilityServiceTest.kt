package com.ttt246.puppet

import android.content.pm.PackageManager
import android.util.Log
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class MyAccessibilityServiceTest {
    @get:Rule
    var rule: ActivityScenarioRule<ChatterAct> = ActivityScenarioRule(ChatterAct::class.java)

    private val context = InstrumentationRegistry.getInstrumentation().targetContext

    @Test
    fun testHandleEvent() {
        val myService = PuppetAS()
        val packageManager = context.packageManager

        val applications = packageManager.getInstalledApplications(PackageManager.GET_META_DATA)
        for (applicationInfo in applications) {
            val packageName = applicationInfo.packageName
            val appName = packageManager.getApplicationLabel(applicationInfo).toString()
            Log.d("AppList", "App: $appName, Package: $packageName")
        }
    }
}
