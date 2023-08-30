package com.ttt246.puppet

//import androidx.test.runner.AndroidJUnit4

import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.action.ViewActions
import androidx.test.espresso.action.ViewActions.click
import androidx.test.espresso.matcher.ViewMatchers.withId
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.rule.GrantPermissionRule
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class MyAdblockVPNServiceTest {
    @get:Rule
    var activityRule = ActivityScenarioRule(ChatterAct::class.java)

    @get:Rule
    val permissionRule: GrantPermissionRule = GrantPermissionRule.grant(
        android.Manifest.permission.POST_NOTIFICATIONS,
        android.Manifest.permission.FOREGROUND_SERVICE,
        android.Manifest.permission.INTERNET
        )

    @Test
    fun test_vpn() {
        onView(withId(R.id.settingsButton)).perform(click())
        onView(withId(R.id.serverUrlEditText)).
                perform(ViewActions.clearText(), ViewActions.typeText("https://up20-puppet-staging.hf.space"))

        onView(withId(R.id.saveButton)).perform(click())
        BaseRobot().doOnView(withId(R.id.settingsButton), click())
        onView(withId(R.id.enableVPNButton)).perform(click())
        onView(withId(R.id.disableVPNButton)).perform(click())
    }
}