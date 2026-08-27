package org.areseducation.sync;

import android.content.Context;
import android.content.SharedPreferences;

import java.time.LocalDate;
import java.time.ZoneId;
import java.util.Arrays;
import java.util.List;

public final class CollectionSchedule {
    public static final ZoneId SCHOOL_ZONE = ZoneId.of("Africa/Nairobi");
    private static final String PREFS = "collection_state";
    private static final String COMPLETE_PREFIX = "completed_";

    public static final class Collection {
        public final String id;
        public final String label;
        public final LocalDate dueDate;

        Collection(String id, String label, String dueDate) {
            this.id = id;
            this.label = label;
            this.dueDate = LocalDate.parse(dueDate);
        }
    }

    private static final List<Collection> COLLECTIONS = Arrays.asList(
            new Collection("2026-Q3-MID", "Quarter 3 mid-quarter", "2026-08-14"),
            new Collection("2026-Q3-END", "Quarter 3 end-quarter", "2026-09-25"),
            new Collection("2026-Q4-MID", "Quarter 4 mid-quarter", "2026-11-06"),
            new Collection("2026-Q4-END", "Quarter 4 end-quarter", "2026-12-11")
    );

    private CollectionSchedule() {
    }

    public static List<Collection> all() {
        return COLLECTIONS;
    }

    public static LocalDate todayAtSchool() {
        return LocalDate.now(SCHOOL_ZONE);
    }

    public static Collection getPendingDueCollection(Context context) {
        LocalDate today = todayAtSchool();
        for (Collection collection : COLLECTIONS) {
            if (!collection.dueDate.isAfter(today) && !isCompleted(context, collection.id)) {
                return collection;
            }
        }
        return null;
    }

    public static Collection getNextIncompleteCollection(Context context) {
        for (Collection collection : COLLECTIONS) {
            if (!isCompleted(context, collection.id)) {
                return collection;
            }
        }
        return null;
    }

    public static Collection find(String id) {
        if (id == null) {
            return null;
        }
        for (Collection collection : COLLECTIONS) {
            if (collection.id.equals(id)) {
                return collection;
            }
        }
        return null;
    }

    public static boolean isCompleted(Context context, String id) {
        SharedPreferences prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return prefs.getBoolean(COMPLETE_PREFIX + id, false);
    }

    public static void markCompleted(Context context, String id) {
        if (find(id) == null) {
            return;
        }
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit()
                .putBoolean(COMPLETE_PREFIX + id, true)
                .apply();
    }
}
