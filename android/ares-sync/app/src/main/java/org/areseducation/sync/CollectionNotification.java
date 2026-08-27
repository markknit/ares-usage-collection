package org.areseducation.sync;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;

public final class CollectionNotification {
    private static final String CHANNEL_ID = "collection_reminders";

    private CollectionNotification() {
    }

    public static void ensureChannel(Context context) {
        NotificationManager manager = context.getSystemService(NotificationManager.class);
        if (manager == null) {
            return;
        }
        NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "ARES collection reminders",
                NotificationManager.IMPORTANCE_HIGH);
        channel.setDescription("Reminders to connect the phone to ARES2 or ARES for scheduled usage collection.");
        manager.createNotificationChannel(channel);
    }

    public static boolean canNotify(Context context) {
        return Build.VERSION.SDK_INT < 33
                || context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                == PackageManager.PERMISSION_GRANTED;
    }

    public static void showIfDue(Context context) {
        CollectionSchedule.Collection due = CollectionSchedule.getPendingDueCollection(context);
        if (due != null) {
            show(context, due);
        }
    }

    public static void show(Context context, CollectionSchedule.Collection collection) {
        ensureChannel(context);
        if (!canNotify(context) || CollectionSchedule.isCompleted(context, collection.id)) {
            return;
        }

        Intent launchIntent = new Intent(context, MainActivity.class);
        launchIntent.setAction(MainActivity.ACTION_COLLECTION_DUE);
        launchIntent.putExtra(MainActivity.EXTRA_COLLECTION_ID, collection.id);
        launchIntent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);

        PendingIntent contentIntent = PendingIntent.getActivity(
                context,
                collection.id.hashCode(),
                launchIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        Notification notification = new Notification.Builder(context, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.stat_notify_sync)
                .setContentTitle("ARES usage collection due")
                .setContentText("At school, tap to choose ARES2 or ARES and collect usage data.")
                .setStyle(new Notification.BigTextStyle().bigText(
                        collection.label + " was due " + collection.dueDate
                                + ". At school, tap this reminder, choose ARES2 or ARES, then return to ARES Sync. The download will start automatically."))
                .setContentIntent(contentIntent)
                .setAutoCancel(true)
                .setOnlyAlertOnce(true)
                .build();

        NotificationManager manager = context.getSystemService(NotificationManager.class);
        if (manager != null) {
            manager.notify(collection.id.hashCode(), notification);
        }
    }

    public static void cancel(Context context, String collectionId) {
        NotificationManager manager = context.getSystemService(NotificationManager.class);
        if (manager != null) {
            manager.cancel(collectionId.hashCode());
        }
    }
}
