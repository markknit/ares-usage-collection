package org.areseducation.sync;

import android.app.Activity;
import android.graphics.Typeface;
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

public final class WifiSetupActivity extends Activity {
    private final Handler handler = new Handler(Looper.getMainLooper());
    private WifiManager wifiManager;
    private WifiManager.SuggestionUserApprovalStatusListener approvalListener;
    private TextView bodyText;
    private Button retryButton;
    private boolean suggestionSubmitted;
    private boolean sawSystemDialogFocusLoss;
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

        bodyText.setText("Android will ask once whether ARES Sync may suggest Wi-Fi networks. Choose Allow. After that, ARES Sync can register ARES and ARES2 for automatic connection without the separate network-save sheet.");
        handler.postDelayed(this::beginSuggestionSetup, 350L);
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
            // Android 11 has the foreground approval dialog but not the approval-status listener.
            // If no dialog appears because approval already exists, verify after the activity has settled.
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
                finishSuccessful();
            } else if (status == WifiManager.STATUS_SUGGESTION_APPROVAL_REJECTED_BY_USER) {
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
            showFailure("Android did not allow ARES Sync to suggest Wi-Fi networks. You can connect manually or enable ARES Sync later under Android's special Wi-Fi control settings.");
        } else if (AresWifiProvisioner.submissionAccepted(status)) {
            finishSuccessful();
        } else {
            showFailure("Android could not confirm automatic ARES Wi-Fi setup (status " + status + "). You can connect manually.");
        }
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
        retryButton.setOnClickListener(view -> beginSuggestionSetup());
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
