package org.areseducation.sync;

import android.content.Context;

import androidx.work.BackoffPolicy;
import androidx.work.Constraints;
import androidx.work.ExistingWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.OneTimeWorkRequest;
import androidx.work.WorkManager;

import java.util.concurrent.TimeUnit;

public final class CentralUploadScheduler {
    private static final String UNIQUE_WORK_NAME = "ares-central-pending-upload";

    private CentralUploadScheduler() {
    }

    public static void enqueuePending(Context context) {
        Context appContext = context.getApplicationContext();
        if (!EnrollmentStore.isEnrolled(appContext)
                || PendingUploadStore.pendingCount(appContext) == 0) {
            return;
        }

        Constraints constraints = new Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build();

        OneTimeWorkRequest request = new OneTimeWorkRequest.Builder(CentralUploadWorker.class)
                .setConstraints(constraints)
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
                .build();

        WorkManager.getInstance(appContext).enqueueUniqueWork(
                UNIQUE_WORK_NAME,
                ExistingWorkPolicy.KEEP,
                request);
    }
}
