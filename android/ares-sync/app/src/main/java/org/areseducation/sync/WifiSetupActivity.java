package org.areseducation.sync;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
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

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class WifiSetupActivity extends Activity {
    private static final int LOCAL_WIFI_PERMISSION_REQUEST = 2002;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private WifiManager wifiManager;
    private WifiManager.SuggestionUserApprovalStatusListener approvalListener;
    private TextView bodyText;
    private Button retryButton;
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
            bodyText.setText("ARES and ARES2 suggestions are already approved. ARES Sync will now prepare a direct local connection for scheduled collections even when another Wi-Fi network has internet access.");
            handler.postDelayed(this::beginLocalNetworkSetup, 300L);
        } else {
            bodyText.setText("Android will ask once whether ARES Sync may suggest Wi-Fi networks. Choose Allow. After that, ARES Sync will prepare direct access to the school network for scheduled collections.");
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
            showFailure("ARES Sync needs Nearby Wi-Fi access to request the school network directly when another Wi-Fi network has internet. Allow the permission to finish automatic setup, or use manual Wi-Fi when a collection is due.");
        }
    }

    private void beginSuggestionSetup() {
        if (finished) {
            return;
        }

        retryButton.setVisibility(View.GONE);
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
        bodyText.setText("ARES and ARES2 have been submitted to Android. If Android asks whether ARES Sync may suggest Wi-Fi networks, choose Allow.");

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            registerApprovalListener();
        } else {
            handler.postDelayed(() -> {
                if (!finished && hasWindowFocus() && !sawSystemDialogFocusLoss) {
                    verifyAndroid11Approval();
                }
            }, 1200L);
        }
    }

    private void registerApprovalListener() {
        if (approvalListener != null || wifiManager == null) {
            return;
        }

        approvalListener = status -> {
            if (finished) {
                return;
            }
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
            wifiManager.addSuggestionUserApprovalStatusListener(
                    getMainExecutor(),
                    approvalListener);
        } catch (RuntimeException error) {
            showFailure("Android could not confirm Wi-Fi approval. You can connect to ARES or ARES2 manually and try automatic setup again later.");
        }
    }

    private void verifyAndroid11Approval() {
        if (finished) {
            return;
        }

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
        if (finished) {
            return;
        }
        if (AresWifiProvisioner.isLocalNetworkReady(this)) {
            finishSuccessful();
            return;
        }

        retryButton.setVisibility(View.GONE);
        String permission = localWifiPermission();
        if (checkSelfPermission(permission) != PackageManager.PERMISSION_GRANTED) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                bodyText.setText("One more one-time permission is needed. Allow Nearby Wi-Fi devices so ARES Sync can reach ARES or ARES2 for a scheduled collection without taking over your normal internet connection.");
            } else {
                bodyText.setText("One more one-time Android permission is needed for direct school Wi-Fi access. On this Android version the system labels that Wi-Fi permission as Location.");
            }
            requestPermissions(new String[]{permission}, LOCAL_WIFI_PERMISSION_REQUEST);
            return;
        }

        startLocalNetworkAuthorization();
    }

    private String localWifiPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            return Manifest.permission.NEARBY_WIFI_DEVICES;
        }
        return Manifest.permission.ACCESS_FINE_LOCATION;
    }

    private void startLocalNetworkAuthorization() {
        if (finished || localRequestRunning) {
            return;
        }

        localRequestRunning = true;
        retryButton.setVisibility(View.GONE);
        bodyText.setText("Preparing direct access to the school server. Android may ask you to approve a connection to ARES2 or ARES. Keep your normal internet Wi-Fi saved; this request is only for ARES Sync's local collection traffic.");

        executor.execute(() -> {
            AresWifiConnector connector = new AresWifiConnector(WifiSetupActivity.this);
            try {
                Network network = connector.requestPreferredAresNetworkBlocking(60_000L);
                if (network == null) {
                    runOnUiThread(() -> {
                        localRequestRunning = false;
                        AresWifiProvisioner.setLocalNetworkReady(WifiSetupActivity.this, false);
                        showFailure("ARES Sync could not obtain a direct ARES Wi-Fi connection. Make sure ARES2 or ARES is in range, then try again. Your normal internet Wi-Fi can remain saved and connected.");
                    });
                    return;
                }

                AresServerClient.probeBlocking(network);
                runOnUiThread(() -> {
                    localRequestRunning = false;
                    AresWifiProvisioner.setLocalNetworkReady(WifiSetupActivity.this, true);
                    bodyText.setText("ARES local access is ready. ARES Sync reached the school server through its direct local connection.");
                    handler.postDelayed(this::finishSuccessful, 500L);
                });
            } catch (SecurityException error) {
                runOnUiThread(() -> {
                    localRequestRunning = false;
                    AresWifiProvisioner.setLocalNetworkReady(WifiSetupActivity.this, false);
                    showFailure("Android blocked the direct ARES Wi-Fi request. Allow Nearby Wi-Fi access and try again.");
                });
            } catch (InterruptedException error) {
                Thread.currentThread().interrupt();
                runOnUiThread(() -> {
                    localRequestRunning = false;
                    AresWifiProvisioner.setLocalNetworkReady(WifiSetupActivity.this, false);
                    showFailure("The direct ARES Wi-Fi request was interrupted. Try again while ARES2 or ARES is in range.");
                });
            } catch (Exception error) {
                runOnUiThread(() -> {
                    localRequestRunning = false;
                    AresWifiProvisioner.setLocalNetworkReady(WifiSetupActivity.this, false);
                    showFailure("ARES Sync connected to the requested school Wi-Fi but could not reach ares.local. Make sure the school server is running and try again.\n\nTechnical details: " + error.getMessage());
                });
            } finally {
                connector.close();
            }
        });
    }

    private void finishSuccessful() {
        if (finished) {
            return;
        }
        finished = true;
        setResult(Activity.RESULT_OK);
        finish();
    }

    private void showFailure(String message) {
        if (finished) {
            return;
        }
        bodyText.setText(message);
        retryButton.setVisibility(View.VISIBLE);
    }

    private void retrySetup() {
        if (AresWifiProvisioner.areSuggestionsApproved(this)) {
            beginLocalNetworkSetup();
        } else {
            beginSuggestionSetup();
        }
    }

    private LinearLayout createSetupView() {
        float density = getResources().getDisplayMetrics().density;
        int sidePadding = Math.round(24f * density);
        int topPadding = Math.round(42f * density);
        int spacing = Math.round(18f * density);

        LinearLayout root = new LinearLayout(this);
        root.setLayoutParams(new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.TOP);
        root.setPadding(sidePadding, topPadding, sidePadding, sidePadding);

        TextView title = new TextView(this);
        title.setText("Enable automatic ARES Wi-Fi");
        title.setTextSize(24f);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        root.addView(title, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));

        bodyText = new TextView(this);
        bodyText.setText("Preparing Android's automatic Wi-Fi approval...");
        bodyText.setTextSize(17f);
        bodyText.setLineSpacing(0f, 1.15f);
        LinearLayout.LayoutParams bodyParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        bodyParams.topMargin = spacing;
        root.addView(bodyText, bodyParams);

        retryButton = new Button(this);
        retryButton.setText("Try automatic Wi-Fi setup again");
        retryButton.setMinHeight(Math.round(56f * density));
        retryButton.setVisibility(View.GONE);
        retryButton.setOnClickListener(view -> retrySetup());
        LinearLayout.LayoutParams retryParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        retryParams.topMargin = spacing;
        root.addView(retryButton, retryParams);

        Button laterButton = new Button(this);
        laterButton.setText("Use manual Wi-Fi instead");
        laterButton.setOnClickListener(view -> finish());
        LinearLayout.LayoutParams laterParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        laterParams.topMargin = Math.round(10f * density);
        root.addView(laterButton, laterParams);

        return root;
    }
}
