package com.ttt246.puppet

import android.app.Service
import android.content.Intent
import android.net.VpnService
import android.util.Log
import androidx.core.app.NotificationCompat
import java.net.Socket

open class AdblockVPNService : VpnService() {
    private val TAG = "AdblockVpnService"
    var vpnStatus: Status = Status.STOPPED
        set(value) {
            field = value
            notificationBuilder.setContentText(value.toString())
            startForeground(10, notificationBuilder.build())
        }

    private var vpnThread: AdblockVPNThread = AdblockVPNThread(this)

    private var notificationBuilder = NotificationCompat.Builder(this, "vpnChannel")
        .setSmallIcon(androidx.core.R.drawable.ic_call_decline_low)

    override fun onStartCommand(intent: Intent, flags: Int, startId: Int): Int {
        Log.i(TAG, "onStartCommand")
        when (intent.action){
            Action.START.toString() -> startVpn()
            Action.STOP.toString() -> stopVpn()
        }

        return Service.START_STICKY
    }

    private fun startVpn() {

        notificationBuilder.setContentTitle("Puppet Adblock VPN")
        vpnStatus = Status.STARTING
        restartVpnThread()
    }

    private fun restartVpnThread() {
        vpnThread.stopThread()
        vpnThread.startThread()
    }

    private fun stopVpnThread() {
        vpnThread.stopThread()
    }

    private fun stopVpn() {
        Log.i(TAG, "Stopping Service")
        stopVpnThread()
        vpnStatus = Status.STOPPED
        stopSelf()
    }

    override fun onDestroy() {
        Log.i(TAG, "Destroyed, shutting down")
        stopVpn()
    }

    enum class Action {
        START, STOP
    }

    enum class Status{
        STARTING, RUNNING, STOPPING, RECONNECTING, STOPPED
    }
}