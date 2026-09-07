<?php
declare(strict_types=1);

require __DIR__ . '/../central-monitoring/web-upload/upload_lib.php';
require __DIR__ . '/../central-monitoring/web-upload/device_auth_lib.php';

function expect_true(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, "FAIL: {$message}\n");
        exit(1);
    }
}

$validName = 'ARES_USAGE_TSAVO3_2026-Q3-MID_2026-08-27_10-20-30.csv';
$parsed = ares_parse_usage_filename($validName);
expect_true($parsed !== null, 'valid filename should parse');
expect_true($parsed['school'] === 'TSAVO3', 'school code should parse');
expect_true($parsed['collection'] === '2026-Q3-MID', 'collection should parse');
expect_true(ares_parse_usage_filename('../' . $validName) === null, 'path traversal must fail');
expect_true(ares_parse_usage_filename('ares_usage_tsavo3.csv') === null, 'invalid filename must fail');
expect_true(ares_parse_usage_filename('ARES_USAGE_TSAVO3_AUTO_2026-08-27_10-20-30.csv') !== null, 'AUTO filename should parse');

$canonicalName = ares_filename_for_school($parsed, 'ARES-S0016');
expect_true(
    $canonicalName === 'ARES_USAGE_ARES-S0016_2026-Q3-MID_2026-08-27_10-20-30.csv',
    'device-authenticated filename should use canonical school ID'
);
expect_true(ares_filename_for_school($parsed, '../bad') === null, 'invalid canonical school ID must fail');

expect_true(ares_is_https(['HTTPS' => 'on']), 'HTTPS=on should be accepted');
expect_true(ares_is_https(['HTTP_X_FORWARDED_PROTO' => 'https']), 'forwarded HTTPS should be accepted');
expect_true(!ares_is_https([]), 'missing HTTPS indicators should fail');
expect_true(ares_extract_upload_key(['HTTP_X_ARES_UPLOAD_KEY' => 'abc']) === 'abc', 'custom header key should parse');
expect_true(ares_extract_upload_key(['HTTP_AUTHORIZATION' => 'Bearer xyz']) === 'xyz', 'bearer key should parse');
expect_true(ares_extract_device_id(['HTTP_X_ARES_DEVICE_ID' => 'ARES-D-ABCDEF123456']) === 'ARES-D-ABCDEF123456', 'device ID header should parse');
expect_true(ares_extract_device_credential(['HTTP_X_ARES_DEVICE_CREDENTIAL' => 'abc123']) === 'abc123', 'device credential header should parse');

$tempDir = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'ares-upload-test-' . bin2hex(random_bytes(6));
expect_true(mkdir($tempDir, 0700, true), 'temporary directory should be created');

$csvPath = $tempDir . DIRECTORY_SEPARATOR . $validName;
file_put_contents($csvPath, "period,metric,value\n2026-Q3,quarter,1\n");
expect_true(ares_plausible_csv($csvPath, 2 * 1024 * 1024), 'valid CSV should be plausible');
expect_true(!ares_plausible_csv($csvPath, 10), 'oversized CSV should fail configured limit');

$badPath = $tempDir . DIRECTORY_SEPARATOR . 'bad.csv';
file_put_contents($badPath, "not a csv payload");
expect_true(!ares_plausible_csv($badPath, 2 * 1024 * 1024), 'non-CSV should fail');

$sha = hash_file('sha256', $csvPath);
expect_true(is_string($sha), 'test SHA should be calculated');
expect_true(ares_target_state($csvPath, $sha) === 'duplicate', 'same file and SHA should be duplicate');
expect_true(ares_target_state($csvPath, str_repeat('0', 64)) === 'conflict', 'same filename with different SHA should conflict');
expect_true(ares_target_state($tempDir . DIRECTORY_SEPARATOR . 'missing.csv', $sha) === 'new', 'missing target should be new');

$deviceId = 'ARES-D-ABCDEF123456';
$credential = str_repeat('a', 64);
$statePath = $tempDir . DIRECTORY_SEPARATOR . 'enrollment_state.json';
$state = [
    'version' => 1,
    'codes' => [],
    'devices' => [
        [
            'device_id' => $deviceId,
            'school_id' => 'ARES-S0016',
            'credential_hash' => hash('sha256', $credential),
            'created_at' => gmdate('c'),
            'label' => 'Test phone',
            'revoked_at' => null,
        ],
    ],
];
file_put_contents($statePath, json_encode($state, JSON_PRETTY_PRINT));

$deviceAuth = ares_authenticate_device($statePath, $deviceId, $credential);
expect_true(($deviceAuth['ok'] ?? false) === true, 'valid device credential should authenticate');
expect_true(($deviceAuth['school_id'] ?? '') === 'ARES-S0016', 'device authentication should return canonical school ID');
expect_true(($deviceAuth['device_id'] ?? '') === $deviceId, 'device authentication should return device ID');

$badCredential = ares_authenticate_device($statePath, $deviceId, str_repeat('b', 64));
expect_true(($badCredential['ok'] ?? true) === false && ($badCredential['error'] ?? '') === 'unauthorized', 'wrong device credential must fail');
$badDevice = ares_authenticate_device($statePath, 'ARES-D-000000000000', $credential);
expect_true(($badDevice['ok'] ?? true) === false && ($badDevice['error'] ?? '') === 'unauthorized', 'unknown device must fail');

$state['devices'][0]['revoked_at'] = gmdate('c');
file_put_contents($statePath, json_encode($state, JSON_PRETTY_PRINT));
$revoked = ares_authenticate_device($statePath, $deviceId, $credential);
expect_true(($revoked['ok'] ?? true) === false && ($revoked['error'] ?? '') === 'unauthorized', 'revoked device must fail');

unlink($csvPath);
unlink($badPath);
unlink($statePath);
rmdir($tempDir);

echo "ARES web upload tests passed\n";
