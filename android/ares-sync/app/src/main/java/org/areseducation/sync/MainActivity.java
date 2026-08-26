package org.areseducation.sync;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;

public final class MainActivity extends Activity {
    private static final int WIFI_PERMISSION_REQUEST = 1001;

    private TextView statusText;
    private Button testButton;
    private AresWifiConnector wifiConnector;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        statusText = findViewById(R.id.statusText);
        testButton = findViewById(R.id.testButton);
        wifiConnector = new AresWifiConnector(this);

        statusText.setText(R.string.status_ready);
        testButton.setOnClickListener(view -> beginTest());
    }

    private void beginTest() {
        if (!hasWifiPermission()) {
            requestWifiPermission();
            return;
        }

        testButton.setEnabled(false);
        setStatus("Requesting ARES2…\n\nAndroid may ask you to approve the Wi-Fi connection.");

        wifiConnector.requestAres2(new AresWifiConnector.Callback() {
            @Override
            public void onAvailable(android.net.Network network) {
                runOnUiThread(() -> setStatus(
                        "✓ ARES2 network available\n\nTesting http://ares.local…"));

                AresServerClient.testAndDownload(
                        MainActivity.this,
                        network,
                        new AresServerClient.Callback() {
                            @Override
                            public void onSuccess(AresServerClient.Result result) {
                                runOnUiThread(() -> {
                                    StringBuilder message = new StringBuilder();
                                    message.append("✓ ARES2 network available\n");
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
                                        message.append("Saved in app-private pending storage");
                                    } else if (result.statusCode == 204) {
                                        message.append("No collection is currently due.");
                                    }

                                    setStatus(message.toString());
                                    testButton.setEnabled(true);
                                });
                            }

                            @Override
                            public void onError(String message) {
                                runOnUiThread(() -> {
                                    setStatus("✓ ARES2 network available\n✗ Server/download test failed\n\n" + message);
                                    testButton.setEnabled(true);
                                });
                            }
                        });
            }

            @Override
            public void onUnavailable() {
                runOnUiThread(() -> {
                    setStatus("✗ ARES2 connection was not established.\n\nConfirm the ARES2 hotspot is active and try again.");
                    testButton.setEnabled(true);
                });
            }

            @Override
            public void onError(String message) {
                runOnUiThread(() -> {
                    setStatus("✗ Wi-Fi request failed\n\n" + message);
                    testButton.setEnabled(true);
                });
            }
        });
    }

    private boolean hasWifiPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            return checkSelfPermission(Manifest.permission.NEARBY_WIFI_DEVICES)
                    == PackageManager.PERMISSION_GRANTED;
        }
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                == PackageManager.PERMISSION_GRANTED;
    }

    private void requestWifiPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            requestPermissions(
                    new String[]{Manifest.permission.NEARBY_WIFI_DEVICES},
                    WIFI_PERMISSION_REQUEST);
        } else {
            requestPermissions(
                    new String[]{Manifest.permission.ACCESS_FINE_LOCATION},
                    WIFI_PERMISSION_REQUEST);
        }
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
            beginTest();
        } else {
            setStatus("Nearby Wi-Fi permission is required to connect to ARES2.");
        }
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
