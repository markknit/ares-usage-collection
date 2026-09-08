package org.areseducation.sync;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

import javax.net.ssl.HttpsURLConnection;
import java.net.URL;

public final class CentralUploadClient {
    private static final String ENDPOINT = "https://areseducation.org/monitor_upload/";

    private CentralUploadClient() {
    }

    public static Result upload(File file, EnrollmentStore.Enrollment enrollment) {
        if (file == null || !file.isFile()) {
            return Result.permanentFailure(0, "pending-file-missing");
        }
        if (enrollment == null) {
            return Result.permanentFailure(0, "device-not-enrolled");
        }

        HttpsURLConnection connection = null;
        String boundary = "----ARES-" + UUID.randomUUID();
        try {
            URL url = new URL(ENDPOINT);
            connection = (HttpsURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setConnectTimeout(15000);
            connection.setReadTimeout(45000);
            connection.setInstanceFollowRedirects(false);
            connection.setDoOutput(true);
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
            connection.setRequestProperty("X-ARES-Device-ID", enrollment.deviceId);
            connection.setRequestProperty("X-ARES-Device-Credential", enrollment.deviceCredential);

            try (DataOutputStream output = new DataOutputStream(connection.getOutputStream());
                 FileInputStream input = new FileInputStream(file)) {
                writeUtf8(output, "--" + boundary + "\r\n");
                writeUtf8(output,
                        "Content-Disposition: form-data; name=\"usage_file\"; filename=\""
                                + safeHeaderFileName(file.getName()) + "\"\r\n");
                writeUtf8(output, "Content-Type: text/csv\r\n\r\n");

                byte[] buffer = new byte[8192];
                int read;
                while ((read = input.read(buffer)) != -1) {
                    output.write(buffer, 0, read);
                }

                writeUtf8(output, "\r\n--" + boundary + "--\r\n");
                output.flush();
            }

            int status = connection.getResponseCode();
            String responseBody = readResponseBody(connection, status);
            JSONObject payload = null;
            try {
                if (!responseBody.isEmpty()) {
                    payload = new JSONObject(responseBody);
                }
            } catch (Exception ignored) {
                payload = null;
            }

            if ((status == 200 || status == 201)
                    && payload != null
                    && payload.optBoolean("accepted", false)) {
                String serverStatus = payload.optString("status", "");
                String responseSchool = payload.optString("school_id", "");
                if (("stored".equals(serverStatus) || "duplicate".equals(serverStatus))
                        && enrollment.schoolId.equals(responseSchool)) {
                    return Result.acknowledged(
                            status,
                            serverStatus,
                            payload.optString("filename", file.getName()));
                }
                return Result.permanentFailure(status, "invalid-server-acknowledgement");
            }

            if (status >= 500 || status == 408 || status == 429) {
                return Result.transientFailure(status, errorFromPayload(payload, responseBody));
            }

            return Result.permanentFailure(status, errorFromPayload(payload, responseBody));
        } catch (Exception ex) {
            return Result.transientFailure(0,
                    ex.getClass().getSimpleName() + ": " + String.valueOf(ex.getMessage()));
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private static String errorFromPayload(JSONObject payload, String body) {
        if (payload != null) {
            String error = payload.optString("error", "");
            if (!error.isEmpty()) {
                return error;
            }
        }
        if (body == null || body.trim().isEmpty()) {
            return "central-upload-failed";
        }
        String compact = body.trim().replaceAll("\\s+", " ");
        return compact.length() > 200 ? compact.substring(0, 200) : compact;
    }

    private static String readResponseBody(HttpsURLConnection connection, int status) {
        InputStream stream = null;
        try {
            stream = status >= 400 ? connection.getErrorStream() : connection.getInputStream();
            if (stream == null) {
                return "";
            }
            StringBuilder body = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(stream, StandardCharsets.UTF_8))) {
                char[] buffer = new char[2048];
                int read;
                while ((read = reader.read(buffer)) != -1 && body.length() < 8192) {
                    body.append(buffer, 0, read);
                }
            }
            return body.toString();
        } catch (Exception ignored) {
            return "";
        }
    }

    private static void writeUtf8(DataOutputStream output, String text) throws Exception {
        output.write(text.getBytes(StandardCharsets.UTF_8));
    }

    private static String safeHeaderFileName(String value) {
        return value.replaceAll("[^A-Za-z0-9._-]", "_");
    }

    public static final class Result {
        public final boolean acknowledged;
        public final boolean retryable;
        public final int statusCode;
        public final String serverStatus;
        public final String storedFileName;
        public final String message;

        private Result(
                boolean acknowledged,
                boolean retryable,
                int statusCode,
                String serverStatus,
                String storedFileName,
                String message) {
            this.acknowledged = acknowledged;
            this.retryable = retryable;
            this.statusCode = statusCode;
            this.serverStatus = serverStatus;
            this.storedFileName = storedFileName;
            this.message = message;
        }

        static Result acknowledged(int statusCode, String serverStatus, String storedFileName) {
            return new Result(true, false, statusCode, serverStatus, storedFileName, "");
        }

        static Result transientFailure(int statusCode, String message) {
            return new Result(false, true, statusCode, "", "", message);
        }

        static Result permanentFailure(int statusCode, String message) {
            return new Result(false, false, statusCode, "", "", message);
        }
    }
}
