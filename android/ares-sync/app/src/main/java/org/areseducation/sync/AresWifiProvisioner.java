package org.areseducation.sync;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.net.wifi.WifiManager;
import android.net.wifi.WifiNetworkSuggestion;
import android.os.Build;

import java.util.ArrayList;
import java.util.List;

public final class AresWifiProvisioner {
    static final String SSID_ARES2 = "ARES2";
    static final String SSID_ARES = "ARES";
    private static final String PREFS = "org.areseducation.sync.wifi_setup";
    private static final String KEY_SUGGESTIONS_APPROVED = "suggested_ares_networks_v1";
    private static final String APP_PACKAGE = "org.areseducation.sync";
    private static final String WIFI_SETUP_ACTIVITY = APP_PACKAGE + ".WifiSetupActivity";

    private AresWifiProvisioner() {
    }

    public static boolean isSupported() {
        return Build.VERSION.SDK_INT >= Build.VERSION_CODES.R;
    }

    public static boolean isComplete(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .getBoolean(KEY_SUGGESTIONS_APPROVED, false);
    }

    public static Intent createSaveNetworksIntent() {
        if (!isSupported()) {
            throw new IllegalStateException("Automatic Wi-Fi suggestions require Android 11 or newer.");
        }
        return new Intent().setClassName(APP_PACKAGE, WIFI_SETUP_ACTIVITY);
    }

    static int addNetworkSuggestions(Context context) {
        if (!isSupported()) {
            throw new IllegalStateException("Automatic Wi-Fi suggestions require Android 11 or newer.");
        }

        WifiManager wifiManager = context.getSystemService(WifiManager.class);
        if (wifiManager == null) {
            return WifiManager.STATUS_NETWORK_SUGGESTIONS_ERROR_INTERNAL;
        }

        return wifiManager.addNetworkSuggestions(buildSuggestions());
    }

    private static List<WifiNetworkSuggestion> buildSuggestions() {
        ArrayList<WifiNetworkSuggestion> suggestions = new ArrayList<>();
        suggestions.add(new WifiNetworkSuggestion.Builder()
                .setSsid(SSID_ARES2)
                .setIsInitialAutojoinEnabled(true)
                .build());
        suggestions.add(new WifiNetworkSuggestion.Builder()
                .setSsid(SSID_ARES)
                .setIsInitialAutojoinEnabled(true)
                .build());
        return suggestions;
    }

    static boolean submissionAccepted(int status) {
        return status == WifiManager.STATUS_NETWORK_SUGGESTIONS_SUCCESS
                || status == WifiManager.STATUS_NETWORK_SUGGESTIONS_ERROR_ADD_DUPLICATE;
    }

    public static boolean wasSaveSuccessful(int resultCode, Intent data) {
        return resultCode == Activity.RESULT_OK;
    }

    public static void setComplete(Context context, boolean complete) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit()
                .putBoolean(KEY_SUGGESTIONS_APPROVED, complete)
                .apply();
    }
}
