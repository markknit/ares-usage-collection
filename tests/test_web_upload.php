<?php
declare(strict_types=1);

require __DIR__ . '/../central-monitoring/web-upload/upload_lib.php';

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

expect_true(ares_is_https(['HTTPS' => 'on']), 'HTTPS=on should be accepted');
expect_true(ares_is_https(['HTTP_X_FORWARDED_PROTO' => 'https']), 'forwarded HTTPS should be accepted');
expect_true(!ares_is_https([]), 'missing HTTPS indicators should fail');
expect_true(ares_extract_upload_key(['HTTP_X_ARES_UPLOAD_KEY' => 'abc']) === 'abc', 'custom header key should parse');
expect_true(ares_extract_upload_key(['HTTP_AUTHORIZATION' => 'Bearer xyz']) === 'xyz', 'bearer key should parse');

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

unlink($csvPath);
unlink($badPath);
rmdir($tempDir);

echo "ARES web upload tests passed\n";
