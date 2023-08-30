package com.ttt246.puppet

import android.content.Context
import android.content.Intent
import androidx.test.core.app.ApplicationProvider
import junit.framework.TestCase.assertEquals
import junit.framework.TestCase.assertNotNull
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.mockito.Mockito
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

class TestableAdblockVPNServiceTest: AdblockVPNService() {
    fun attachBaseContextPublic(context: Context) {
        attachBaseContext(context)
    }
}
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [Config.OLDEST_SDK])
class AdblockVPNServiceTest{
    private lateinit var adblockService: TestableAdblockVPNServiceTest
    @Before
    fun setUp() {
        adblockService = Mockito.spy(TestableAdblockVPNServiceTest())
        val context = ApplicationProvider.getApplicationContext<Context>()
        adblockService.attachBaseContextPublic(context)
    }

    @Test
    fun test_start() {
        Intent(adblockService, AdblockVPNService::class.java).also {
            it.action = AdblockVPNService.Action.START.toString()
            val componentName = adblockService.startService(it)
            assertNotNull(componentName)
            assertEquals(AdblockVPNService::class.java.name, componentName!!.className)
        }
    }
}