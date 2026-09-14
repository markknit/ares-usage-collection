package org.areseducation.sync;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

public final class WifiSetupActivity extends Activity {
    private static final int SAVE_ARES2_REQUEST = 2001;
    private static final int SAVE_ARES_REQUEST = 2002;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setResult(Activity.RESULT_CANCELED);

        if (savedInstanceState == null) {
            launchSaveRequest(AresWifiProvisioner.SSID_ARES2, SAVE_ARES2_REQUEST);
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == SAVE_ARES2_REQUEST) {
            if (!AresWifiProvisioner.wasSaveSuccessful(resultCode, data)) {
                finish();
                return;
            }
            launchSaveRequest(AresWifiProvisioner.SSID_ARES, SAVE_ARES_REQUEST);
            return;
        }

        if (requestCode == SAVE_ARES_REQUEST) {
            if (AresWifiProvisioner.wasSaveSuccessful(resultCode, data)) {
                setResult(Activity.RESULT_OK);
            }
            finish();
        }
    }

    private void launchSaveRequest(String ssid, int requestCode) {
        try {
            startActivityForResult(
                    AresWifiProvisioner.createSingleNetworkSaveIntent(ssid),
                    requestCode);
        } catch (RuntimeException error) {
            finish();
        }
    }
}
