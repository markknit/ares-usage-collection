package org.areseducation.sync;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;

import java.time.ZonedDateTime;

public final class CollectionReminderScheduler {
    private CollectionReminderScheduler() {
    }

    public static void scheduleAll(Context context) {
        AlarmManager alarmManager = context.getSystemService(AlarmManager.class);
        if (alarmManager == null) {
            return;
        }

        if (!EnrollmentStore.isEnrolled(context)) {
            for (CollectionSchedule.Collection collection : CollectionSchedule.all()) {
                alarmManager.cancel(reminderPendingIntent(context, collection.id));
                CollectionNotification.cancel(context, collection.id);
            }
            return;
        }

        long now = System.currentTimeMillis();
        for (CollectionSchedule.Collection collection : CollectionSchedule.all()) {
            PendingIntent pendingIntent = reminderPendingIntent(context, collection.id);

            if (CollectionSchedule.isCompleted(context, collection.id)) {
                alarmManager.cancel(pendingIntent);
                continue;
            }

            long triggerAt = ZonedDateTime.of(
                    collection.dueDate,
                    java.time.LocalTime.of(8, 0),
                    CollectionSchedule.SCHOOL_ZONE)
                    .toInstant()
                    .toEpochMilli();

            if (triggerAt > now) {
                alarmManager.setAndAllowWhileIdle(
                        AlarmManager.RTC_WAKEUP,
                        triggerAt,
                        pendingIntent);
            }
        }
    }

    public static void cancel(Context context, String collectionId) {
        AlarmManager alarmManager = context.getSystemService(AlarmManager.class);
        if (alarmManager != null) {
            alarmManager.cancel(reminderPendingIntent(context, collectionId));
        }
    }

    private static PendingIntent reminderPendingIntent(Context context, String collectionId) {
        Intent intent = new Intent(context, CollectionReminderReceiver.class);
        intent.putExtra(CollectionReminderReceiver.EXTRA_COLLECTION_ID, collectionId);
        return PendingIntent.getBroadcast(
                context,
                collectionId.hashCode(),
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }
}
