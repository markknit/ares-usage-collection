<?php
declare(strict_types=1);

require __DIR__ . '/../central-monitoring/web-upload/enrollment_lib.php';

function enrollment_expect(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, "FAIL: {$message}\n");
        exit(1);
    }
}

$registry = [
    'version' => 1,
    'schools' => [
        ['school_id' => 'ARES-S0001', 'canonical_name' => 'Misuuni Sec', 'aliases' => ['Misuuni Secondary'], 'active' => true],
        ['school_id' => 'ARES-S0002', 'canonical_name' => 'Laikipia Air base sec', 'aliases' => [], 'active' => true],
        ['school_id' => 'ARES-S0003', 'canonical_name' => 'Retired School', 'aliases' => [], 'active' => false],
    ],
];

enrollment_expect(ares_validate_school_registry($registry), 'valid registry should pass');
$invalidRegistry = $registry;
$invalidRegistry['schools'][1]['school_id'] = 'ARES-S0001';
enrollment_expect(!ares_validate_school_registry($invalidRegistry), 'duplicate school IDs must fail');

enrollment_expect(ares_normalize_school_text('Misuuni Secondary School') === 'misuuni sec', 'secondary/school normalization should work');
enrollment_expect(ares_normalize_school_text('Laikipia Airbase Sec') === 'laikipia air base sec', 'airbase normalization should work');

$matches = ares_search_schools($registry, 'misuuni secondary', 8);
enrollment_expect(count($matches) >= 1 && $matches[0]['school_id'] === 'ARES-S0001', 'Misuuni variation should resolve to canonical school');
$airMatches = ares_search_schools($registry, 'laikipia airbase', 8);
enrollment_expect(count($airMatches) >= 1 && $airMatches[0]['school_id'] === 'ARES-S0002', 'airbase variation should resolve to canonical school');
enrollment_expect(ares_search_schools($registry, 'r', 8) === [], 'one-character searches should be rejected');
enrollment_expect(ares_search_schools($registry, 'retired school', 8) === [], 'inactive schools should not be returned');

$secret = str_repeat('a', 64);
$codeOne = 'ABCD-EFGH';
$codeTwo = 'JKLM-NPQR';
$revokedCode = 'STUV-WXYZ';
enrollment_expect(ares_enrollment_code_hash($codeOne, $secret) === ares_enrollment_code_hash('abcd efgh', $secret), 'code normalization must be stable');

$tempDir = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'ares-enrollment-test-' . bin2hex(random_bytes(6));
enrollment_expect(mkdir($tempDir, 0700, true), 'temporary enrollment directory should be created');
$statePath = $tempDir . DIRECTORY_SEPARATOR . 'enrollment_state.json';
$state = [
    'version' => 1,
    'codes' => [
        ['school_id' => 'ARES-S0001', 'code_hash' => ares_enrollment_code_hash($codeOne, $secret), 'created_at' => gmdate('c'), 'used_at' => null, 'used_by_device_id' => null, 'revoked_at' => null],
        ['school_id' => 'ARES-S0002', 'code_hash' => ares_enrollment_code_hash($codeTwo, $secret), 'created_at' => gmdate('c'), 'used_at' => null, 'used_by_device_id' => null, 'revoked_at' => null],
        ['school_id' => 'ARES-S0001', 'code_hash' => ares_enrollment_code_hash($revokedCode, $secret), 'created_at' => gmdate('c'), 'used_at' => null, 'used_by_device_id' => null, 'revoked_at' => gmdate('c')],
    ],
    'devices' => [],
];
file_put_contents($statePath, json_encode($state, JSON_PRETTY_PRINT));

$mismatch = ares_issue_device_credential($statePath, $registry, 'ARES-S0001', $codeTwo, $secret, 'Test Phone');
enrollment_expect(($mismatch['error'] ?? '') === 'school-code-mismatch', 'code assigned to another school must fail');
$revoked = ares_issue_device_credential($statePath, $registry, 'ARES-S0001', $revokedCode, $secret, 'Test Phone');
enrollment_expect(($revoked['error'] ?? '') === 'invalid-enrollment-code', 'revoked code must fail');

$result = ares_issue_device_credential($statePath, $registry, 'ARES-S0001', $codeOne, $secret, 'Test Phone');
enrollment_expect(($result['ok'] ?? false) === true, 'valid school and code should enroll');
enrollment_expect(($result['status'] ?? '') === 'enrolled', 'successful result should report enrolled');
enrollment_expect(($result['school_id'] ?? '') === 'ARES-S0001', 'successful enrollment should bind the selected school');
enrollment_expect(($result['canonical_name'] ?? '') === 'Misuuni Sec', 'successful enrollment should return canonical school name');
enrollment_expect((bool)preg_match('/^ARES-D-[A-F0-9]{12}$/', (string)($result['device_id'] ?? '')), 'device ID should use expected format');
$credential = (string)($result['device_credential'] ?? '');
enrollment_expect((bool)preg_match('/^[a-f0-9]{64}$/', $credential), 'device credential should be a 256-bit hex token');

$stored = file_get_contents($statePath);
enrollment_expect(is_string($stored), 'enrollment state should be readable after write');
enrollment_expect(!str_contains($stored, $credential), 'raw device credential must never be stored server-side');
enrollment_expect(str_contains($stored, hash('sha256', $credential)), 'credential hash should be stored server-side');

$retry = ares_issue_device_credential($statePath, $registry, 'ARES-S0001', $codeOne, $secret, 'Test Phone');
enrollment_expect(($retry['error'] ?? '') === 'enrollment-code-used', 'one-time enrollment code must not be reusable');

unlink($statePath);
rmdir($tempDir);

echo "ARES enrollment tests passed\n";
