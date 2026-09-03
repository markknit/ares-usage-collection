package org.areseducation.sync;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Network;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Spinner;
import android.widget.TextView;

import java.util.List;
import java.util.Locale;

public final class MainActivity extends Activity {
    public static final String ACTION_COLLECTION_DUE = "org.areseducation.sync.COLLECTION_DUE";
    public static final String EXTRA_COLLECTION_ID = "collection_id";
    private static final int NOTIFICATION_PERMISSION_REQUEST = 1002;

    private LinearLayout enrollmentPanel;
    private LinearLayout collectionPanel;
    private EditText schoolSearchInput;
    private EditText enrollmentCodeInput;
    private Button schoolSearchButton;
    private Button enrollButton;
    private Spinner schoolSpinner;
    private TextView enrollmentStatus;
    private TextView enrolledSchoolText;
    private TextView scheduleText;
    private TextView statusText;
    private Button chooseWifiButton;
    private AresWifiConnector wifiConnector;
    private boolean awaitingWifiSelection;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        enrollmentPanel = findViewById(R.id.enrollmentPanel);
        collectionPanel = findViewById(R.id.collectionPanel);
        schoolSearchInput = findViewById(R.id.schoolSearchInput);
        enrollmentCodeInput = findViewById(R.id.enrollmentCodeInput);
        schoolSearchButton = findViewById(R.id.schoolSearchButton);
        enrollButton = findViewById(R.id.enrollButton);
        schoolSpinner = findViewById(R.id.schoolSpinner);
        enrollmentStatus = findViewById(R.id.enrollmentStatus);
        enrolledSchoolText = findViewById(R.id.enrolledSchoolText);
        scheduleText = findViewById(R.id.scheduleText);
        statusText = findViewById(R.id.statusText);
        chooseWifiButton = findViewById(R.id.chooseWifiButton);
        wifiConnector = new AresWifiConnector(this);

        CollectionNotification.ensureChannel(this);

        schoolSearchButton.setOnClickListener(view -> searchForSchool());
        enrollButton.setOnClickListener(view -> enrollSelectedSchool());
        chooseWifiButton.setOnClickListener(view -> openWifiPanel());

        if (EnrollmentStore.isEnrolled(this)) {
            activateCollectionUi(false);
        } else {
            showEnrollmentUi();
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        if (EnrollmentStore.isEnrolled(this)) {
            handleIntent(intent);
            refreshScheduleStatus();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (EnrollmentStore.isEnrolled(this) && awaitingWifiSelection) {
            awaitingWifiSelection = false;
            statusText.postDelayed(this::tryCollectionOnCurrentWifi, 1200L);
        }
    }

    private void showEnrollmentUi() {
        enrollmentPanel.setVisibility(View.VISIBLE);
        collectionPanel.setVisibility(View.GONE);
        schoolSpinner.setVisibility(View.GONE);
        enrollmentCodeInput.setVisibility(View.GONE);
        enrollButton.setVisibility(View.GONE);
        setEnrollmentControlsEnabled(true);
        enrollmentStatus.setText("Type at least two letters of the school name, then select the correct school from the results.");
    }

    private void searchForSchool() {
        String query = schoolSearchInput.getText().toString().trim();
        if (query.length() < 2) {
            enrollmentStatus.setText("Enter at least two letters of the school name.");
            return;
        }

        setEnrollmentControlsEnabled(false);
        schoolSpinner.setVisibility(View.GONE);
        enrollmentCodeInput.setVisibility(View.GONE);
        enrollButton.setVisibility(View.GONE);
        enrollmentStatus.setText("Searching the ARES school list…");

        EnrollmentClient.searchSchools(query, new EnrollmentClient.SearchCallback() {
            @Override
            public void onSuccess(List<EnrollmentClient.School> schools) {
                runOnUiThread(() -> {
                    setEnrollmentControlsEnabled(true);
                    if (schools.isEmpty()) {
                        enrollmentStatus.setText("No matching school was found. Try a shorter or slightly different school name.");
                        return;
                    }

                    ArrayAdapter<EnrollmentClient.School> adapter = new ArrayAdapter<>(
                            MainActivity.this,
                            android.R.layout.simple_spinner_item,
                            schools);
                    adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
                    schoolSpinner.setAdapter(adapter);
                    schoolSpinner.setVisibility(View.VISIBLE);
                    enrollmentCodeInput.setVisibility(View.VISIBLE);
                    enrollButton.setVisibility(View.VISIBLE);
                    enrollmentStatus.setText("Select the exact school, enter its enrollment code, then tap Enroll this phone.");
                });
            }

            @Override
            public void onError(String message) {
                runOnUiThread(() -> {
                    setEnrollmentControlsEnabled(true);
                    enrollmentStatus.setText("Could not search the school list. Make sure this phone has Internet access, then try again.\n\n" + message);
                });
            }
        });
    }

    private void enrollSelectedSchool() {
        Object selected = schoolSpinner.getSelectedItem();
        if (!(selected instanceof EnrollmentClient.School)) {
            enrollmentStatus.setText("Search for and select the school first.");
            return;
        }

        EnrollmentClient.School school = (EnrollmentClient.School) selected;
        String code = enrollmentCodeInput.getText().toString().trim().toUpperCase(Locale.US);
        if (code.isEmpty()) {
            enrollmentStatus.setText("Enter the enrollment code for " + school.canonicalName + ".");
            return;
        }

        enrollmentCodeInput.setText(code);
        setEnrollmentControlsEnabled(false);
        enrollmentStatus.setText("Enrolling this phone to " + school.canonicalName + "…");

        String deviceLabel = (Build.MANUFACTURER + " " + Build.MODEL).trim();
        EnrollmentClient.enroll(
                school.schoolId,
                code,
                deviceLabel,
                new EnrollmentClient.EnrollmentCallback() {
                    @Override
                    public void onSuccess(EnrollmentClient.EnrollmentResult result) {
                        runOnUiThread(() -> {
                            EnrollmentStore.save(MainActivity.this, result);
                            enrollmentCodeInput.setText("");
                            activateCollectionUi(true);
                        });
                    }

                    @Override
                    public void onError(String message) {
                        runOnUiThread(() -> {
                            setEnrollmentControlsEnabled(true);
                            enrollmentStatus.setText("Enrollment failed. Confirm the selected school and code, then try again.\n\n" + message);
                        });
                    }
                });
    }

    private void activateCollectionUi(boolean justEnrolled) {
        EnrollmentStore.Enrollment enrollment = EnrollmentStore.get(this);
        if (enrollment == null) {
            showEnrollmentUi();
            return;
        }

        enrollmentPanel.setVisibility(View.GONE);
        collectionPanel.setVisibility(View.VISIBLE);
        enrolledSchoolText.setText("School: " + enrollment.canonicalName
                + "\nDevice: " + enrollment.deviceId);

        CollectionReminderScheduler.scheduleAll(this);
        refreshScheduleStatus();

        if (justEnrolled) {
            setStatus("✓ Setup complete for " + enrollment.canonicalName + ".\n\n"
                    + "ARES Sync is ready. When a collection is due, use the button below to connect to ARES2 or ARES at the school.");
        } else {
            handleIntent(getIntent());
        }

        requestNotificationPermissionIfNeeded();
    }

    private void handleIntent(Intent intent) {
        if (intent != null && ACTION_COLLECTION_DUE.equals(intent.getAction())) {
            String collectionId = intent.getStringExtra(EXTRA_COLLECTION_ID);
            CollectionSchedule.Collection collection = CollectionSchedule.find(collectionId);
            if (collection != null && !CollectionSchedule.isCompleted(this, collection.id)) {
                setStatus(collection.label + " collection is due.\n\n"
                        + "Tap Connect to ARES or ARES2 wifi network, select ARES2 or ARES in Android's Wi-Fi panel, then return to ARES Sync. The download will start automatically.");
                return;
            }
        }
        setStatus("Ready. When a collection is due, connect to ARES2 or ARES at the school. ARES Sync will test ares.local and download the due usage file automatically after you return.");
    }

    private void openWifiPanel() {
        if (!EnrollmentStore.isEnrolled(this)) {
            showEnrollmentUi();
            return;
        }

        awaitingWifiSelection = true;
        setStatus("Android Wi-Fi controls are opening.\n\n"
                + "Please choose ARES2 or ARES. Then close the Wi-Fi panel or return to ARES Sync. The collection check will start automatically.");
        try {
            startActivity(new Intent(Settings.Panel.ACTION_WIFI));
        } catch (RuntimeException ex) {
            startActivity(new Intent(Settings.ACTION_WIFI_SETTINGS));
        }
    }

    private void tryCollectionOnCurrentWifi() {
        if (!EnrollmentStore.isEnrolled(this)) {
            showEnrollmentUi();
            return;
        }

        Network wifiNetwork = wifiConnector.getCurrentWifiNetwork();
        if (wifiNetwork == null) {
            setStatus("No Wi-Fi connection is currently available.\n\n"
                    + "Tap Connect to ARES or ARES2 wifi network, select ARES2 or ARES, then return to ARES Sync.\n\n"
                    + wifiConnector.getDiagnostics());
            setButtonsEnabled(true);
            return;
        }

        setButtonsEnabled(false);
        setStatus("Wi-Fi selection returned. Checking for the ARES server…\n\n"
                + wifiConnector.getDiagnostics());

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
        if (!EnrollmentStore.isEnrolled(this)) {
            return;
        }

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
        if (!EnrollmentStore.isEnrolled(this)) {
            return;
        }

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
                && grantResults[0] == PackageManager.PERMISSION_GRANTED
                && EnrollmentStore.isEnrolled(this)) {
            CollectionNotification.showIfDue(this);
        }
    }

    private void setEnrollmentControlsEnabled(boolean enabled) {
        schoolSearchInput.setEnabled(enabled);
        schoolSearchButton.setEnabled(enabled);
        schoolSpinner.setEnabled(enabled);
        enrollmentCodeInput.setEnabled(enabled);
        enrollButton.setEnabled(enabled);
    }

    private void setButtonsEnabled(boolean enabled) {
        chooseWifiButton.setEnabled(enabled);
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
