package org.areseducation.sync;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Network;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.RadioButton;
import android.widget.RadioGroup;
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
    private static final String UI_PREFS = "org.areseducation.sync.ui";
    private static final String KEY_APPEARANCE = "appearance";
    private static final DateTimeFormatter DISPLAY_DATE =
            DateTimeFormatter.ofPattern("d MMMM uuuu", Locale.ENGLISH);

    private LinearLayout enrollmentPanel;
    private LinearLayout collectionPanel;
    private LinearLayout headerCard;
    private LinearLayout schoolCard;
    private LinearLayout scheduleCard;
    private LinearLayout statusCard;
    private LinearLayout appearanceCard;
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
    private RadioGroup appearanceGroup;
    private RadioButton appearanceLight;
    private RadioButton appearanceWarm;
    private RadioButton appearanceBlue;
    private RadioButton appearanceDark;
    private AresWifiConnector wifiConnector;
    private boolean awaitingWifiSelection;
    private boolean applyingAppearance;

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
        headerCard = findViewById(R.id.headerCard);
        schoolCard = findViewById(R.id.schoolCard);
        scheduleCard = findViewById(R.id.scheduleCard);
        statusCard = findViewById(R.id.statusCard);
        appearanceCard = findViewById(R.id.appearanceCard);
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
        appearanceGroup = findViewById(R.id.appearanceGroup);
        appearanceLight = findViewById(R.id.appearanceLight);
        appearanceWarm = findViewById(R.id.appearanceWarm);
        appearanceBlue = findViewById(R.id.appearanceBlue);
        appearanceDark = findViewById(R.id.appearanceDark);
        wifiConnector = new AresWifiConnector(this);

        CollectionNotification.ensureChannel(this);

        schoolSearchButton.setOnClickListener(view -> searchForSchool());
        enrollButton.setOnClickListener(view -> enrollSelectedSchool());
        chooseWifiButton.setOnClickListener(view -> openWifiPanel());
        appearanceGroup.setOnCheckedChangeListener((group, checkedId) -> {
            if (applyingAppearance) {
                return;
            }
            String value = "light";
            if (checkedId == R.id.appearanceWarm) {
                value = "warm";
            } else if (checkedId == R.id.appearanceBlue) {
                value = "blue";
            } else if (checkedId == R.id.appearanceDark) {
                value = "dark";
            }
            getSharedPreferences(UI_PREFS, MODE_PRIVATE).edit().putString(KEY_APPEARANCE, value).apply();
            applyAppearance(value);
        });

        String appearance = getSharedPreferences(UI_PREFS, MODE_PRIVATE)
                .getString(KEY_APPEARANCE, "light");
        applyAppearance(appearance);

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
        enrolledSchoolText.setText(enrollment.canonicalName);

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
            applyScheduleHighlight(true);
            return;
        }

        chooseWifiButton.setVisibility(View.GONE);
        applyScheduleHighlight(false);
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

    private void applyAppearance(String appearance) {
        ThemeColors colors = ThemeColors.forName(appearance);
        applyingAppearance = true;
        if ("warm".equals(appearance)) {
            appearanceWarm.setChecked(true);
        } else if ("blue".equals(appearance)) {
            appearanceBlue.setChecked(true);
        } else if ("dark".equals(appearance)) {
            appearanceDark.setChecked(true);
        } else {
            appearanceLight.setChecked(true);
        }
        applyingAppearance = false;

        View root = findViewById(R.id.screenRoot);
        root.setBackgroundColor(colors.page);
        styleViewTree(findViewById(R.id.contentRoot), colors);

        headerCard.setBackground(cardDrawable(colors.header, colors.border, 16));
        enrollmentPanel.setBackground(cardDrawable(colors.card, colors.border, 16));
        schoolCard.setBackground(cardDrawable(colors.card, colors.border, 16));
        scheduleCard.setBackground(cardDrawable(colors.card, colors.border, 16));
        statusCard.setBackground(cardDrawable(colors.card, colors.border, 16));
        appearanceCard.setBackground(cardDrawable(colors.card, colors.border, 16));

        styleInput(schoolSearchInput, colors);
        styleInput(enrollmentCodeInput, colors);
        styleButton(schoolSearchButton, colors);
        styleButton(enrollButton, colors);
        styleButton(chooseWifiButton, colors);
        appearanceLight.setButtonTintList(ColorStateList.valueOf(colors.accent));
        appearanceWarm.setButtonTintList(ColorStateList.valueOf(colors.accent));
        appearanceBlue.setButtonTintList(ColorStateList.valueOf(colors.accent));
        appearanceDark.setButtonTintList(ColorStateList.valueOf(colors.accent));
        applyScheduleHighlight(CollectionSchedule.getPendingDueCollection(this) != null
                && EnrollmentStore.isEnrolled(this));
    }

    private void applyScheduleHighlight(boolean due) {
        if (scheduleCard == null) {
            return;
        }
        String appearance = getSharedPreferences(UI_PREFS, MODE_PRIVATE)
                .getString(KEY_APPEARANCE, "light");
        ThemeColors colors = ThemeColors.forName(appearance);
        int fill = due ? colors.warning : colors.card;
        int stroke = due ? colors.warningBorder : colors.border;
        scheduleCard.setBackground(cardDrawable(fill, stroke, 16));
    }

    private void styleViewTree(View view, ThemeColors colors) {
        if (view instanceof TextView) {
            TextView textView = (TextView) view;
            Object tag = textView.getTag();
            if ("accent".equals(tag)) {
                textView.setTextColor(colors.accent);
            } else if ("muted".equals(tag)) {
                textView.setTextColor(colors.mutedText);
            } else {
                textView.setTextColor(colors.text);
            }
        }
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) {
                styleViewTree(group.getChildAt(i), colors);
            }
        }
    }

    private static void styleInput(EditText input, ThemeColors colors) {
        input.setTextColor(colors.text);
        input.setHintTextColor(colors.mutedText);
        input.setBackground(cardDrawable(colors.input, colors.border, 10));
        input.setPadding(16, 8, 16, 8);
    }

    private static void styleButton(Button button, ThemeColors colors) {
        button.setTextColor(colors.buttonText);
        button.setBackgroundTintList(ColorStateList.valueOf(colors.accent));
    }

    private static GradientDrawable cardDrawable(int fill, int stroke, int radiusDp) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(fill);
        drawable.setCornerRadius(radiusDp * 2.5f);
        drawable.setStroke(2, stroke);
        return drawable;
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

    private static final class ThemeColors {
        final int page;
        final int header;
        final int card;
        final int input;
        final int text;
        final int mutedText;
        final int accent;
        final int border;
        final int buttonText;
        final int warning;
        final int warningBorder;

        ThemeColors(int page, int header, int card, int input, int text, int mutedText,
                    int accent, int border, int buttonText, int warning, int warningBorder) {
            this.page = page;
            this.header = header;
            this.card = card;
            this.input = input;
            this.text = text;
            this.mutedText = mutedText;
            this.accent = accent;
            this.border = border;
            this.buttonText = buttonText;
            this.warning = warning;
            this.warningBorder = warningBorder;
        }

        static ThemeColors forName(String name) {
            if ("dark".equals(name)) {
                return new ThemeColors(
                        Color.rgb(20, 24, 29), Color.rgb(29, 36, 44), Color.rgb(34, 41, 49),
                        Color.rgb(46, 55, 64), Color.rgb(245, 247, 250), Color.rgb(190, 199, 210),
                        Color.rgb(91, 180, 235), Color.rgb(79, 92, 105), Color.WHITE,
                        Color.rgb(79, 58, 20), Color.rgb(225, 170, 59));
            }
            if ("warm".equals(name)) {
                return new ThemeColors(
                        Color.rgb(250, 246, 236), Color.rgb(244, 236, 216), Color.WHITE,
                        Color.rgb(255, 253, 247), Color.rgb(41, 37, 31), Color.rgb(100, 91, 77),
                        Color.rgb(34, 105, 132), Color.rgb(205, 191, 162), Color.WHITE,
                        Color.rgb(255, 244, 204), Color.rgb(204, 151, 30));
            }
            if ("blue".equals(name)) {
                return new ThemeColors(
                        Color.rgb(239, 247, 252), Color.rgb(218, 239, 250), Color.WHITE,
                        Color.rgb(248, 252, 255), Color.rgb(27, 46, 58), Color.rgb(82, 103, 116),
                        Color.rgb(16, 108, 155), Color.rgb(173, 205, 222), Color.WHITE,
                        Color.rgb(255, 247, 214), Color.rgb(213, 157, 36));
            }
            return new ThemeColors(
                    Color.rgb(245, 247, 249), Color.rgb(232, 241, 246), Color.WHITE,
                    Color.rgb(250, 251, 252), Color.rgb(31, 40, 47), Color.rgb(93, 106, 115),
                    Color.rgb(20, 111, 151), Color.rgb(202, 213, 219), Color.WHITE,
                    Color.rgb(255, 248, 218), Color.rgb(215, 164, 47));
        }
    }
}
