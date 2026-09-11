package org.areseducation.sync;

import android.content.Context;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.TextView;

import java.util.List;

final class SchoolSpinnerAdapter extends ArrayAdapter<EnrollmentClient.School> {
    private int textColor = Color.BLACK;
    private int backgroundColor = Color.WHITE;
    private int borderColor = Color.LTGRAY;

    SchoolSpinnerAdapter(Context context, List<EnrollmentClient.School> schools) {
        super(context, android.R.layout.simple_spinner_item, schools);
    }

    void setPalette(int textColor, int backgroundColor, int borderColor) {
        this.textColor = textColor;
        this.backgroundColor = backgroundColor;
        this.borderColor = borderColor;
        notifyDataSetChanged();
    }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        return buildRow(position, 14, 14);
    }

    @Override
    public View getDropDownView(int position, View convertView, ViewGroup parent) {
        return buildRow(position, 16, 16);
    }

    private View buildRow(int position, int verticalPadding, int horizontalPadding) {
        TextView row = new TextView(getContext());
        EnrollmentClient.School school = getItem(position);
        row.setText(school == null ? "" : school.toString());
        row.setTextColor(textColor);
        row.setTextSize(17f);
        row.setGravity(Gravity.CENTER_VERTICAL);
        int density = Math.max(1, Math.round(getContext().getResources().getDisplayMetrics().density));
        row.setPadding(horizontalPadding * density, verticalPadding * density,
                horizontalPadding * density, verticalPadding * density);
        GradientDrawable background = new GradientDrawable();
        background.setColor(backgroundColor);
        background.setStroke(Math.max(1, density), borderColor);
        row.setBackground(background);
        return row;
    }
}
