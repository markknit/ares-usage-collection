package org.areseducation.sync;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.res.ColorStateList;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.Rect;
import android.graphics.drawable.GradientDrawable;
import android.net.Network;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.ScrollView;
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

    private ScrollView screenRoot;
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
    private ThemeColors currentColors;

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

        screenRoot = findViewById(R.id.screenRoot);
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
        schoolSearchInput.setOnFocusChangeListener((view, focused) -> {
            if (focused) {
                scrollFieldAboveKeyboard(view);
            }
        });
        enrollmentCodeInput.setOnFocusChangeListener((view, focused) -> {
            if (focused) {
                scrollFieldAboveKeyboard(view);
            }
        });

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
            getSharedPreferences(UI_PREFS, MODE_PRIVATE)
                    .edit()
                    .putString(KEY_APPEARANCE, value)
                    .apply();
            applyAppearance(value);
        });

        String appearance = getSharedPreferences(UI_PREFS, MODE_PRIVATE)
                .getString(KEY_APPEARANCE, null);
        if (appearance == null || appearance.isEmpty()) {
            appearance = defaultAppearanceForSystem();
        }
        applyAppearance(appearance);

        if (EnrollmentStore.isEnrolled(this)) {
            activateCollectionUi(false);
        } else {
            showEnrollmentUi();
        }
    }

    private String defaultAppearanceForSystem() {
        int nightMode = getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK;
        return nightMode == Configuration.UI_MODE_NIGHT_YES ? "dark" : "warm";
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

                    SchoolSpinnerAdapter adapter = new SchoolSpinnerAdapter(MainActivity.this, schools);
                    ThemeColors colors = currentColors == null ? ThemeColors.forName(defaultAppearanceForSystem()) : currentColors;
                    adapter.setPalette(colors.text, colors.input, colors.border);
                    schoolSpinner.setAdapter(adapter);
                    schoolSpinner.setVisibility(View.VISIBLE);
                    enrollmentCodeInput.setVisibility(View.VISIBLE);
                    enrollButton.setVisibility(View.VISIBLE);
                    enrollmentStatus.setText("Select the school, enter its enrollment code, then tap Enroll this phone.");
                    enrollmentCodeInput.postDelayed(() -> scrollFieldIntoView(enrollmentCodeInput), 180L);
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
            scrollFieldIntoView(enrollmentCodeInput);
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
                            scrollFieldIntoView(enrollmentCodeInput);
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

    private void scrollFieldAboveKeyboard(View field) {
        field.postDelayed(() -> scrollFieldIntoView(field), 300L);
    }

    private void scrollFieldIntoView(View field) {
        if (screenRoot == null || field == null) {
            return;
        }
        Rect rect = new Rect();
        field.getDrawingRect(rect);
        screenRoot.offsetDescendantRectToMyCoords(field, rect);
        int margin = Math.round(28f * getResources().getDisplayMetrics().density);
        screenRoot.smoothScrollTo(0, Math.max(0, rect.top - margin));
    }

    private void applyAppearance(String appearance) {
        currentColors = ThemeColors.forName(appearance);
        ThemeColors colors = currentColors;
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

        screenRoot.setBackgroundColor(colors.page);
        styleViewTree(findViewById(R.id.contentRoot), colors);

        headerCard.setBackground(cardDrawable(colors.header, colors.borderStrong, 16));
        enrollmentPanel.setBackground(cardDrawable(colors.enrollment, colors.border, 16));
        schoolCard.setBackground(cardDrawable(colors.school, colors.borderStrong, 16));
        scheduleCard.setBackground(cardDrawable(colors.schedule, colors.borderStrong, 16));
        statusCard.setBackground(cardDrawable(colors.status, colors.borderStrong, 16));
        appearanceCard.setBackground(cardDrawable(colors.appearance, colors.border, 16));

        styleInput(schoolSearchInput, colors);
        styleInput(enrollmentCodeInput, colors);
        styleButton(schoolSearchButton, colors);
        styleButton(enrollButton, colors);
        styleButton(chooseWifiButton, colors);
        appearanceLight.setButtonTintList(ColorStateList.valueOf(colors.accent));
        appearanceWarm.setButtonTintList(ColorStateList.valueOf(colors.accent));
        appearanceBlue.setButtonTintList(ColorStateList.valueOf(colors.accent));
        appearanceDark.setButtonTintList(ColorStateList.valueOf(colors.accent));

        if (schoolSpinner.getAdapter() instanceof SchoolSpinnerAdapter) {
            ((SchoolSpinnerAdapter) schoolSpinner.getAdapter())
                    .setPalette(colors.text, colors.input, colors.border);
        }

        applyScheduleHighlight(EnrollmentStore.isEnrolled(this)
                && CollectionSchedule.getPendingDueCollection(this) != null);
    }

    private void applyScheduleHighlight(boolean due) {
        if (scheduleCard == null || currentColors == null) {
            return;
        }
        int fill = due ? currentColors.warning : currentColors.schedule;
        int stroke = due ? currentColors.warningBorder : currentColors.borderStrong;
        scheduleCard.setBackground(cardDrawable(fill, stroke, 16));
    }

    private void styleViewTree(View view, ThemeColors colors) {
        if (view instanceof TextView) {
            TextView textView = (TextView) view;
            Object tag = textView.getTag();
            if ("accent".equals(tag) || "section".equals(tag) || "title".equals(tag)) {
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
        input.setBackground(cardDrawable(colors.input, colors.borderStrong, 10));
        int h = Math.round(16f * input.getResources().getDisplayMetrics().density);
        int v = Math.round(10f * input.getResources().getDisplayMetrics().density);
        input.setPadding(h, v, h, v);
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
        final int enrollment;
        final int school;
        final int schedule;
        final int status;
        final int appearance;
        final int input;
        final int text;
        final int mutedText;
        final int accent;
        final int border;
        final int borderStrong;
        final int buttonText;
        final int warning;
        final int warningBorder;

        ThemeColors(int page, int header, int enrollment, int school, int schedule, int status,
                    int appearance, int input, int text, int mutedText, int accent, int border,
                    int borderStrong, int buttonText, int warning, int warningBorder) {
            this.page = page;
            this.header = header;
            this.enrollment = enrollment;
            this.school = school;
            this.schedule = schedule;
            this.status = status;
            this.appearance = appearance;
            this.input = input;
            this.text = text;
            this.mutedText = mutedText;
            this.accent = accent;
            this.border = border;
            this.borderStrong = borderStrong;
            this.buttonText = buttonText;
            this.warning = warning;
            this.warningBorder = warningBorder;
        }

        static ThemeColors forName(String name) {
            if ("dark".equals(name)) {
                return new ThemeColors(
                        Color.rgb(14, 18, 23),
                        Color.rgb(25, 42, 54),
                        Color.rgb(35, 42, 50),
                        Color.rgb(27, 53, 46),
                        Color.rgb(37, 48, 63),
                        Color.rgb(54, 40, 32),
                        Color.rgb(39, 39, 51),
                        Color.rgb(18, 23, 29),
                        Color.rgb(248, 250, 252),
                        Color.rgb(205, 214, 223),
                        Color.rgb(110, 205, 255),
                        Color.rgb(78, 91, 105),
                        Color.rgb(116, 136, 154),
                        Color.WHITE,
                        Color.rgb(88, 61, 15),
                        Color.rgb(243, 181, 54));
            }
            if ("blue".equals(name)) {
                return new ThemeColors(
                        Color.rgb(235, 245, 251),
                        Color.rgb(214, 237, 249),
                        Color.rgb(246, 250, 252),
                        Color.rgb(230, 246, 237),
                        Color.rgb(229, 241, 251),
                        Color.rgb(252, 243, 232),
                        Color.rgb(240, 238, 251),
                        Color.WHITE,
                        Color.rgb(26, 43, 54),
                        Color.rgb(76, 96, 108),
                        Color.rgb(12, 104, 153),
                        Color.rgb(171, 201, 218),
                        Color.rgb(103, 160, 190),
                        Color.WHITE,
                        Color.rgb(255, 245, 205),
                        Color.rgb(207, 150, 28));
            }
            if ("light".equals(name)) {
                return new ThemeColors(
                        Color.rgb(244, 247, 249),
                        Color.rgb(229, 241, 247),
                        Color.WHITE,
                        Color.rgb(236, 247, 240),
                        Color.rgb(239, 246, 251),
                        Color.rgb(252, 245, 236),
                        Color.rgb(244, 241, 250),
                        Color.WHITE,
                        Color.rgb(30, 39, 46),
                        Color.rgb(86, 100, 109),
                        Color.rgb(18, 108, 150),
                        Color.rgb(199, 211, 218),
                        Color.rgb(131, 166, 184),
                        Color.WHITE,
                        Color.rgb(255, 247, 214),
                        Color.rgb(215, 164, 47));
            }
            return new ThemeColors(
                    Color.rgb(249, 245, 235),
                    Color.rgb(242, 233, 210),
                    Color.rgb(255, 252, 245),
                    Color.rgb(235, 246, 236),
                    Color.rgb(237, 245, 249),
                    Color.rgb(251, 239, 224),
                    Color.rgb(244, 239, 249),
                    Color.WHITE,
                    Color.rgb(40, 36, 30),
                    Color.rgb(96, 87, 73),
                    Color.rgb(27, 102, 132),
                    Color.rgb(201, 187, 158),
                    Color.rgb(162, 135, 90),
                    Color.WHITE,
                    Color.rgb(255, 243, 199),
                    Color.rgb(201, 145, 27));
        }
    }
}
