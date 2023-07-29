package com.ttt246.puppet
import android.content.Context
import androidx.test.core.app.ApplicationProvider
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.junit.runner.RunWith
import org.junit.Test
import org.junit.Before
import org.mockito.Mockito

class TestablePuppetAS : PuppetAS() {
    fun attachBaseContextPublic(context: Context) {
        attachBaseContext(context)
    }
}


@RunWith(RobolectricTestRunner::class)
@Config(sdk = [Config.OLDEST_SDK])
class PuppetASTest {
    private lateinit var puppetService: TestablePuppetAS

    @Before
    fun setUp() {
        puppetService = Mockito.spy(TestablePuppetAS())
        val context = ApplicationProvider.getApplicationContext<Context>()
        puppetService.attachBaseContextPublic(context)
    }

    @Test
    fun processCommands_executesIntentCommands() {
        val command = "intent:test"
        puppetService.processCommands(listOf(command))
        Mockito.verify(puppetService).executeIntentCommand("intent:test")
    }

    @Test
    fun processCommands_executesAccCommands() {
        val command = "acc:UP"
        puppetService.processCommands(listOf(command))

        Mockito.verify(puppetService).executeAccCommand(command)
    }
}
