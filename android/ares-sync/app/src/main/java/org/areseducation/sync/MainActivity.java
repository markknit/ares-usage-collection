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

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Locale;

public final class MainActivity extends Activity {
    public static final String ACTION_COLLECTION_DUE = "org.areseducation.sync.COLLECTION_DUE";
    public static final String EXTRA_COLLECTION_ID = "collection_id";
    private static final int NOTIFICATION_PERMISSION_REQUEST = 1002;
    private static final DateTimeFormatter DISPLAY_DATE =
            DateTimeFormatter.ofPattern("d MMMM uuuu", Locale.ENGLISH);

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
    private final Runnable uploadStatusRefresh = new Runnable() {
        @Override
        public void run() {
            if (EnrollmentStore.isEnrolled(MainActivity.this)) {
                refreshScheduleStatus();
                statusText.postDelayed(this, 5000L);
            }
        }
    };

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
            CentralUploadScheduler.enqueuePending(this);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (EnrollmentStore.isEnrolled(this)) {
            CentralUploadScheduler.enqueuePending(this);
            refreshScheduleStatus();
            statusText.removeCallbacks(uploadStatusRefresh);
            statusText.postDelayed(uploadStatusRefresh, 1500L);
            if (awaitingWifiSelection) {
                awaitingWifiSelection = false;
                statusText.postDelayed(this::tryCollectionOnCurrentWifi, 1200L);
            }
        }
    }

    @Override
    protected void onPause() {
        if (statusText != null) {
            statusText.removeCallbacks(uploadStatusRefresh);
        }
        super.onPause();
    }

    private void showEnrollmentUi() {
        enrollmentPanel.setVisibility(View.VISIBLE);
        collectionPanel.setVisibility(View.GONE);
        schoolSpinner.setVisibility(View.GONE);
        enrollmentCodeInput.setVisibility(View.GONE);
        enrollButton.setVisibility(View.GONE);
        setEnrollmentControlsEnabled(true);
        enrollmentStatus.setText("Type at least two letters of the school name, then select the correct school.");
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
        enrollmentStatus.setText("Searching for the school...");

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
                    enrollmentStatus.setText("Select the school, enter its enrollment code, then tap Enroll this phone.");
                });
            }

            @Override
            public void onError(String message) {
                runOnUiThread(() -> {
                    setEnrollmentControlsEnabled(true);
                    enrollmentStatus.setText("Could not search the school list. Make sure this phone has Internet access, then try again.\n\nTechnical details: " + message);
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
        enrollmentStatus.setText("Enrolling this phone to " + school.canonicalName + "...");

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
                            enrollmentStatus.setText("Enrollment failed. Confirm the selected school and code, then try again.\n\nTechnical details: " + message);
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
        enrolledSchoolText.setText("School: " + enrollment.canonicalName);

        CollectionReminderScheduler.scheduleAll(this);
        CentralUploadScheduler.enqueuePending(this);
        refreshScheduleStatus();

        if (justEnrolled) {
            setStatus("Setup complete. Everything is ready. No action is required now.");
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
                setStatus("ARES Sync needs the school Wi-Fi for this collection. Connect this phone to ARES or ARES2. Collection will start automatically when the school server is available.");
                return;
            }
        }
        setStatus("Everything is ready. No action is required now.");
    }

    private void openWifiPanel() {
        if (!EnrollmentStore.isEnrolled(this)) {
            showEnrollmentUi();
            return;
        }

        awaitingWifiSelection = true;
        setStatus("Choose ARES or ARES2 in Wi-Fi settings, then return to ARES Sync. Collection will start automatically.");
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
            setStatus("No Wi-Fi connection is available. Connect this phone to ARES or ARES2 and try again.\n\nTechnical details: "
                    + wifiConnector.getDiagnostics());
            setButtonsEnabled(true);
            return;
        }

        setButtonsEnabled(false);
        setStatus("Checking the school server...");

        AresServerClient.testAndDownload(
                this,
                wifiNetwork,
                new AresServerClient.Callback() {
                    @Override
                    public void onSuccess(AresServerClient.Result result) {
                        runOnUiThread(() -> {
                            if (result.fileName != null) {
                                if (CollectionSchedule.find(result.collectionId) != null) {
                                    CollectionSchedule.markCompleted(MainActivity.this, result.collectionId);
                                    CollectionReminderScheduler.cancel(MainActivity.this, result.collectionId);
                                    CollectionNotification.cancel(MainActivity.this, result.collectionId);
                                }
                                CentralUploadScheduler.enqueuePending(MainActivity.this);
                                CollectionReminderScheduler.scheduleAll(MainActivity.this);
                                refreshScheduleStatus();
                                setStatus("Usage collection complete. It will be sent automatically when Internet access is available.");
                            } else if (result.statusCode == 204) {
                                CollectionReminderScheduler.scheduleAll(MainActivity.this);
                                refreshScheduleStatus();
                                setStatus("No usage collection is due right now.");
                            } else {
                                setStatus("The school server responded, but no usage file was received. Please try again.");
                            }
                            setButtonsEnabled(true);
                        });
                    }

                    @Override
                    public void onError(String message) {
                        runOnUiThread(() -> {
                            setStatus("Could not collect usage data from the school server. Make sure this phone is connected to ARES or ARES2, then try again.\n\nTechnical details: "
                                    + message + "\n" + wifiConnector.getDiagnostics());
                            setButtonsEnabled(true);
                        });
                    }
                });
    }

    private void refreshScheduleStatus() {
        if (!EnrollmentStore.isEnrolled(this)) {
            return;
        }

        String uploadLine = pendingUploadLine();
        CollectionSchedule.Collection due = CollectionSchedule.getPendingDueCollection(this);
        if (due != null) {
            chooseWifiButton.setVisibility(View.VISIBLE);
            scheduleText.setText("Usage collection is due\n"
                    + due.label + " - " + formatDate(due.dueDate)
                    + "\n\nConnect this phone to the school ARES Wi-Fi. ARES Sync will collect automatically."
                    + uploadLine);
            return;
        }

        chooseWifiButton.setVisibility(View.GONE);
        CollectionSchedule.Collection next = CollectionSchedule.getNextIncompleteCollection(this);
        if (next != null) {
            scheduleText.setText("Next collection\n"
                    + formatDate(next.dueDate)
                    + "\n\nEverything is ready. No action required."
                    + uploadLine);
        } else {
            scheduleText.setText("2026 collections complete\n\nNo further collection is scheduled on this phone."
                    + uploadLine);
        }
    }

    private String pendingUploadLine() {
        PendingUploadStore.UploadStatus upload = PendingUploadStore.getStatus(this);
        if (upload.pendingCount <= 0) {
            return "\n\nUsage data: up to date.";
        }

        if ("blocked".equals(upload.status)) {
            return "\n\nUsage data: upload needs attention. Connect to the Internet and reopen ARES Sync.";
        }

        return "\n\nUsage data: " + upload.pendingCount + " collection"
                + (upload.pendingCount == 1 ? "" : "s")
                + " waiting to send when Internet is available.";
    }

    private static String formatDate(LocalDate date) {
        return DISPLAY_DATE.format(date);
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
