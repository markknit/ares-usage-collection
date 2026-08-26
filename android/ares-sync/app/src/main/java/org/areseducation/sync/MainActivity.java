package org.areseducation.sync;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.net.Network;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;

public final class MainActivity extends Activity {
    private static final int WIFI_PERMISSION_REQUEST = 1001;

    private TextView statusText;
    private Button switchTestButton;
    private Button currentNetworkTestButton;
    private AresWifiConnector wifiConnector;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        statusText = findViewById(R.id.statusText);
        switchTestButton = findViewById(R.id.switchTestButton);
        currentNetworkTestButton = findViewById(R.id.currentNetworkTestButton);
        wifiConnector = new AresWifiConnector(this);

        statusText.setText(R.string.status_ready);
        switchTestButton.setOnClickListener(view -> beginSwitchTest());
        currentNetworkTestButton.setOnClickListener(view -> beginCurrentNetworkTest());
    }

    private void beginSwitchTest() {
        if (!hasWifiPermission()) {
            requestWifiPermission();
            return;
        }

        setButtonsEnabled(false);
        setStatus("Requesting exact ARES2 connection…\n\n"
                + "This build targets Android 11/API 30 compatibility behavior. "
                + "Android should temporarily leave the current Wi-Fi network before connecting to ARES2.\n\n"
                + wifiConnector.getDiagnostics());

        wifiConnector.requestAres2(new AresWifiConnector.Callback() {
            @Override
            public void onAvailable(Network network) {
                runOnUiThread(() -> setStatus(
                        "✓ Android supplied an ARES2 Wi-Fi network\n"
                                + "Testing http://ares.local…\n\n"
                                + wifiConnector.getDiagnostics()));
                runServerTest(network, true);
            }

            @Override
            public void onUnavailable() {
                runOnUiThread(() -> {
                    setStatus("✗ Android could not satisfy the ARES2 switch request.\n\n"
                            + wifiConnector.getDiagnostics());
                    setButtonsEnabled(true);
                });
            }

            @Override
            public void onFailure(String message) {
                runOnUiThread(() -> {
                    setStatus("✗ ARES2 connection failed\n\nReason: " + message
                            + "\n\n" + wifiConnector.getDiagnostics());
                    setButtonsEnabled(true);
                });
            }

            @Override
            public void onError(String message) {
                runOnUiThread(() -> {
                    setStatus("✗ Wi-Fi request failed\n\n" + message
                            + "\n\n" + wifiConnector.getDiagnostics());
                    setButtonsEnabled(true);
                });
            }
        });
    }

    private void beginCurrentNetworkTest() {
        Network wifiNetwork = wifiConnector.getCurrentWifiNetwork();
        if (wifiNetwork == null) {
            setStatus("✗ No currently connected Wi-Fi network was found.\n\n"
                    + "For this manual test, connect the phone to ARES2 in Android Wi-Fi settings, then return here and try again.\n\n"
                    + wifiConnector.getDiagnostics());
            return;
        }

        setButtonsEnabled(false);
        setStatus("Testing http://ares.local over the phone's current Wi-Fi connection…\n\n"
                + wifiConnector.getDiagnostics());
        runServerTest(wifiNetwork, false);
    }

    private void runServerTest(Network network, boolean releaseAfterTest) {
        AresServerClient.testAndDownload(
                this,
                network,
                new AresServerClient.Callback() {
                    @Override
                    public void onSuccess(AresServerClient.Result result) {
                        if (releaseAfterTest) {
                            wifiConnector.release();
                        }
                        runOnUiThread(() -> {
                            StringBuilder message = new StringBuilder();
                            message.append("✓ ARES server reached\n");
                            message.append("HTTP status: ").append(result.statusCode).append("\n");

                            if (result.collectionId != null && !result.collectionId.isEmpty()) {
                                message.append("Collection: ").append(result.collectionId).append("\n");
                            }
                            if (result.dueDate != null && !result.dueDate.isEmpty()) {
                                message.append("Due date: ").append(result.dueDate).append("\n");
                            }
                            if (result.fileName != null) {
                                message.append("✓ Downloaded: ").append(result.fileName).append("\n");
                                message.append("Bytes: ").append(result.byteCount).append("\n");
                                message.append("Saved in app-private pending storage\n");
                            } else if (result.statusCode == 204) {
                                message.append("No collection is currently due.\n");
                            }

                            if (releaseAfterTest) {
                                message.append("✓ Released ARES2 request\n");
                                message.append("Now watch whether Android reconnects to the previous Internet Wi-Fi.\n");
                            }

                            message.append("\n").append(wifiConnector.getDiagnostics());
                            setStatus(message.toString());
                            setButtonsEnabled(true);
                        });
                    }

                    @Override
                    public void onError(String message) {
                        if (releaseAfterTest) {
                            wifiConnector.release();
                        }
                        runOnUiThread(() -> {
                            setStatus("✗ Server/download test failed\n\n" + message
                                    + (releaseAfterTest
                                    ? "\n\nARES2 request released; observe whether normal Wi-Fi reconnects."
                                    : "")
                                    + "\n\n" + wifiConnector.getDiagnostics());
                            setButtonsEnabled(true);
                        });
                    }
                });
    }

    private boolean hasWifiPermission() {
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                == PackageManager.PERMISSION_GRANTED;
    }

    private void requestWifiPermission() {
        requestPermissions(
                new String[]{Manifest.permission.ACCESS_FINE_LOCATION},
                WIFI_PERMISSION_REQUEST);
    }

    @Override
    public void onRequestPermissionsResult(
            int requestCode,
            String[] permissions,
            int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != WIFI_PERMISSION_REQUEST) {
            return;
        }

        if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            beginSwitchTest();
        } else {
            setStatus("Location permission is required by Android for this API-30 Wi-Fi compatibility test.");
        }
    }

    private void setButtonsEnabled(boolean enabled) {
        switchTestButton.setEnabled(enabled);
        currentNetworkTestButton.setEnabled(enabled);
    }

    private void setStatus(String message) {
        statusText.setText(message);
    }

    @Override
    protected void onDestroy() {
        wifiConnector.release();
        super.onDestroy();
    }
}
