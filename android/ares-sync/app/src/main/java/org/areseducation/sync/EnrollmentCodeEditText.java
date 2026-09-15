package org.areseducation.sync;

import android.content.Context;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.AttributeSet;
import android.widget.EditText;

import java.util.Locale;

public final class EnrollmentCodeEditText extends EditText {
    private boolean formatting;

    public EnrollmentCodeEditText(Context context) {
        super(context);
        initialize();
    }

    public EnrollmentCodeEditText(Context context, AttributeSet attrs) {
        super(context, attrs);
        initialize();
    }

    public EnrollmentCodeEditText(Context context, AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        initialize();
    }

    private void initialize() {
        addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {
            }

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
            }

            @Override
            public void afterTextChanged(Editable editable) {
                if (formatting) {
                    return;
                }

                String raw = editable.toString()
                        .replaceAll("[^A-Za-z0-9]", "")
                        .toUpperCase(Locale.US);
                if (raw.length() > 8) {
                    raw = raw.substring(0, 8);
                }

                String formatted = raw.length() <= 4
                        ? raw
                        : raw.substring(0, 4) + "-" + raw.substring(4);
                if (formatted.equals(editable.toString())) {
                    return;
                }

                formatting = true;
                setText(formatted);
                setSelection(formatted.length());
                formatting = false;
            }
        });
    }
}
