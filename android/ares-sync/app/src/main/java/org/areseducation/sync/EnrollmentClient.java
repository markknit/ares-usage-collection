package org.areseducation.sync;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import javax.net.ssl.HttpsURLConnection;

import java.net.URL;

public final class EnrollmentClient {
    private static final String BASE_URL = "https://areseducation.org/monitor_upload/";
    private static final int CONNECT_TIMEOUT_MS = 10_000;
    private static final int READ_TIMEOUT_MS = 20_000;
    private static final ExecutorService EXECUTOR = Executors.newSingleThreadExecutor();

    private EnrollmentClient() {
    }

    public static void searchSchools(String query, SearchCallback callback) {
        EXECUTOR.execute(() -> {
            try {
                callback.onSuccess(searchSchoolsBlocking(query));
            } catch (Exception error) {
                callback.onError(messageFor(error));
            }
        });
    }

    public static void enroll(
            String schoolId,
            String enrollmentCode,
            String deviceLabel,
            EnrollmentCallback callback) {
        EXECUTOR.execute(() -> {
            try {
                callback.onSuccess(enrollBlocking(schoolId, enrollmentCode, deviceLabel));
            } catch (Exception error) {
                callback.onError(messageFor(error));
            }
        });
    }

    private static List<School> searchSchoolsBlocking(String query) throws IOException, JSONException {
        String encoded = URLEncoder.encode(query.trim(), StandardCharsets.UTF_8.name());
        URL url = new URL(BASE_URL + "schools.php?q=" + encoded);
        HttpsURLConnection connection = open(url);
        connection.setRequestMethod("GET");
        connection.setRequestProperty("Accept", "application/json");

        int status = connection.getResponseCode();
        String body = readResponse(connection, status);
        if (status != 200) {
            throw new IOException(serverError(status, body));
        }

        JSONObject root = new JSONObject(body);
        if (!root.optBoolean("ok", false)) {
            throw new IOException(serverError(status, body));
        }

        JSONArray matches = root.optJSONArray("matches");
        List<School> schools = new ArrayList<>();
        if (matches == null) {
            return schools;
        }

        for (int index = 0; index < matches.length(); index++) {
            JSONObject item = matches.optJSONObject(index);
            if (item == null) {
                continue;
            }
            String schoolId = item.optString("school_id", "").trim();
            String canonicalName = item.optString("canonical_name", "").trim();
            if (!schoolId.isEmpty() && !canonicalName.isEmpty()) {
                schools.add(new School(schoolId, canonicalName));
            }
        }
        return schools;
    }

    private static EnrollmentResult enrollBlocking(
            String schoolId,
            String enrollmentCode,
            String deviceLabel) throws IOException, JSONException {
        URL url = new URL(BASE_URL + "enroll.php");
        HttpsURLConnection connection = open(url);
        connection.setRequestMethod("POST");
        connection.setDoOutput(true);
        connection.setRequestProperty("Accept", "application/json");
        connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");

        JSONObject request = new JSONObject();
        request.put("school_id", schoolId);
        request.put("enrollment_code", enrollmentCode);
        request.put("device_label", deviceLabel);
        byte[] payload = request.toString().getBytes(StandardCharsets.UTF_8);
        connection.setFixedLengthStreamingMode(payload.length);

        try (OutputStream output = connection.getOutputStream()) {
            output.write(payload);
        }

        int status = connection.getResponseCode();
        String body = readResponse(connection, status);
        if (status != 201) {
            throw new IOException(serverError(status, body));
        }

        JSONObject root = new JSONObject(body);
        if (!root.optBoolean("ok", false)) {
            throw new IOException(serverError(status, body));
        }

        String resultSchoolId = root.optString("school_id", "").trim();
        String canonicalName = root.optString("canonical_name", "").trim();
        String deviceId = root.optString("device_id", "").trim();
        String deviceCredential = root.optString("device_credential", "").trim();
        if (resultSchoolId.isEmpty()
                || canonicalName.isEmpty()
                || deviceId.isEmpty()
                || deviceCredential.isEmpty()) {
            throw new IOException("Enrollment service returned an incomplete success response.");
        }

        return new EnrollmentResult(
                resultSchoolId,
                canonicalName,
                deviceId,
                deviceCredential);
    }

    private static HttpsURLConnection open(URL url) throws IOException {
        HttpsURLConnection connection = (HttpsURLConnection) url.openConnection();
        connection.setConnectTimeout(CONNECT_TIMEOUT_MS);
        connection.setReadTimeout(READ_TIMEOUT_MS);
        connection.setUseCaches(false);
        connection.setInstanceFollowRedirects(false);
        return connection;
    }

    private static String readResponse(HttpsURLConnection connection, int status) throws IOException {
        InputStream stream = status >= 200 && status < 400
                ? connection.getInputStream()
                : connection.getErrorStream();
        if (stream == null) {
            return "";
        }

        StringBuilder body = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                body.append(line);
            }
        }
        return body.toString();
    }

    private static String serverError(int status, String body) {
        try {
            JSONObject root = new JSONObject(body);
            String error = root.optString("error", "").trim();
            if (!error.isEmpty()) {
                return "Enrollment service error: " + error + " (HTTP " + status + ")";
            }
        } catch (JSONException ignored) {
            // Fall through to the generic HTTP error.
        }

        if (status >= 300 && status < 400) {
            return "Enrollment service redirected unexpectedly (HTTP " + status + ").";
        }
        return "Enrollment service returned HTTP " + status + ".";
    }

    private static String messageFor(Exception error) {
        String message = error.getMessage();
        if (message == null || message.trim().isEmpty()) {
            return error.getClass().getSimpleName();
        }
        return message;
    }

    public interface SearchCallback {
        void onSuccess(List<School> schools);

        void onError(String message);
    }

    public interface EnrollmentCallback {
        void onSuccess(EnrollmentResult result);

        void onError(String message);
    }

    public static final class School {
        public final String schoolId;
        public final String canonicalName;

        School(String schoolId, String canonicalName) {
            this.schoolId = schoolId;
            this.canonicalName = canonicalName;
        }

        @Override
        public String toString() {
            return canonicalName;
        }
    }

    public static final class EnrollmentResult {
        public final String schoolId;
        public final String canonicalName;
        public final String deviceId;
        public final String deviceCredential;

        EnrollmentResult(
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
