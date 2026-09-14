package org.areseducation.sync;

import android.content.Context;
import android.util.AttributeSet;
import android.view.View;
import android.widget.Button;
import android.widget.RadioGroup;

public final class AppearanceToggleButton extends Button {
    public AppearanceToggleButton(Context context) {
        super(context);
        initialize();
    }

    public AppearanceToggleButton(Context context, AttributeSet attrs) {
        super(context, attrs);
        initialize();
    }

    public AppearanceToggleButton(Context context, AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        initialize();
    }

    private void initialize() {
        setOnClickListener(view -> {
            View root = getRootView();
            RadioGroup group = root.findViewById(R.id.appearanceGroup);
            if (group == null) {
                return;
            }
            boolean opening = group.getVisibility() != View.VISIBLE;
            group.setVisibility(opening ? View.VISIBLE : View.GONE);
            setText(opening
                    ? "Appearance: hide theme choices"
                    : "Appearance: click here to change theme");
        });
    }
}
