package org.areseducation.sync;

import android.content.Context;
import android.net.Network;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class AresServerClient {
    private static final String ENDPOINT =
            "http://ares.local/tracker/prepare_due_usage_upload.php";
    private static final ExecutorService EXECUTOR = Executors.newSingleThreadExecutor();

    public interface Callback {
        void onSuccess(Result result);
        void onError(String message);
    }

    public static final class Result {
        public final int statusCode;
        public final String collectionId;
        public final String dueDate;
        public final String fileName;
        public final long byteCount;

        private Result(
                int statusCode,
                String collectionId,
                String dueDate,
                String fileName,
                long byteCount) {
            this.statusCode = statusCode;
            this.collectionId = collectionId;
            this.dueDate = dueDate;
            this.fileName = fileName;
            this.byteCount = byteCount;
        }
    }

    private AresServerClient() {
    }

    public static void testAndDownload(
            Context context,
            Network network,
            Callback callback) {
        EXECUTOR.execute(() -> {
            HttpURLConnection connection = null;
            try {
                URL url = new URL(ENDPOINT);
                connection = (HttpURLConnection) network.openConnection(url);
                connection.setRequestMethod("GET");
                connection.setConnectTimeout(10000);
                connection.setReadTimeout(30000);
                connection.setInstanceFollowRedirects(false);
                connection.setRequestProperty("Accept", "text/csv");

                int status = connection.getResponseCode();
                String collection = connection.getHeaderField("X-ARES-Collection");
                String dueDate = connection.getHeaderField("X-ARES-Due-Date");

                if (status == HttpURLConnection.HTTP_NO_CONTENT) {
                    callback.onSuccess(new Result(status, collection, dueDate, null, 0));
                    return;
                }

                if (status != HttpURLConnection.HTTP_OK) {
                    callback.onError("ARES server returned HTTP " + status + ".");
                    return;
                }

                String fileName = fileNameFromDisposition(
                        connection.getHeaderField("Content-Disposition"));
                if (fileName == null) {
                    fileName = String.format(
                            Locale.US,
                            "ARES_USAGE_%d.csv",
                            System.currentTimeMillis());
                }

                File pendingDir = new File(context.getFilesDir(), "pending");
                if (!pendingDir.exists() && !pendingDir.mkdirs()) {
                    throw new IOException("Could not create app-private pending directory.");
                }

                File target = new File(pendingDir, safeFileName(fileName));
                long bytes = 0;
                try (InputStream input = connection.getInputStream();
                     FileOutputStream output = new FileOutputStream(target)) {
                    byte[] buffer = new byte[8192];
                    int read;
                    while ((read = input.read(buffer)) != -1) {
                        output.write(buffer, 0, read);
                        bytes += read;
                    }
                }

                callback.onSuccess(new Result(
                        status,
                        collection,
                        dueDate,
                        target.getName(),
                        bytes));
            } catch (Exception ex) {
                callback.onError(ex.getClass().getSimpleName() + ": " + ex.getMessage());
            } finally {
                if (connection != null) {
                    connection.disconnect();
                }
            }
        });
    }

    private static String fileNameFromDisposition(String disposition) {
        if (disposition == null) {
            return null;
        }
        for (String part : disposition.split(";")) {
            String trimmed = part.trim();
            if (trimmed.toLowerCase(Locale.US).startsWith("filename=")) {
                String value = trimmed.substring("filename=".length()).trim();
                if (value.startsWith("\"") && value.endsWith("\"") && value.length() >= 2) {
                    value = value.substring(1, value.length() - 1);
                }
                return value;
            }
        }
        return null;
    }

    private static String safeFileName(String fileName) {
        return fileName.replaceAll("[^A-Za-z0-9._-]", "_");
    }
}
