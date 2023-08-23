package com.ttt246.puppet

import android.app.Service
import android.content.Intent
import android.net.VpnService
import android.util.Log
import androidx.core.app.NotificationCompat
import java.net.Socket

class AdblockVPNService : VpnService() {
    private val TAG = "AdblockVpnService"
    companion object {
        var vpnStatus: Status = Status.STOPPED
    }

    private var vpnThread: AdblockVPNThread = AdblockVPNThread(this) {
        updateVpnStatus(it)
    }

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

    private fun updateVpnStatus(status: Status) {
        vpnStatus = status
        notificationBuilder.setContentText(status.toString())
        startForeground(10, notificationBuilder.build())
    }

    private fun startVpn() {

        notificationBuilder.setContentTitle("Puppet Adblock VPN")
        updateVpnStatus(Status.STARTING)
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
        updateVpnStatus(Status.STOPPED)
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