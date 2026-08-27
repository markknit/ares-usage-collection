package org.areseducation.sync;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Network;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.Button;
import android.widget.TextView;

public final class MainActivity extends Activity {
    public static final String ACTION_COLLECTION_DUE = "org.areseducation.sync.COLLECTION_DUE";
    public static final String EXTRA_COLLECTION_ID = "collection_id";
    private static final int NOTIFICATION_PERMISSION_REQUEST = 1002;

    private TextView scheduleText;
    private TextView statusText;
    private Button chooseWifiButton;
    private Button currentWifiButton;
    private AresWifiConnector wifiConnector;
    private boolean awaitingWifiSelection;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        scheduleText = findViewById(R.id.scheduleText);
        statusText = findViewById(R.id.statusText);
        chooseWifiButton = findViewById(R.id.chooseWifiButton);
        currentWifiButton = findViewById(R.id.currentWifiButton);
        wifiConnector = new AresWifiConnector(this);

        CollectionNotification.ensureChannel(this);
        CollectionReminderScheduler.scheduleAll(this);
        refreshScheduleStatus();
        handleIntent(getIntent());

        chooseWifiButton.setOnClickListener(view -> openWifiPanel());
        currentWifiButton.setOnClickListener(view -> tryCollectionOnCurrentWifi(false));

        requestNotificationPermissionIfNeeded();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleIntent(intent);
        refreshScheduleStatus();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (awaitingWifiSelection) {
            awaitingWifiSelection = false;
            statusText.postDelayed(() -> tryCollectionOnCurrentWifi(true), 1200L);
        }
    }

    private void handleIntent(Intent intent) {
        if (intent != null && ACTION_COLLECTION_DUE.equals(intent.getAction())) {
            String collectionId = intent.getStringExtra(EXTRA_COLLECTION_ID);
            CollectionSchedule.Collection collection = CollectionSchedule.find(collectionId);
            if (collection != null && !CollectionSchedule.isCompleted(this, collection.id)) {
                setStatus(collection.label + " collection is due.\n\n"
                        + "Tap Choose ARES Wi-Fi, select ARES2 or ARES in Android's Wi-Fi panel, then return to ARES Sync. The download will start automatically.");
                return;
            }
        }
        setStatus("Ready. When a collection is due, choose ARES2 or ARES at the school. ARES Sync will test ares.local and download the due usage file automatically after you return.");
    }

    private void openWifiPanel() {
        awaitingWifiSelection = true;
        setStatus("Android Wi-Fi controls are opening.\n\n"
                + "Please choose ARES2 or ARES. Then close the Wi-Fi panel or return to ARES Sync. The collection check will start automatically.");
        try {
            startActivity(new Intent(Settings.Panel.ACTION_WIFI));
        } catch (RuntimeException ex) {
            startActivity(new Intent(Settings.ACTION_WIFI_SETTINGS));
        }
    }

    private void tryCollectionOnCurrentWifi(boolean fromPicker) {
        Network wifiNetwork = wifiConnector.getCurrentWifiNetwork();
        if (wifiNetwork == null) {
            setStatus("No Wi-Fi connection is currently available.\n\n"
                    + "Tap Choose ARES Wi-Fi and select ARES2 or ARES, then return to ARES Sync.\n\n"
                    + wifiConnector.getDiagnostics());
            setButtonsEnabled(true);
            return;
        }

        setButtonsEnabled(false);
        setStatus((fromPicker
                ? "Wi-Fi selection returned. Checking for the ARES server…"
                : "Checking the current Wi-Fi for the ARES server…")
                + "\n\n" + wifiConnector.getDiagnostics());

        AresServerClient.testAndDownload(
                this,
                wifiNetwork,
                new AresServerClient.Callback() {
                    @Override
                    public void onSuccess(AresServerClient.Result result) {
                        runOnUiThread(() -> {
                            StringBuilder message = new StringBuilder();
                            message.append("✓ ARES server reached\n");
                            message.append("HTTP status: ").append(result.statusCode).append("\n");

                            if (result.collectionId != null && !result.collectionId.isEmpty()) {
                                message.append("Collection: ").append(result.collectionId).append("\n");
                            }
                            if (result.dueDate != null && !result.dueDate.isEmpty()) {
                                message.append("Server due date: ").append(result.dueDate).append("\n");
                            }

                            if (result.fileName != null) {
                                message.append("✓ Downloaded: ").append(result.fileName).append("\n");
                                message.append("Bytes: ").append(result.byteCount).append("\n");
                                message.append("Saved in app-private pending storage\n");

                                if (CollectionSchedule.find(result.collectionId) != null) {
                                    CollectionSchedule.markCompleted(MainActivity.this, result.collectionId);
                                    CollectionReminderScheduler.cancel(MainActivity.this, result.collectionId);
                                    CollectionNotification.cancel(MainActivity.this, result.collectionId);
                                }
                                message.append("\nCollection complete. The teacher can reconnect the phone to its normal Internet Wi-Fi.");
                            } else if (result.statusCode == 204) {
                                message.append("No collection is currently due according to the ARES server.\n");
                            }

                            CollectionReminderScheduler.scheduleAll(MainActivity.this);
                            refreshScheduleStatus();
                            message.append("\n\n").append(wifiConnector.getDiagnostics());
                            setStatus(message.toString());
                            setButtonsEnabled(true);
                        });
                    }

                    @Override
                    public void onError(String message) {
                        runOnUiThread(() -> {
                            setStatus("Could not reach the ARES server over the selected Wi-Fi.\n\n"
                                    + "Make sure the phone is connected to ARES2 or ARES, then try again.\n\n"
                                    + message + "\n\n" + wifiConnector.getDiagnostics());
                            setButtonsEnabled(true);
                        });
                    }
                });
    }

    private void refreshScheduleStatus() {
        CollectionSchedule.Collection due = CollectionSchedule.getPendingDueCollection(this);
        if (due != null) {
            scheduleText.setText("DUE: " + due.label + "\nScheduled date: " + due.dueDate
                    + " (Africa/Nairobi)\nConnect to ARES2 or ARES at the school to collect.");
            return;
        }

        CollectionSchedule.Collection next = CollectionSchedule.getNextIncompleteCollection(this);
        if (next != null) {
            scheduleText.setText("Next collection: " + next.label + "\nScheduled date: "
                    + next.dueDate + " (Africa/Nairobi)");
        } else {
            scheduleText.setText("All configured 2026 collections are marked complete on this phone.");
        }
    }

    private void requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(
                    new String[]{Manifest.permission.POST_NOTIFICATIONS},
                    NOTIFICATION_PERMISSION_REQUEST);
        } else {
            CollectionNotification.showIfDue(this);
        }
    }

    @Override
    public void onRequestPermissionsResult(
            int requestCode,
            String[] permissions,
            int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == NOTIFICATION_PERMISSION_REQUEST
                && grantResults.length > 0
                && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            CollectionNotification.showIfDue(this);
        }
    }

    private void setButtonsEnabled(boolean enabled) {
        chooseWifiButton.setEnabled(enabled);
        currentWifiButton.setEnabled(enabled);
    }

    private void setStatus(String message) {
        statusText.setText(message);
    }

    @Override
    protected void onDestroy() {
        wifiConnector.close();
        super.onDestroy();
    }
}
