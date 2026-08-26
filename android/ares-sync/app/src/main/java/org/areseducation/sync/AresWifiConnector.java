package org.areseducation.sync;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.NetworkRequest;
import android.net.wifi.WifiNetworkSpecifier;

public final class AresWifiConnector {
    private final ConnectivityManager connectivityManager;
    private ConnectivityManager.NetworkCallback activeCallback;

    public interface Callback {
        void onAvailable(Network network);
        void onUnavailable();
        void onError(String message);
    }

    public AresWifiConnector(Context context) {
        connectivityManager = context.getSystemService(ConnectivityManager.class);
    }

    public void requestAres2(Callback callback) {
        release();

        try {
            WifiNetworkSpecifier specifier = new WifiNetworkSpecifier.Builder()
                    .setSsid("ARES2")
                    .build();

            NetworkRequest request = new NetworkRequest.Builder()
                    .addTransportType(NetworkCapabilities.TRANSPORT_WIFI)
                    .removeCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
                    .setNetworkSpecifier(specifier)
                    .build();

            activeCallback = new ConnectivityManager.NetworkCallback() {
                @Override
                public void onAvailable(Network network) {
                    callback.onAvailable(network);
                }

                @Override
                public void onUnavailable() {
                    callback.onUnavailable();
                }
            };

            connectivityManager.requestNetwork(request, activeCallback, 30000);
        } catch (SecurityException | IllegalArgumentException ex) {
            callback.onError(ex.getClass().getSimpleName() + ": " + ex.getMessage());
        }
    }

    public void release() {
        if (activeCallback == null) {
            return;
        }
        try {
            connectivityManager.unregisterNetworkCallback(activeCallback);
        } catch (IllegalArgumentException ignored) {
            // Callback had already been released by Android.
        }
        activeCallback = null;
    }
}
