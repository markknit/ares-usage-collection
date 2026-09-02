<?php
declare(strict_types=1);

require __DIR__ . '/upload_lib.php';
require __DIR__ . '/enrollment_lib.php';
require __DIR__ . '/enrollment_admin_lib.php';

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

$adminKey = trim((string)($config['enrollment_admin_key'] ?? ''));
if (strlen($adminKey) < 32 || str_starts_with($adminKey, 'REPLACE_')) {
    ares_json_response(503, ['ok' => false, 'error' => 'enrollment-admin-key-not-configured']);
}

$providedKey = ares_extract_enrollment_admin_key($_SERVER);
if ($providedKey === '' || !hash_equals($adminKey, $providedKey)) {
    header('WWW-Authenticate: Bearer realm="ARES enrollment admin"');
    ares_json_response(401, ['ok' => false, 'error' => 'unauthorized']);
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
if ($schoolId === '') {
    ares_json_response(400, ['ok' => false, 'error' => 'school-required']);
}
$rotate = isset($payload['rotate']) ? (bool)$payload['rotate'] : false;

$registryPath = (string)($config['school_registry_path'] ?? (__DIR__ . '/data/schools.json'));
$statePath = (string)($config['enrollment_state_path'] ?? (__DIR__ . '/data/enrollment_state.json'));
$secret = trim((string)($config['enrollment_secret'] ?? ''));

$registry = ares_load_school_registry($registryPath);
if ($registry === null) {
    ares_json_response(503, ['ok' => false, 'error' => 'school-registry-not-ready']);
}

$result = ares_generate_enrollment_code_for_school(
    $statePath,
    $registry,
    $schoolId,
    $secret,
    $rotate
);

if (($result['ok'] ?? false) === true) {
    ares_json_response(201, $result);
}

$error = (string)($result['error'] ?? 'enrollment-code-generation-failed');
$status = match ($error) {
    'unknown-school', 'active-enrollment-code-exists' => 400,
    'invalid-school-registry', 'enrollment-secret-not-configured', 'enrollment-storage-unavailable',
    'invalid-enrollment-state', 'enrollment-storage-write-failed' => 503,
    default => 500,
};

ares_json_response($status, $result);
