package org.areseducation.sync;

import android.content.Context;
import android.net.Network;

import androidx.annotation.NonNull;
import androidx.work.Worker;
import androidx.work.WorkerParameters;

public final class CollectionAttemptWorker extends Worker {
    public CollectionAttemptWorker(
            @NonNull Context appContext,
            @NonNull WorkerParameters workerParams) {
        super(appContext, workerParams);
    }

    @NonNull
    @Override
    public Result doWork() {
        Context context = getApplicationContext();
        String collectionId = getInputData().getString(CollectionReminderReceiver.EXTRA_COLLECTION_ID);
        CollectionSchedule.Collection collection = CollectionSchedule.find(collectionId);

        if (!EnrollmentStore.isEnrolled(context)
                || collection == null
                || CollectionSchedule.isCompleted(context, collection.id)
                || collection.dueDate.isAfter(CollectionSchedule.todayAtSchool())) {
            return Result.success();
        }

        AresWifiConnector connector = new AresWifiConnector(context);
        try {
            Network wifiNetwork = connector.getCurrentWifiNetwork();
            if (wifiNetwork == null) {
                CollectionNotification.show(context, collection);
                return Result.success();
            }

            AresServerClient.Result download;
            try {
                download = AresServerClient.downloadBlocking(context, wifiNetwork, collection.id);
            } catch (Exception ex) {
                CollectionNotification.show(context, collection);
                return Result.success();
            }

            if (download.statusCode != 200 || download.fileName == null) {
                CollectionNotification.show(context, collection);
                return Result.success();
            }

            CollectionSchedule.markCompleted(context, collection.id);
            CollectionReminderScheduler.cancel(context, collection.id);
            CollectionNotification.cancel(context, collection.id);
            CentralUploadScheduler.enqueuePending(context);
            CollectionReminderScheduler.scheduleAll(context);
            return Result.success();
        } finally {
            connector.close();
        }
    }
}
