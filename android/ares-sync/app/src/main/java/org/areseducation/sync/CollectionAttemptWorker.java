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
            Network currentWifi = connector.getCurrentWifiNetwork();
            if (currentWifi != null && tryDownload(context, currentWifi, collection)) {
                return Result.success();
            }

            if (!AresWifiProvisioner.isComplete(context)) {
                CollectionNotification.show(context, collection);
                return Result.retry();
            }

            Network aresNetwork;
            try {
                aresNetwork = connector.requestPreferredAresNetworkBlocking(30_000L);
            } catch (InterruptedException error) {
                Thread.currentThread().interrupt();
                CollectionNotification.show(context, collection);
                return Result.retry();
            } catch (RuntimeException error) {
                CollectionNotification.show(context, collection);
                return Result.retry();
            }

            if (aresNetwork == null || !tryDownload(context, aresNetwork, collection)) {
                CollectionNotification.show(context, collection);
                return Result.retry();
            }

            return Result.success();
        } finally {
            connector.close();
        }
    }

    private boolean tryDownload(
            Context context,
            Network network,
            CollectionSchedule.Collection collection) {
        AresServerClient.Result download;
        try {
            download = AresServerClient.downloadBlocking(context, network, collection.id);
        } catch (Exception ex) {
            return false;
        }

        if (download.statusCode != 200 || download.fileName == null) {
            return false;
        }

        CollectionSchedule.markCompleted(context, collection.id);
        CollectionReminderScheduler.cancel(context, collection.id);
        CollectionNotification.cancel(context, collection.id);
        CentralUploadScheduler.enqueuePending(context);
        CollectionReminderScheduler.scheduleAll(context);
        return true;
    }
}
