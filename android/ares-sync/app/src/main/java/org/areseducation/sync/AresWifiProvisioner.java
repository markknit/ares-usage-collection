package org.areseducation.sync;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.net.wifi.WifiNetworkSuggestion;
import android.os.Build;
import android.provider.Settings;

import java.util.ArrayList;

public final class AresWifiProvisioner {
    private static final String PREFS = "org.areseducation.sync.wifi_setup";
    private static final String KEY_SAVED_NETWORKS = "saved_ares_networks";

    private AresWifiProvisioner() {
    }

    public static boolean isSupported() {
        return Build.VERSION.SDK_INT >= Build.VERSION_CODES.R;
    }

    public static boolean isComplete(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .getBoolean(KEY_SAVED_NETWORKS, false);
    }

    public static Intent createSaveNetworksIntent() {
        if (!isSupported()) {
            throw new IllegalStateException("Saved-network setup requires Android 11 or newer.");
        }

        ArrayList<WifiNetworkSuggestion> networks = new ArrayList<>();
        networks.add(new WifiNetworkSuggestion.Builder()
                .setSsid("ARES2")
                .setIsInitialAutojoinEnabled(true)
                .build());
        networks.add(new WifiNetworkSuggestion.Builder()
                .setSsid("ARES")
                .setIsInitialAutojoinEnabled(true)
                .build());

        Intent intent = new Intent(Settings.ACTION_WIFI_ADD_NETWORKS);
        intent.putParcelableArrayListExtra(Settings.EXTRA_WIFI_NETWORK_LIST, networks);
        return intent;
    }

    public static boolean wasSaveSuccessful(int resultCode, Intent data) {
        if (resultCode != Activity.RESULT_OK) {
            return false;
        }

        if (data == null) {
            return true;
        }

        ArrayList<Integer> results = data.getIntegerArrayListExtra(
                Settings.EXTRA_WIFI_NETWORK_RESULT_LIST);
        if (results == null || results.isEmpty()) {
            return true;
        }

        for (int result : results) {
            if (result != Settings.ADD_WIFI_RESULT_SUCCESS
                    && result != Settings.ADD_WIFI_RESULT_ALREADY_EXISTS) {
                return false;
            }
        }
        return true;
    }

    public static void setComplete(Context context, boolean complete) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit()
                .putBoolean(KEY_SAVED_NETWORKS, complete)
                .apply();
    }
}
