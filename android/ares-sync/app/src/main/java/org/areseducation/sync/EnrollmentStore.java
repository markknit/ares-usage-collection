package org.areseducation.sync;

import android.content.Context;
import android.content.SharedPreferences;

public final class EnrollmentStore {
    private static final String PREFS = "org.areseducation.sync.device_enrollment";
    private static final String KEY_SCHOOL_ID = "school_id";
    private static final String KEY_CANONICAL_NAME = "canonical_name";
    private static final String KEY_DEVICE_ID = "device_id";
    private static final String KEY_DEVICE_CREDENTIAL = "device_credential";

    private EnrollmentStore() {
    }

    public static boolean isEnrolled(Context context) {
        return get(context) != null;
    }

    public static Enrollment get(Context context) {
        SharedPreferences preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        String schoolId = preferences.getString(KEY_SCHOOL_ID, "");
        String canonicalName = preferences.getString(KEY_CANONICAL_NAME, "");
        String deviceId = preferences.getString(KEY_DEVICE_ID, "");
        String deviceCredential = preferences.getString(KEY_DEVICE_CREDENTIAL, "");

        if (isBlank(schoolId)
                || isBlank(canonicalName)
                || isBlank(deviceId)
                || isBlank(deviceCredential)) {
            return null;
        }

        return new Enrollment(schoolId, canonicalName, deviceId, deviceCredential);
    }

    public static void save(Context context, EnrollmentClient.EnrollmentResult result) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit()
                .putString(KEY_SCHOOL_ID, result.schoolId)
                .putString(KEY_CANONICAL_NAME, result.canonicalName)
                .putString(KEY_DEVICE_ID, result.deviceId)
                .putString(KEY_DEVICE_CREDENTIAL, result.deviceCredential)
                .apply();
    }

    static void clear(Context context) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit()
                .clear()
                .apply();
    }

    private static boolean isBlank(String value) {
        return value == null || value.trim().isEmpty();
    }

    public static final class Enrollment {
        public final String schoolId;
        public final String canonicalName;
        public final String deviceId;
        public final String deviceCredential;

        Enrollment(
                String schoolId,
                String canonicalName,
                String deviceId,
                String deviceCredential) {
            this.schoolId = schoolId;
            this.canonicalName = canonicalName;
            this.deviceId = deviceId;
            this.deviceCredential = deviceCredential;
        }
    }
}
