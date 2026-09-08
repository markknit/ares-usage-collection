package org.areseducation.sync;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;

import androidx.annotation.NonNull;
import androidx.work.Worker;
import androidx.work.WorkerParameters;

import java.io.File;

public final class CentralUploadWorker extends Worker {
    public CentralUploadWorker(
            @NonNull Context appContext,
            @NonNull WorkerParameters workerParams) {
        super(appContext, workerParams);
    }

    @NonNull
    @Override
    public Result doWork() {
        Context context = getApplicationContext();
        EnrollmentStore.Enrollment enrollment = EnrollmentStore.get(context);
        if (enrollment == null) {
            PendingUploadStore.record(context, "blocked", "", "device-not-enrolled");
            return Result.failure();
        }

        File[] files = PendingUploadStore.pendingFiles(context);
        if (files.length == 0) {
            PendingUploadStore.record(context, "idle", "", "no-pending-files");
            return Result.success();
        }

        if (!hasValidatedInternet(context)) {
            PendingUploadStore.record(
                    context,
                    "waiting",
                    files[0].getName(),
                    "validated-internet-not-available");
            return Result.retry();
        }

        boolean permanentFailure = false;
        for (File file : files) {
            CentralUploadClient.Result upload = CentralUploadClient.upload(file, enrollment);
            if (upload.acknowledged) {
                if (!PendingUploadStore.moveToSent(context, file, upload.storedFileName)) {
                    PendingUploadStore.record(
                            context,
                            "waiting",
                            file.getName(),
                            "server-acknowledged-but-local-move-failed");
                    return Result.retry();
                }
                PendingUploadStore.record(
                        context,
                        "sent",
                        upload.storedFileName,
                        upload.serverStatus + " (HTTP " + upload.statusCode + ")");
                continue;
            }

            if (upload.retryable) {
                PendingUploadStore.record(
                        context,
                        "waiting",
                        file.getName(),
                        upload.message + statusSuffix(upload.statusCode));
                return Result.retry();
            }

            permanentFailure = true;
            PendingUploadStore.record(
                    context,
                    "blocked",
                    file.getName(),
                    upload.message + statusSuffix(upload.statusCode));
        }

        return permanentFailure ? Result.failure() : Result.success();
    }

    private static boolean hasValidatedInternet(Context context) {
        ConnectivityManager manager = context.getSystemService(ConnectivityManager.class);
        if (manager == null) {
            return false;
        }
        Network network = manager.getActiveNetwork();
        if (network == null) {
            return false;
        }
        NetworkCapabilities capabilities = manager.getNetworkCapabilities(network);
        return capabilities != null
                && capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
                && capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED);
    }

    private static String statusSuffix(int statusCode) {
        return statusCode > 0 ? " (HTTP " + statusCode + ")" : "";
    }
}
