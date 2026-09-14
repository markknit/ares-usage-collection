package org.areseducation.sync;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.NetworkRequest;
import android.net.wifi.WifiNetworkSpecifier;
import android.os.Build;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

public final class AresWifiConnector {
    public interface RequestProgress {
        void onTrying(String ssid, boolean fallback);
    }

    private final Context context;
    private final ConnectivityManager connectivityManager;
    private ConnectivityManager.NetworkCallback activeCallback;

    public AresWifiConnector(Context context) {
        this.context = context;
        connectivityManager = context.getSystemService(ConnectivityManager.class);
    }

    public Network getCurrentWifiNetwork() {
        if (connectivityManager == null) {
            return null;
        }
        for (Network network : connectivityManager.getAllNetworks()) {
            NetworkCapabilities capabilities = connectivityManager.getNetworkCapabilities(network);
            if (capabilities != null && capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) {
                return network;
            }
        }
        return null;
    }

    public Network requestPreferredAresNetworkBlocking(long timeoutMillis) throws InterruptedException {
        return requestPreferredAresNetworkBlocking(timeoutMillis, null);
    }

    public Network requestPreferredAresNetworkBlocking(
            long timeoutMillis,
            RequestProgress progress) throws InterruptedException {
        if (connectivityManager == null || Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) {
            return null;
        }

        long perNetworkTimeout = Math.max(8_000L, timeoutMillis / 2L);
        if (progress != null) {
            progress.onTrying(AresWifiProvisioner.SSID_ARES2, false);
        }
        Network network = requestSpecificSsidBlocking(AresWifiProvisioner.SSID_ARES2, perNetworkTimeout);
        if (network != null) {
            return network;
        }

        close();
        if (progress != null) {
            progress.onTrying(AresWifiProvisioner.SSID_ARES, true);
        }
        return requestSpecificSsidBlocking(AresWifiProvisioner.SSID_ARES, perNetworkTimeout);
    }

    private Network requestSpecificSsidBlocking(String ssid, long timeoutMillis) throws InterruptedException {
        WifiNetworkSpecifier specifier = new WifiNetworkSpecifier.Builder()
                .setSsid(ssid)
                .build();

        NetworkRequest request = new NetworkRequest.Builder()
                .addTransportType(NetworkCapabilities.TRANSPORT_WIFI)
                .removeCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
                .setNetworkSpecifier(specifier)
                .build();

        CountDownLatch latch = new CountDownLatch(1);
        AtomicReference<Network> result = new AtomicReference<>();
        ConnectivityManager.NetworkCallback callback = new ConnectivityManager.NetworkCallback() {
            @Override
            public void onAvailable(Network network) {
                result.set(network);
                latch.countDown();
            }

            @Override
            public void onUnavailable() {
                latch.countDown();
            }
        };

        activeCallback = callback;
        try {
            int systemTimeout = (int) Math.min(Integer.MAX_VALUE, Math.max(1_000L, timeoutMillis));
            connectivityManager.requestNetwork(request, callback, systemTimeout);
            latch.await(timeoutMillis + 2_000L, TimeUnit.MILLISECONDS);
            Network network = result.get();
            if (network == null) {
                releaseCallback(callback);
            }
            return network;
        } catch (RuntimeException error) {
            releaseCallback(callback);
            throw error;
        }
    }

    public String getDiagnostics() {
        return "Android API: " + Build.VERSION.SDK_INT
                + "\nApp target SDK: " + context.getApplicationInfo().targetSdkVersion
                + "\nConnection mode: Wi-Fi suggestions plus app-specific local network request"
                + "\nAccepted school networks: ARES2 or ARES";
    }

    public void close() {
        ConnectivityManager.NetworkCallback callback = activeCallback;
        if (callback != null) {
            releaseCallback(callback);
        }
    }

    private void releaseCallback(ConnectivityManager.NetworkCallback callback) {
        if (connectivityManager != null) {
            try {
                connectivityManager.unregisterNetworkCallback(callback);
            } catch (RuntimeException ignored) {
            }
        }
        if (activeCallback == callback) {
            activeCallback = null;
        }
    }
}
