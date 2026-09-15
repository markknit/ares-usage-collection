package org.areseducation.sync;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.pm.PackageManager;
import android.content.res.ColorStateList;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Network;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class WifiSetupActivity extends Activity {
    private static final int LOCAL_WIFI_PERMISSION_REQUEST = 2002;
    private static final String UI_PREFS = "org.areseducation.sync.ui";
    private static final String KEY_APPEARANCE = "appearance";

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private WifiManager wifiManager;
    private WifiManager.SuggestionUserApprovalStatusListener approvalListener;
    private TextView bodyText;
    private Button retryButton;
    private Button laterButton;
    private boolean suggestionSubmitted;
    private boolean sawSystemDialogFocusLoss;
    private boolean localRequestRunning;
    private boolean finished;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setResult(Activity.RESULT_CANCELED);
        setContentView(createSetupView());

        wifiManager = getSystemService(WifiManager.class);
        if (wifiManager == null || !AresWifiProvisioner.isSupported()) {
            showFailure("Automatic ARES Wi-Fi setup is not available on this phone. Use the normal Wi-Fi screen to connect to ARES or ARES2 when needed.");
            return;
        }

        if (AresWifiProvisioner.areSuggestionsApproved(this)) {
            bodyText.setText("ARES and ARES2 suggestions are already approved. ARES Sync will now check both school Wi-Fi names and prepare direct local access for scheduled collections.");
            handler.postDelayed(this::beginLocalNetworkSetup, 300L);
        } else {
            bodyText.setText("Android will ask once whether ARES Sync may suggest Wi-Fi networks. Choose Allow. After that, ARES Sync will check both ARES and ARES2 for direct school access.");
            handler.postDelayed(this::beginSuggestionSetup, 350L);
        }
    }

    @Override
    protected void onDestroy() {
        if (wifiManager != null && approvalListener != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            try {
                wifiManager.removeSuggestionUserApprovalStatusListener(approvalListener);
            } catch (RuntimeException ignored) {
            }
        }
        handler.removeCallbacksAndMessages(null);
        executor.shutdownNow();
        super.onDestroy();
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (finished || Build.VERSION.SDK_INT != Build.VERSION_CODES.R || !suggestionSubmitted) {
            return;
        }
        if (!hasFocus) {
            sawSystemDialogFocusLoss = true;
            return;
        }
        if (sawSystemDialogFocusLoss) {
            handler.postDelayed(this::verifyAndroid11Approval, 250L);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != LOCAL_WIFI_PERMISSION_REQUEST) {
            return;
        }
        if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            startLocalNetworkAuthorization();
        } else {
            AresWifiProvisioner.setLocalNetworkReady(this, false);
            showFailure("ARES Sync needs Nearby Wi-Fi access to reach ARES or ARES2 when another Wi-Fi network has internet. Allow the permission to finish automatic setup, or use manual Wi-Fi when a collection is due.");
        }
    }

    private void beginSuggestionSetup() {
        if (finished) return;
        hideActionButtons();
        int status;
        try {
            status = AresWifiProvisioner.addNetworkSuggestions(this);
        } catch (SecurityException error) {
            showFailure("Android blocked automatic Wi-Fi setup. Use the normal Wi-Fi screen to connect to ARES or ARES2 when needed.");
            return;
        } catch (RuntimeException error) {
            showFailure("Android could not start automatic ARES Wi-Fi setup. You can try again or connect to ARES or ARES2 manually.");
            return;
        }
        if (status == WifiManager.STATUS_NETWORK_SUGGESTIONS_ERROR_APP_DISALLOWED) {
            AresWifiProvisioner.setSuggestionsApproved(this, false);
            showFailure("Automatic Wi-Fi access is turned off for ARES Sync. You can connect to ARES or ARES2 manually, or enable ARES Sync later under Android's special Wi-Fi control settings.");
            return;
        }
        if (!AresWifiProvisioner.submissionAccepted(status)) {
            showFailure("Android could not register the ARES Wi-Fi networks (status " + status + "). You can try again or connect manually.");
            return;
        }
        suggestionSubmitted = true;
        bodyText.setText("ARES and ARES2 have been submitted to Android. If Android asks whether ARES Sync may suggest Wi-Fi networks, choose Allow. Setup will continue automatically afterward.");
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            registerApprovalListener();
        } else {
            handler.postDelayed(() -> {
                if (!finished && hasWindowFocus() && !sawSystemDialogFocusLoss) verifyAndroid11Approval();
            }, 1200L);
        }
    }

    private void registerApprovalListener() {
        if (approvalListener != null || wifiManager == null) return;
        approvalListener = status -> {
            if (finished) return;
            if (status == WifiManager.STATUS_SUGGESTION_APPROVAL_APPROVED_BY_USER
                    || status == WifiManager.STATUS_SUGGESTION_APPROVAL_APPROVED_BY_CARRIER_PRIVILEGE) {
                AresWifiProvisioner.setSuggestionsApproved(this, true);
                beginLocalNetworkSetup();
            } else if (status == WifiManager.STATUS_SUGGESTION_APPROVAL_REJECTED_BY_USER) {
                AresWifiProvisioner.setSuggestionsApproved(this, false);
                AresWifiProvisioner.setLocalNetworkReady(this, false);
                showFailure("Android did not allow ARES Sync to suggest Wi-Fi networks. You can connect to ARES or ARES2 manually, or enable ARES Sync later under Android's special Wi-Fi control settings.");
            }
        };
        try {
            wifiManager.addSuggestionUserApprovalStatusListener(getMainExecutor(), approvalListener);
        } catch (RuntimeException error) {
            showFailure("Android could not confirm Wi-Fi approval. You can connect to ARES or ARES2 manually and try automatic setup again later.");
        }
    }

    private void verifyAndroid11Approval() {
        if (finished) return;
        int status;
        try {
            status = AresWifiProvisioner.addNetworkSuggestions(this);
        } catch (RuntimeException error) {
            showFailure("Android could not confirm automatic Wi-Fi setup. You can connect to ARES or ARES2 manually.");
            return;
        }
        if (status == WifiManager.STATUS_NETWORK_SUGGESTIONS_ERROR_APP_DISALLOWED) {
            AresWifiProvisioner.setSuggestionsApproved(this, false);
            showFailure("Android did not allow ARES Sync to suggest Wi-Fi networks. You can connect manually or enable ARES Sync later under Android's special Wi-Fi control settings.");
        } else if (AresWifiProvisioner.submissionAccepted(status)) {
            AresWifiProvisioner.setSuggestionsApproved(this, true);
            beginLocalNetworkSetup();
        } else {
            showFailure("Android could not confirm automatic ARES Wi-Fi setup (status " + status + "). You can connect manually.");
        }
    }

    private void beginLocalNetworkSetup() {
        if (finished) return;
        if (AresWifiProvisioner.isLocalNetworkReady(this)) {
            finishSuccessful("Automatic ARES Wi-Fi setup is already complete.");
            return;
        }
        hideActionButtons();
        String permission = localWifiPermission();
        if (checkSelfPermission(permission) != PackageManager.PERMISSION_GRANTED) {
            bodyText.setText(Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU
                    ? "One more one-time permission is needed. Allow Nearby Wi-Fi devices so ARES Sync can reach ARES or ARES2 for a scheduled collection without taking over your normal internet connection."
                    : "One more one-time Android permission is needed for direct school Wi-Fi access. On this Android version the system labels that Wi-Fi permission as Location.");
            requestPermissions(new String[]{permission}, LOCAL_WIFI_PERMISSION_REQUEST);
            return;
        }
        startLocalNetworkAuthorization();
    }

    private String localWifiPermission() {
        return Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU
                ? Manifest.permission.NEARBY_WIFI_DEVICES
                : Manifest.permission.ACCESS_FINE_LOCATION;
    }

    private void startLocalNetworkAuthorization() {
        if (finished || localRequestRunning) return;
        localRequestRunning = true;
        hideActionButtons();
        bodyText.setText("Checking both school Wi-Fi names. ARES Sync will try ARES first and then ARES2. Please wait; no action is needed unless Android asks you to approve a network.");

        executor.execute(() -> {
            List<String> successful = new ArrayList<>();
            String firstSuccessful = null;
            String lastError = null;
            String[] ssids = {AresWifiProvisioner.SSID_ARES, AresWifiProvisioner.SSID_ARES2};

            for (int i = 0; i < ssids.length; i++) {
                String ssid = ssids[i];
                int step = i + 1;
                runOnUiThread(() -> bodyText.setText("Checking " + ssid + " (" + step + " of 2). Android may show a one-time network approval. Setup will continue automatically afterward."));
                AresWifiConnector connector = new AresWifiConnector(WifiSetupActivity.this);
                try {
                    Network network = connector.requestSpecificAresNetworkBlocking(ssid, 20_000L);
                    if (network == null) continue;
                    runOnUiThread(() -> bodyText.setText(ssid + " connected successfully. Verifying the school server before continuing..."));
                    AresServerClient.probeBlocking(network);
                    successful.add(ssid);
                    if (firstSuccessful == null) firstSuccessful = ssid;
                } catch (SecurityException error) {
                    lastError = "Android blocked the direct " + ssid + " request.";
                } catch (InterruptedException error) {
                    Thread.currentThread().interrupt();
                    lastError = "The " + ssid + " request was interrupted.";
                    break;
                } catch (Exception error) {
                    lastError = ssid + " connected but ares.local could not be reached: " + error.getMessage();
                } finally {
                    connector.close();
                }
            }

            final String preferred = firstSuccessful;
            final String errorText = lastError;
            runOnUiThread(() -> {
                localRequestRunning = false;
                if (preferred != null) {
                    AresWifiProvisioner.setPreferredLocalSsid(WifiSetupActivity.this, preferred);
                    String checked = successful.size() == 2 ? "ARES and ARES2" : successful.get(0);
                    finishSuccessful("Automatic ARES Wi-Fi setup succeeded. " + checked + " reached the school server and ARES Sync is ready for scheduled collections.");
                } else {
                    AresWifiProvisioner.setLocalNetworkReady(WifiSetupActivity.this, false);
                    showFailure("ARES Sync could not verify either ARES or ARES2. Make sure at least one school network is in range, then try again."
                            + (errorText == null ? "" : "\n\nTechnical details: " + errorText));
                }
            });
        });
    }

    private void finishSuccessful(String message) {
        if (finished) return;
        finished = true;
        AresWifiProvisioner.setLocalNetworkReady(this, true);
        setResult(Activity.RESULT_OK);
        bodyText.setText(message + "\n\nReturning to ARES Sync...");
        hideActionButtons();
        handler.postDelayed(this::finish, 1200L);
    }

    private void showFailure(String message) {
        if (finished) return;
        bodyText.setText(message);
        retryButton.setVisibility(View.VISIBLE);
        laterButton.setVisibility(View.VISIBLE);
    }

    private void hideActionButtons() {
        retryButton.setVisibility(View.GONE);
        laterButton.setVisibility(View.GONE);
    }

    private void retrySetup() {
        if (AresWifiProvisioner.areSuggestionsApproved(this)) beginLocalNetworkSetup();
        else beginSuggestionSetup();
    }

    private LinearLayout createSetupView() {
        float density = getResources().getDisplayMetrics().density;
        int sidePadding = Math.round(24f * density);
        int topPadding = Math.round(42f * density);
        int spacing = Math.round(18f * density);
        SetupColors colors = SetupColors.current(this);

        LinearLayout root = new LinearLayout(this);
        root.setLayoutParams(new ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.TOP);
        root.setPadding(sidePadding, topPadding, sidePadding, sidePadding);
        root.setBackgroundColor(colors.background);

        TextView title = new TextView(this);
        title.setText("Enable automatic ARES Wi-Fi");
        title.setTextSize(24f);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setTextColor(colors.accent);
        root.addView(title, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        bodyText = new TextView(this);
        bodyText.setText("Preparing Android's automatic Wi-Fi approval...");
        bodyText.setTextSize(17f);
        bodyText.setLineSpacing(0f, 1.15f);
        bodyText.setTextColor(colors.text);
        LinearLayout.LayoutParams bodyParams = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        bodyParams.topMargin = spacing;
        root.addView(bodyText, bodyParams);

        retryButton = new Button(this);
        retryButton.setText("Try automatic Wi-Fi setup again");
        retryButton.setMinHeight(Math.round(56f * density));
        retryButton.setVisibility(View.GONE);
        retryButton.setTextColor(colors.buttonText);
        retryButton.setBackgroundTintList(ColorStateList.valueOf(colors.accent));
        retryButton.setOnClickListener(view -> retrySetup());
        LinearLayout.LayoutParams retryParams = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        retryParams.topMargin = spacing;
        root.addView(retryButton, retryParams);

        laterButton = new Button(this);
        laterButton.setText("Use manual Wi-Fi instead");
        laterButton.setVisibility(View.GONE);
        laterButton.setTextColor(colors.buttonText);
        laterButton.setBackgroundTintList(ColorStateList.valueOf(colors.accent));
        laterButton.setOnClickListener(view -> finish());
        LinearLayout.LayoutParams laterParams = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        laterParams.topMargin = Math.round(10f * density);
        root.addView(laterButton, laterParams);
        return root;
    }

    private static final class SetupColors {
        final int background;
        final int text;
        final int accent;
        final int buttonText;

        SetupColors(int background, int text, int accent, int buttonText) {
            this.background = background;
            this.text = text;
            this.accent = accent;
            this.buttonText = buttonText;
        }

        static SetupColors current(Context context) {
            String appearance = context.getSharedPreferences(UI_PREFS, Context.MODE_PRIVATE)
                    .getString(KEY_APPEARANCE, null);
            if (appearance == null || appearance.isEmpty()) {
                int nightMode = context.getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK;
                appearance = nightMode == Configuration.UI_MODE_NIGHT_YES ? "dark" : "warm";
            }
            if ("dark".equals(appearance)) {
                return new SetupColors(Color.rgb(14, 18, 23), Color.rgb(248, 250, 252), Color.rgb(110, 205, 255), Color.BLACK);
            }
            if ("blue".equals(appearance)) {
                return new SetupColors(Color.rgb(235, 245, 251), Color.rgb(26, 43, 54), Color.rgb(12, 104, 153), Color.WHITE);
            }
            if ("light".equals(appearance)) {
                return new SetupColors(Color.rgb(244, 247, 249), Color.rgb(30, 39, 46), Color.rgb(18, 108, 150), Color.WHITE);
            }
            return new SetupColors(Color.rgb(249, 245, 235), Color.rgb(40, 36, 30), Color.rgb(27, 102, 132), Color.WHITE);
        }
    }
}
