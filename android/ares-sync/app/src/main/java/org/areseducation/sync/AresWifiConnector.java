package org.areseducation.sync;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.wifi.WifiConfiguration;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.os.Build;

import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@SuppressWarnings("deprecation")
public final class AresWifiConnector {
    private static final String ARES_SSID = "ARES2";
    private static final long SWITCH_TIMEOUT_MS = 30000L;
    private static final long POLL_INTERVAL_MS = 500L;

    private final Context context;
    private final ConnectivityManager connectivityManager;
    private final WifiManager wifiManager;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    private volatile int previousNetworkId = -1;
    private volatile String previousSsid = "unknown";
    private volatile int aresNetworkId = -1;
    private volatile boolean previousNetworkDisabled = false;
    private volatile String lastLegacyResults = "not run";

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
        result.append("App target SDK: ").append(context.getApplicationInfo().targetSdkVersion).append("\n");
        result.append("Wi-Fi enabled: ").append(wifiManager != null && wifiManager.isWifiEnabled()).append("\n");
        result.append("Connection mode under test: API 28 forced prior-network disable\n");
        result.append("Current SSID: ").append(getCurrentSsid()).append("\n");
        result.append("Previous SSID: ").append(previousSsid).append("\n");
        result.append("ARES2 network id: ").append(aresNetworkId).append("\n");
        result.append("Legacy API results: ").append(lastLegacyResults);
        return result.toString();
    }

    public String getCurrentSsid() {
        if (wifiManager == null) {
            return "Wi-Fi manager unavailable";
        }
        try {
            WifiInfo info = wifiManager.getConnectionInfo();
            return normalizeSsid(info == null ? null : info.getSSID());
        } catch (SecurityException ex) {
            return "permission unavailable";
        }
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

    public void requestAres2(Callback callback) {
        executor.execute(() -> performLegacySwitch(callback));
    }

    private void performLegacySwitch(Callback callback) {
        if (wifiManager == null || connectivityManager == null) {
            callback.onError("Wi-Fi or connectivity service is unavailable.");
            return;
        }

        try {
            if (!wifiManager.isWifiEnabled()) {
                callback.onError("Wi-Fi is disabled. Enable Wi-Fi before running this test.");
                return;
            }

            WifiInfo before = wifiManager.getConnectionInfo();
            previousNetworkId = before == null ? -1 : before.getNetworkId();
            previousSsid = normalizeSsid(before == null ? null : before.getSSID());
            previousNetworkDisabled = false;

            if (ARES_SSID.equals(previousSsid)) {
                aresNetworkId = previousNetworkId;
                Network network = waitForWifiNetwork(5000L);
                if (network != null) {
                    callback.onAvailable(network);
                } else {
                    callback.onFailure("Phone reports ARES2 as the current SSID, but Android did not expose its Wi-Fi Network object.");
                }
                return;
            }

            List<WifiConfiguration> configuredNetworks = wifiManager.getConfiguredNetworks();
            int configuredCount = configuredNetworks == null ? 0 : configuredNetworks.size();
            aresNetworkId = findNetworkId(configuredNetworks, ARES_SSID);

            if (aresNetworkId < 0) {
                WifiConfiguration aresConfig = new WifiConfiguration();
                aresConfig.SSID = quoteSsid(ARES_SSID);
                aresConfig.allowedKeyManagement.set(WifiConfiguration.KeyMgmt.NONE);
                aresNetworkId = wifiManager.addNetwork(aresConfig);
            }

            if (aresNetworkId < 0) {
                lastLegacyResults = "configuredNetworks=" + configuredCount
                        + ", addNetwork=-1";
                callback.onFailure("ARES2 was not available as a configured network and Android refused to add the open ARES2 configuration.\n\n"
                        + getDiagnostics());
                clearPreviousState();
                return;
            }

            String disablePreviousText = "not-applicable";
            if (previousNetworkId >= 0 && previousNetworkId != aresNetworkId) {
                previousNetworkDisabled = wifiManager.disableNetwork(previousNetworkId);
                disablePreviousText = Boolean.toString(previousNetworkDisabled);
            }

            boolean disconnectResult = wifiManager.disconnect();
            sleepQuietly(750L);
            boolean enableResult = wifiManager.enableNetwork(aresNetworkId, true);
            boolean reconnectResult = wifiManager.reconnect();

            lastLegacyResults = "configuredNetworks=" + configuredCount
                    + ", disablePrevious=" + disablePreviousText
                    + ", disconnect=" + disconnectResult
                    + ", enableNetwork=" + enableResult
                    + ", reconnect=" + reconnectResult;

            if (!enableResult) {
                restorePreviousNetwork();
                callback.onFailure("Android rejected enableNetwork(ARES2).\n\n" + getDiagnostics());
                return;
            }

            long deadline = System.currentTimeMillis() + SWITCH_TIMEOUT_MS;
            while (System.currentTimeMillis() < deadline) {
                if (ARES_SSID.equals(getCurrentSsid())) {
                    Network network = waitForWifiNetwork(8000L);
                    if (network != null) {
                        callback.onAvailable(network);
                        return;
                    }
                }
                sleepQuietly(POLL_INTERVAL_MS);
            }

            String failedDiagnostics = getDiagnostics();
            restorePreviousNetwork();
            callback.onUnavailable();
            lastLegacyResults = lastLegacyResults + "; timeout before ARES2 association\n" + failedDiagnostics;
        } catch (SecurityException ex) {
            restorePreviousNetwork();
            callback.onError("SecurityException: " + ex.getMessage());
        } catch (RuntimeException ex) {
            restorePreviousNetwork();
            callback.onError(ex.getClass().getSimpleName() + ": " + ex.getMessage());
        }
    }

    private int findNetworkId(List<WifiConfiguration> configuredNetworks, String ssid) {
        if (configuredNetworks == null) {
            return -1;
        }
        for (WifiConfiguration configuration : configuredNetworks) {
            if (configuration != null && ssid.equals(normalizeSsid(configuration.SSID))) {
                return configuration.networkId;
            }
        }
        return -1;
    }

    private Network waitForWifiNetwork(long timeoutMs) {
        long deadline = System.currentTimeMillis() + timeoutMs;
        while (System.currentTimeMillis() < deadline) {
            Network network = getCurrentWifiNetwork();
            if (network != null) {
                return network;
            }
            sleepQuietly(250L);
        }
        return null;
    }

    public synchronized void release() {
        restorePreviousNetwork();
    }

    private synchronized void restorePreviousNetwork() {
        if (wifiManager == null) {
            clearPreviousState();
            return;
        }

        if (previousNetworkId < 0 || ARES_SSID.equals(previousSsid)) {
            clearPreviousState();
            return;
        }

        try {
            boolean disconnectResult = wifiManager.disconnect();
            boolean enableResult = wifiManager.enableNetwork(previousNetworkId, true);
            boolean reconnectResult = wifiManager.reconnect();
            lastLegacyResults = lastLegacyResults
                    + "; restore(previousWasDisabled=" + previousNetworkDisabled
                    + ", disconnect=" + disconnectResult
                    + ", enableNetwork=" + enableResult
                    + ", reconnect=" + reconnectResult + ")";
        } catch (SecurityException ex) {
            lastLegacyResults = lastLegacyResults + "; restore SecurityException=" + ex.getMessage();
        } finally {
            clearPreviousState();
        }
    }

    private void clearPreviousState() {
        previousNetworkId = -1;
        previousSsid = "none";
        previousNetworkDisabled = false;
    }

    public void close() {
        release();
        executor.shutdownNow();
    }

    private static String normalizeSsid(String ssid) {
        if (ssid == null || ssid.isEmpty() || "<unknown ssid>".equalsIgnoreCase(ssid)) {
            return "unknown";
        }
        if (ssid.length() >= 2 && ssid.startsWith("\"") && ssid.endsWith("\"")) {
            return ssid.substring(1, ssid.length() - 1);
        }
        return ssid;
    }

    private static String quoteSsid(String ssid) {
        return "\"" + ssid + "\"";
    }

    private static void sleepQuietly(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
        }
    }
}
