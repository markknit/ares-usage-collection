package org.areseducation.sync;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.NetworkRequest;
import android.net.wifi.WifiManager;
import android.net.wifi.WifiNetworkSpecifier;
import android.os.Build;
import android.os.PatternMatcher;

public final class AresWifiConnector {
    private final Context context;
    private final ConnectivityManager connectivityManager;
    private final WifiManager wifiManager;
    private ConnectivityManager.NetworkCallback activeCallback;
    private WifiManager.LocalOnlyConnectionFailureListener failureListener;

    public interface Callback {
        void onAvailable(Network network);
        void onUnavailable();
        void onFailure(String message);
        void onError(String message);
    }

    public AresWifiConnector(Context context) {
        this.context = context;
        connectivityManager = context.getSystemService(ConnectivityManager.class);
        wifiManager = context.getSystemService(WifiManager.class);
    }

    public String getDiagnostics() {
        StringBuilder result = new StringBuilder();
        result.append("Android API: ").append(Build.VERSION.SDK_INT).append("\n");
        result.append("Wi-Fi enabled: ").append(wifiManager != null && wifiManager.isWifiEnabled());
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && wifiManager != null) {
            result.append("\nConcurrent local-only Wi-Fi: ")
                    .append(wifiManager.isStaConcurrencyForLocalOnlyConnectionsSupported());
        } else {
            result.append("\nConcurrent local-only Wi-Fi: unavailable on this Android version");
        }
        result.append("\nDiagnostic network match: ARES*");
        return result.toString();
    }

    public void requestAres2(Callback callback) {
        release();

        try {
            WifiNetworkSpecifier specifier = new WifiNetworkSpecifier.Builder()
                    .setSsidPattern(new PatternMatcher("ARES", PatternMatcher.PATTERN_PREFIX))
                    .build();

            NetworkRequest request = new NetworkRequest.Builder()
                    .addTransportType(NetworkCapabilities.TRANSPORT_WIFI)
                    .removeCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
                    .setNetworkSpecifier(specifier)
                    .build();

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE && wifiManager != null) {
                failureListener = (failedSpecifier, failureReason) ->
                        callback.onFailure(describeFailure(failureReason));
                wifiManager.addLocalOnlyConnectionFailureListener(
                        context.getMainExecutor(), failureListener);
            }

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
        } catch (SecurityException | IllegalArgumentException | IllegalStateException ex) {
            callback.onError(ex.getClass().getSimpleName() + ": " + ex.getMessage());
        }
    }

    private String describeFailure(int reason) {
        if (reason == WifiManager.STATUS_LOCAL_ONLY_CONNECTION_FAILURE_ASSOCIATION) {
            return "Association failure";
        }
        if (reason == WifiManager.STATUS_LOCAL_ONLY_CONNECTION_FAILURE_AUTHENTICATION) {
            return "Authentication failure";
        }
        if (reason == WifiManager.STATUS_LOCAL_ONLY_CONNECTION_FAILURE_IP_PROVISIONING) {
            return "IP provisioning failure";
        }
        if (reason == WifiManager.STATUS_LOCAL_ONLY_CONNECTION_FAILURE_NOT_FOUND) {
            return "Access point not found";
        }
        if (reason == WifiManager.STATUS_LOCAL_ONLY_CONNECTION_FAILURE_NO_RESPONSE) {
            return "Access point did not respond";
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.BAKLAVA
                && reason == WifiManager.STATUS_LOCAL_ONLY_CONNECTION_FAILURE_USER_REJECT) {
            return "Connection request rejected by user";
        }
        return "Unknown local-only Wi-Fi failure (code " + reason + ")";
    }

    public void release() {
        if (activeCallback != null) {
            try {
                connectivityManager.unregisterNetworkCallback(activeCallback);
            } catch (IllegalArgumentException ignored) {
                // Callback had already been released by Android.
            }
            activeCallback = null;
        }

        if (failureListener != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE
                && wifiManager != null) {
            wifiManager.removeLocalOnlyConnectionFailureListener(failureListener);
            failureListener = null;
        }
    }
}
