package org.areseducation.sync;

import android.content.Context;
import android.content.SharedPreferences;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.Arrays;
import java.util.Comparator;

public final class PendingUploadStore {
    private static final String PREFS = "org.areseducation.sync.central_upload";
    private static final String KEY_LAST_STATUS = "last_status";
    private static final String KEY_LAST_FILE = "last_file";
    private static final String KEY_LAST_MESSAGE = "last_message";
    private static final String KEY_LAST_UPDATED = "last_updated";

    private PendingUploadStore() {
    }

    public static File[] pendingFiles(Context context) {
        File directory = new File(context.getFilesDir(), "pending");
        File[] files = directory.listFiles(file -> file.isFile() && file.getName().endsWith(".csv"));
        if (files == null) {
            return new File[0];
        }
        Arrays.sort(files, Comparator.comparing(File::getName));
        return files;
    }

    public static int pendingCount(Context context) {
        return pendingFiles(context).length;
    }

    public static boolean moveToSent(Context context, File pendingFile, String acknowledgedFileName) {
        if (pendingFile == null || !pendingFile.isFile()) {
            return false;
        }

        File sentDirectory = new File(context.getFilesDir(), "sent");
        if (!sentDirectory.exists() && !sentDirectory.mkdirs()) {
            return false;
        }

        String fileName = safeFileName(
                acknowledgedFileName == null || acknowledgedFileName.trim().isEmpty()
                        ? pendingFile.getName()
                        : acknowledgedFileName.trim());
        File target = new File(sentDirectory, fileName);
        try {
            Files.move(
                    pendingFile.toPath(),
                    target.toPath(),
                    StandardCopyOption.REPLACE_EXISTING);
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }

    public static void record(Context context, String status, String fileName, String message) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit()
                .putString(KEY_LAST_STATUS, value(status))
                .putString(KEY_LAST_FILE, value(fileName))
                .putString(KEY_LAST_MESSAGE, value(message))
                .putLong(KEY_LAST_UPDATED, System.currentTimeMillis())
                .apply();
    }

    public static UploadStatus getStatus(Context context) {
        SharedPreferences preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return new UploadStatus(
                preferences.getString(KEY_LAST_STATUS, ""),
                preferences.getString(KEY_LAST_FILE, ""),
                preferences.getString(KEY_LAST_MESSAGE, ""),
                preferences.getLong(KEY_LAST_UPDATED, 0L),
                pendingCount(context));
    }

    private static String safeFileName(String value) {
        return value.replaceAll("[^A-Za-z0-9._-]", "_");
    }

    private static String value(String value) {
        return value == null ? "" : value;
    }

    public static final class UploadStatus {
        public final String status;
        public final String fileName;
        public final String message;
        public final long updatedAt;
        public final int pendingCount;

        UploadStatus(String status, String fileName, String message, long updatedAt, int pendingCount) {
            this.status = status;
            this.fileName = fileName;
            this.message = message;
            this.updatedAt = updatedAt;
            this.pendingCount = pendingCount;
        }
    }
}
