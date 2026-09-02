<?php
declare(strict_types=1);

require __DIR__ . '/upload_lib.php';
require __DIR__ . '/enrollment_lib.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Allow: POST');
    ares_json_response(405, ['ok' => false, 'error' => 'method-not-allowed']);
}

$configPath = __DIR__ . '/config.php';
if (!is_file($configPath)) {
    ares_json_response(503, ['ok' => false, 'error' => 'service-not-configured']);
}

$config = require $configPath;
if (!is_array($config)) {
    ares_json_response(503, ['ok' => false, 'error' => 'invalid-server-configuration']);
}

$requireHttps = array_key_exists('require_https', $config) ? (bool)$config['require_https'] : true;
if ($requireHttps && !ares_is_https($_SERVER)) {
    ares_json_response(400, ['ok' => false, 'error' => 'https-required']);
}

$contentType = strtolower((string)($_SERVER['CONTENT_TYPE'] ?? ''));
$payload = [];
if (str_contains($contentType, 'application/json')) {
    $raw = file_get_contents('php://input');
    $decoded = is_string($raw) ? json_decode($raw, true) : null;
    if (!is_array($decoded)) {
        ares_json_response(400, ['ok' => false, 'error' => 'invalid-json']);
    }
    $payload = $decoded;
} else {
    $payload = $_POST;
}

$schoolId = trim((string)($payload['school_id'] ?? ''));
$enrollmentCode = trim((string)($payload['enrollment_code'] ?? ''));
$deviceLabel = trim((string)($payload['device_label'] ?? ''));
if ($schoolId === '' || $enrollmentCode === '') {
    ares_json_response(400, ['ok' => false, 'error' => 'school-and-code-required']);
}

$registryPath = (string)($config['school_registry_path'] ?? (__DIR__ . '/data/schools.json'));
$statePath = (string)($config['enrollment_state_path'] ?? (__DIR__ . '/data/enrollment_state.json'));
$secret = trim((string)($config['enrollment_secret'] ?? ''));

$registry = ares_load_school_registry($registryPath);
if ($registry === null) {
    ares_json_response(503, ['ok' => false, 'error' => 'school-registry-not-ready']);
}
if (strlen($secret) < 32 || str_starts_with($secret, 'REPLACE_')) {
    ares_json_response(503, ['ok' => false, 'error' => 'enrollment-secret-not-configured']);
}

$result = ares_issue_device_credential(
    $statePath,
    $registry,
    $schoolId,
    $enrollmentCode,
    $secret,
    $deviceLabel
);

if (($result['ok'] ?? false) === true) {
    ares_json_response(201, $result);
}

$error = (string)($result['error'] ?? 'enrollment-failed');
$status = match ($error) {
    'unknown-school', 'invalid-enrollment-code', 'school-code-mismatch', 'enrollment-code-used' => 400,
    'invalid-school-registry', 'enrollment-secret-not-configured', 'enrollment-storage-unavailable',
    'invalid-enrollment-state', 'enrollment-storage-write-failed' => 503,
    default => 500,
};

ares_json_response($status, $result);
