package org.areseducation.sync;

import android.content.Context;

import androidx.annotation.NonNull;
import androidx.work.Data;
import androidx.work.ExistingWorkPolicy;
import androidx.work.OneTimeWorkRequest;
import androidx.work.WorkManager;

public final class CollectionAttemptScheduler {
    private static final String WORK_PREFIX = "ares-local-collection-";

    private CollectionAttemptScheduler() {
    }

    public static void enqueue(Context context, String collectionId) {
        if (!EnrollmentStore.isEnrolled(context)
                || collectionId == null
                || CollectionSchedule.isCompleted(context, collectionId)) {
            return;
        }

        Data input = new Data.Builder()
                .putString(CollectionReminderReceiver.EXTRA_COLLECTION_ID, collectionId)
                .build();

        OneTimeWorkRequest request = new OneTimeWorkRequest.Builder(CollectionAttemptWorker.class)
                .setInputData(input)
                .build();

        WorkManager.getInstance(context.getApplicationContext()).enqueueUniqueWork(
                WORK_PREFIX + collectionId,
                ExistingWorkPolicy.KEEP,
                request);
    }
}
