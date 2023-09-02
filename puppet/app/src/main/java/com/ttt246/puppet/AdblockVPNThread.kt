package com.ttt246.puppet

import android.app.PendingIntent
import android.content.Intent
import android.content.SharedPreferences
import android.os.ParcelFileDescriptor
import android.system.ErrnoException
import android.system.OsConstants
import android.util.Log
import androidx.preference.PreferenceManager
import com.ttt246.puppet.AdblockVPNService.Status
import org.json.JSONObject
import org.pcap4j.packet.IpV4Packet
import org.pcap4j.packet.UdpPacket
import org.pcap4j.packet.UnknownPacket
import org.xbill.DNS.ARecord
import org.xbill.DNS.Flags
import org.xbill.DNS.Message
import org.xbill.DNS.Section
import java.io.BufferedInputStream
import java.io.FileInputStream
import java.io.FileOutputStream
import java.io.IOException
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.HttpURLConnection
import java.net.Inet4Address
import java.net.InetAddress
import java.net.URL
import java.nio.charset.StandardCharsets
import java.util.concurrent.RejectedExecutionException
import java.util.concurrent.SynchronousQueue
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit


class VpnNetworkException(msg: String) : RuntimeException(msg)

const val MIN_RETRY_TIME = 5
const val MAX_RETRY_TIME = 2*60
class AdblockVPNThread(vpnService: AdblockVPNService): Runnable {
    private val TAG = "AdVpnThread"
    private var vpnService = vpnService
    private var dnsServer: InetAddress? = null
    private var vpnFileDescriptor: ParcelFileDescriptor? = null
    private var thread: Thread? = null
    private var fileInputStream: FileInputStream? = null
    private var sharedPreferences: SharedPreferences? = null


    fun startThread() {
        Log.i(TAG, "Starting Vpn Thread")
        sharedPreferences = PreferenceManager.getDefaultSharedPreferences(vpnService.applicationContext)
        thread = Thread(this, "PuppetVPNThread").apply { start() }
        Log.i(TAG, "Vpn Thread started")
    }

    fun stopThread() {
        Log.i(TAG, "Stopping Vpn Thread")
        thread?.interrupt()
        fileInputStream?.close()
        thread?.join(2000)
        if (thread?.isAlive == true) {
            Log.w(TAG, "Couldn't kill Vpn Thread")
        }
        thread = null
        Log.i(TAG, "Vpn Thread stopped")
    }

    @Synchronized override fun run() {
        try {
            Log.i(TAG, "Starting")
            vpnService.vpnStatus = Status.STARTING

            var retryTimeout = MIN_RETRY_TIME
            // Try connecting the vpn continuously
            while (true) {
                try {
                    // If the function returns, that means it was interrupted
                    runVpn()

                    Log.i(TAG, "Told to stop")
                    break
                } catch (e: InterruptedException) {
                    throw e
                } catch (e: VpnNetworkException) {
                    // We want to filter out VpnNetworkException from out crash analytics as these
                    // are exceptions that we expect to happen from network errors
                    Log.w(TAG, "Network exception in vpn thread, ignoring and reconnecting", e)
                    // If an exception was thrown, show to the user and try again
                    vpnService.vpnStatus = Status.RECONNECTING
                } catch (e: Exception) {
                    Log.e(TAG, "Network exception in vpn thread, reconnecting", e)
                    vpnService.vpnStatus = Status.RECONNECTING
                }

                // ...wait and try again
                Log.i(TAG, "Retrying to connect in $retryTimeout seconds...")
                Thread.sleep(retryTimeout.toLong() * 1000)
                retryTimeout = if (retryTimeout < MAX_RETRY_TIME) {
                    retryTimeout * 2
                } else {
                    retryTimeout
                }
            }

            Log.i(TAG, "Stopped")
        } catch (e: InterruptedException) {
            Log.i(TAG, "Vpn Thread interrupted")
            Thread.currentThread().interrupt();
        } catch (e: Exception) {
            Log.e(TAG, "Exception in run() ", e)
        } finally {
            vpnService.vpnStatus = Status.STOPPING
            Log.i(TAG, "Exiting")
        }
    }

    @Throws(Exception::class)
    private fun runVpn() {
        // Authenticate and configure the virtual network interface.
        val pfd = configure()
        vpnFileDescriptor = pfd

        // Packets to be sent are queued in this input stream.
        val inputStream = FileInputStream(pfd.fileDescriptor)
        fileInputStream = inputStream

        // Allocate the buffer for a single packet.
        val packet = ByteArray(32767)

        // Like this `Executors.newCachedThreadPool()`, except with an upper limit
        val executor = ThreadPoolExecutor(0, 32, 60L, TimeUnit.SECONDS, SynchronousQueue<Runnable>())

        try {
            // Now we are connected. Set the flag and show the message.
            vpnService.vpnStatus = Status.RUNNING


            // We keep forwarding packets till something goes wrong.
            while (true) {
                // Read the outgoing packet from the input stream.
                val length = try {
                    inputStream.read(packet)
                } catch (e: Exception) {
                    Log.e(TAG, "Told to stop VPN")
                    e.printStackTrace()
                    return
                }

                if (length == 0) {
                    Log.w(TAG, "Got empty packet!")
                }

                val readPacket = packet.copyOfRange(0, length)

                // Packets received need to be written to this output stream.
                val outFd = FileOutputStream(pfd.fileDescriptor)

                // Packets to be sent to the real DNS server will need to be protected from the VPN
                val dnsSocket = DatagramSocket()

                Log.i(TAG, "Starting new thread to handle dns request" +
                        " (active = ${executor.activeCount} backlog = ${executor.queue.size})")
                // Start a new thread to handle the DNS request
                try {
                    executor.execute {
                        handleDnsRequest(readPacket, dnsSocket, outFd)
                    }
                } catch (e: RejectedExecutionException) {
                    VpnNetworkException("High backlog in dns thread pool executor, network probably stalled")
                }
            }
        } finally {
            executor.shutdownNow()
            pfd.close()
            vpnFileDescriptor = null
        }
    }

    private fun sendPuppetRequest(domain: String, uid: String, host: String): Boolean{
        var allowed: Boolean = true
        var modifiedHost: String = host

        if(host.contains("hf.space")){
            if (!host.endsWith("/")){
                modifiedHost += "/"
            }
            modifiedHost+="api/predict"
        }
        val url = URL(modifiedHost)
        val con = url.openConnection() as HttpURLConnection
        con.requestMethod = "POST";
        con.setRequestProperty("Content-Type", "application/json");
        con.doOutput = true;

        val jsonInputString = "{\"data\":[\"$uid\", \"$domain\", \"falcon\"],\"event_data\":null,\"fn_index\":20,\"session_hash\":\"ccomaehgo0q\"}"
        con.outputStream.use { os ->
            val input = jsonInputString.toByteArray(charset("utf-8"))
            os.write(input, 0, input.size)
        }
        Log.i(TAG, "Server response from puppet:")

        val inputStream = con.inputStream
        val bufferedInputStream = BufferedInputStream(inputStream)
        val buffer = ByteArray(4096) // or any other appropriate size

        var bytesRead: Int
        val responseBuilder = StringBuilder()

        while (bufferedInputStream.read(buffer).also { bytesRead = it } != -1) {
            val chunk = String(buffer, 0, bytesRead, StandardCharsets.UTF_8)
            responseBuilder.append(chunk)
        }

        var res: String = responseBuilder.toString()
        Log.i(TAG, res)
        val data= Regex("(?<=\\[)(.*\\n?)(?=\\])").find(res)
        if(data != null) {
            Log.i(TAG, "regex match: " + data.value)
            val jsonData = JSONObject(data.value)
            allowed = jsonData.getBoolean("allow")
        }
        bufferedInputStream.close()
        inputStream.close()

        return allowed
    }

    private fun handleDnsRequest(packet: ByteArray, dnsSocket: DatagramSocket, outFd: FileOutputStream) {
        try {
            val parsedPacket = IpV4Packet.newPacket(packet, 0, packet.size)

            if (parsedPacket.payload !is UdpPacket) {
                Log.i(TAG, "Ignoring unknown packet")
                return
            }

            val dnsRawData = (parsedPacket.payload as UdpPacket).payload.rawData
            val dnsMsg = Message(dnsRawData)
            if (dnsMsg.question == null) {
                Log.i(TAG, "Ignoring DNS packet with no query $dnsMsg")
                return
            }
            val dnsQueryName = dnsMsg.question.name.toString(true)

            val response: ByteArray

            val host: String = sharedPreferences?.getString("SERVER_URL", "http://172.17.0.1:7860")!!
            val uid: String = sharedPreferences?.getString("UUID", "")!!

            var allowed: Boolean = sendPuppetRequest(dnsQueryName, uid, host)

            if(allowed){
                Log.i(TAG, "DNS Name $dnsQueryName Allowed!")
                val outPacket = DatagramPacket(dnsRawData, 0, dnsRawData.size, dnsServer!!, 53)

                try {
                    dnsSocket.send(outPacket)
                } catch (e: ErrnoException) {
                    if ((e.errno == OsConstants.ENETUNREACH) || (e.errno == OsConstants.EPERM)) {
                        throw VpnNetworkException("Network unreachable, can't send DNS packet")
                    } else {
                        throw e
                    }
                }

                val datagramData = ByteArray(1024)
                val replyPacket = DatagramPacket(datagramData, datagramData.size)
                dnsSocket.receive(replyPacket)
                response = datagramData
            } else {
                Log.i(TAG, "DNS Name $dnsQueryName Blocked!")
                dnsMsg.header.setFlag(Flags.QR.toInt())
                dnsMsg.addRecord(ARecord(dnsMsg.question.name,
                    dnsMsg.question.dClass,
                    10.toLong(),
                    Inet4Address.getLocalHost()), Section.ANSWER)
                response = dnsMsg.toWire()
            }


            val udpOutPacket = parsedPacket.payload as UdpPacket
            val ipOutPacket = IpV4Packet.Builder(parsedPacket)
                .srcAddr(parsedPacket.header.dstAddr)
                .dstAddr(parsedPacket.header.srcAddr)
                .correctChecksumAtBuild(true)
                .correctLengthAtBuild(true)
                .payloadBuilder(
                    UdpPacket.Builder(udpOutPacket)
                        .srcPort(udpOutPacket.header.dstPort)
                        .dstPort(udpOutPacket.header.srcPort)
                        .srcAddr(parsedPacket.header.dstAddr)
                        .dstAddr(parsedPacket.header.srcAddr)
                        .correctChecksumAtBuild(true)
                        .correctLengthAtBuild(true)
                        .payloadBuilder(
                            UnknownPacket.Builder()
                                .rawData(response)
                        )
                ).build()
            try {
                outFd.write(ipOutPacket.rawData)
            } catch (e: ErrnoException) {
                if (e.errno == OsConstants.EBADF) {
                    throw VpnNetworkException("Outgoing VPN socket closed")
                } else {
                    throw e
                }
            } catch (e: IOException) {
                throw VpnNetworkException("Outgoing VPN output stream closed")
            }
        } catch (e: VpnNetworkException) {
            Log.w(TAG, "Ignoring exception, stopping thread", e)
        } catch (e: Exception) {
            Log.e(TAG, "Got exception: " + e.printStackTrace(), e)
        } finally {
            dnsSocket.close()
            outFd.close()
        }

    }

    @Throws(Exception::class)
    private fun configure(): ParcelFileDescriptor {

        Log.i(TAG, "Configuring")

        dnsServer = InetAddress.getByName("1.1.1.1")
        Log.i(TAG, "Got DNS server = $dnsServer")

        // Configure a builder while parsing the parameters.
        val builder = vpnService.Builder()
            .addAddress("192.168.50.1", 24)
            .addDnsServer("192.168.50.5")
            .addRoute("192.168.50.0", 24)
            .setBlocking(true)
            .allowBypass()
            .addDisallowedApplication(BuildConfig.APPLICATION_ID)

        // Create a new interface using the builder and save the parameters.
        val pfd = builder
            .setSession(TAG)
            .setConfigureIntent(
                PendingIntent.getActivity(vpnService, 1, Intent(vpnService, ChatterAct::class.java),
                    PendingIntent.FLAG_CANCEL_CURRENT)
            ).establish()
        Log.i(TAG, "Configured")
        return pfd!!
    }

}