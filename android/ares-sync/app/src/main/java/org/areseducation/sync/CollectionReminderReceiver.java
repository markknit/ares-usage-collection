package org.areseducation.sync;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public final class CollectionReminderReceiver extends BroadcastReceiver {
    public static final String EXTRA_COLLECTION_ID = "collection_id";

    @Override
    public void onReceive(Context context, Intent intent) {
        String collectionId = intent == null ? null : intent.getStringExtra(EXTRA_COLLECTION_ID);
        CollectionSchedule.Collection collection = CollectionSchedule.find(collectionId);
        if (collection != null
                && !CollectionSchedule.isCompleted(context, collection.id)
                && !collection.dueDate.isAfter(CollectionSchedule.todayAtSchool())) {
            CollectionNotification.show(context, collection);
        }
        CollectionReminderScheduler.scheduleAll(context);
    }
}
