package org.areseducation.sync;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.Build;

public final class AresWifiConnector {
    private final Context context;
    private final ConnectivityManager connectivityManager;

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

    public String getDiagnostics() {
        return "Android API: " + Build.VERSION.SDK_INT
                + "\nApp target SDK: " + context.getApplicationInfo().targetSdkVersion
                + "\nConnection mode: teacher-assisted Wi-Fi selection"
                + "\nAccepted school networks: ARES2 or ARES";
    }

    public void close() {
        // No app-controlled Wi-Fi request is held in the guided-handoff design.
    }
}
