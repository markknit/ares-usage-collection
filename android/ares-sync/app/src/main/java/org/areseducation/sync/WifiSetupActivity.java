package org.areseducation.sync;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class WifiSetupActivity extends Activity {
    private static final int SAVE_NETWORKS_REQUEST = 2001;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setResult(Activity.RESULT_CANCELED);
        setContentView(createSetupView());
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != SAVE_NETWORKS_REQUEST) {
            return;
        }

        if (AresWifiProvisioner.wasSaveSuccessful(resultCode, data)) {
            setResult(Activity.RESULT_OK, data);
        }
        finish();
    }

    private LinearLayout createSetupView() {
        float density = getResources().getDisplayMetrics().density;
        int sidePadding = Math.round(24f * density);
        int topPadding = Math.round(42f * density);
        int spacing = Math.round(18f * density);

        LinearLayout root = new LinearLayout(this);
        root.setLayoutParams(new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.TOP);
        root.setPadding(sidePadding, topPadding, sidePadding, sidePadding);

        TextView title = new TextView(this);
        title.setText("Finish ARES Wi-Fi setup");
        title.setTextSize(24f);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        root.addView(title, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView body = new TextView(this);
        body.setText("One final step remains. Tap the button below, then use Android's Save button to save ARES2 and ARES. This user-initiated step helps Android present a responsive Wi-Fi confirmation screen.");
        body.setTextSize(17f);
        body.setLineSpacing(0f, 1.15f);
        LinearLayout.LayoutParams bodyParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        bodyParams.topMargin = spacing;
        root.addView(body, bodyParams);

        Button saveButton = new Button(this);
        saveButton.setText("Save ARES Wi-Fi networks");
        saveButton.setMinHeight(Math.round(56f * density));
        saveButton.setOnClickListener(view -> launchSystemSave(saveButton));
        LinearLayout.LayoutParams saveParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        saveParams.topMargin = spacing;
        root.addView(saveButton, saveParams);

        Button laterButton = new Button(this);
        laterButton.setText("Not now");
        laterButton.setOnClickListener(view -> finish());
        LinearLayout.LayoutParams laterParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        laterParams.topMargin = Math.round(10f * density);
        root.addView(laterButton, laterParams);

        return root;
    }

    private void launchSystemSave(Button saveButton) {
        saveButton.setEnabled(false);
        try {
            startActivityForResult(
                    AresWifiProvisioner.createSystemSaveNetworksIntent(),
                    SAVE_NETWORKS_REQUEST);
        } catch (RuntimeException error) {
            saveButton.setEnabled(true);
        }
    }
}
