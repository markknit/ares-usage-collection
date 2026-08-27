<?php
declare(strict_types=1);

require __DIR__ . '/upload_lib.php';

if ($_SERVER['REQUEST_METHOD'] === 'GET' || $_SERVER['REQUEST_METHOD'] === 'HEAD') {
    ares_json_response(200, [
        'service' => 'ares-monitor-upload',
        'status' => 'ready',
        'upload_method' => 'POST multipart/form-data',
        'file_field' => 'usage_file',
    ]);
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Allow: GET, HEAD, POST');
    ares_json_response(405, ['accepted' => false, 'error' => 'method-not-allowed']);
}

$configPath = __DIR__ . '/config.php';
if (!is_file($configPath)) {
    ares_json_response(503, ['accepted' => false, 'error' => 'service-not-configured']);
}

$config = require $configPath;
if (!is_array($config)) {
    ares_json_response(503, ['accepted' => false, 'error' => 'invalid-server-configuration']);
}

$requireHttps = array_key_exists('require_https', $config) ? (bool)$config['require_https'] : true;
if ($requireHttps && !ares_is_https($_SERVER)) {
    ares_json_response(400, ['accepted' => false, 'error' => 'https-required']);
}

$expectedKey = trim((string)($config['upload_key'] ?? ''));
if (strlen($expectedKey) < 32 || strpos($expectedKey, 'REPLACE_') === 0) {
    ares_json_response(503, ['accepted' => false, 'error' => 'upload-key-not-configured']);
}

$providedKey = ares_extract_upload_key($_SERVER);
if ($providedKey === '' || !hash_equals($expectedKey, $providedKey)) {
    header('WWW-Authenticate: Bearer realm="ARES monitor upload"');
    ares_json_response(401, ['accepted' => false, 'error' => 'unauthorized']);
}

if (!isset($_FILES['usage_file']) || !is_array($_FILES['usage_file'])) {
    ares_json_response(400, ['accepted' => false, 'error' => 'usage-file-required']);
}

$file = $_FILES['usage_file'];
$errorCode = (int)($file['error'] ?? UPLOAD_ERR_NO_FILE);
if ($errorCode !== UPLOAD_ERR_OK) {
    ares_json_response(400, [
        'accepted' => false,
        'error' => 'upload-failed',
        'upload_error_code' => $errorCode,
    ]);
}

$filename = (string)($file['name'] ?? '');
$metadata = ares_parse_usage_filename($filename);
if ($metadata === null) {
    ares_json_response(400, ['accepted' => false, 'error' => 'invalid-filename']);
}

$maxBytes = (int)($config['max_bytes'] ?? (2 * 1024 * 1024));
if ($maxBytes < 1024) {
    ares_json_response(503, ['accepted' => false, 'error' => 'invalid-size-configuration']);
}

$tmpPath = (string)($file['tmp_name'] ?? '');
if ($tmpPath === '' || !is_uploaded_file($tmpPath)) {
    ares_json_response(400, ['accepted' => false, 'error' => 'invalid-upload']);
}

if (!ares_plausible_csv($tmpPath, $maxBytes)) {
    ares_json_response(400, ['accepted' => false, 'error' => 'invalid-csv']);
}

$storageDir = (string)($config['storage_dir'] ?? (__DIR__ . '/incoming'));
if ($storageDir === '') {
    ares_json_response(503, ['accepted' => false, 'error' => 'storage-not-configured']);
}

if (!is_dir($storageDir) && !mkdir($storageDir, 0700, true) && !is_dir($storageDir)) {
    ares_json_response(503, ['accepted' => false, 'error' => 'storage-unavailable']);
}

if (!is_writable($storageDir)) {
    ares_json_response(503, ['accepted' => false, 'error' => 'storage-not-writable']);
}

$incomingSha256 = hash_file('sha256', $tmpPath);
if ($incomingSha256 === false) {
    ares_json_response(500, ['accepted' => false, 'error' => 'hash-failed']);
}

$targetPath = rtrim($storageDir, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR . $filename;
$targetState = ares_target_state($targetPath, $incomingSha256);

if ($targetState === 'duplicate') {
    ares_json_response(200, [
        'accepted' => true,
        'status' => 'duplicate',
        'filename' => $filename,
        'school' => $metadata['school'],
        'collection' => $metadata['collection'],
        'sha256' => $incomingSha256,
    ]);
}

if ($targetState === 'conflict') {
    ares_json_response(409, [
        'accepted' => false,
        'error' => 'filename-conflict',
        'filename' => $filename,
    ]);
}

try {
    $suffix = bin2hex(random_bytes(6));
} catch (Throwable $error) {
    ares_json_response(500, ['accepted' => false, 'error' => 'temporary-name-failed']);
}

$tempTarget = rtrim($storageDir, DIRECTORY_SEPARATOR)
    . DIRECTORY_SEPARATOR . '.' . $filename . '.' . $suffix . '.part';

if (!move_uploaded_file($tmpPath, $tempTarget)) {
    ares_json_response(500, ['accepted' => false, 'error' => 'store-failed']);
}

@chmod($tempTarget, 0600);

if (!rename($tempTarget, $targetPath)) {
    @unlink($tempTarget);

    $raceState = ares_target_state($targetPath, $incomingSha256);
    if ($raceState === 'duplicate') {
        ares_json_response(200, [
            'accepted' => true,
            'status' => 'duplicate',
            'filename' => $filename,
            'school' => $metadata['school'],
            'collection' => $metadata['collection'],
            'sha256' => $incomingSha256,
        ]);
    }

    ares_json_response(500, ['accepted' => false, 'error' => 'finalize-failed']);
}

@chmod($targetPath, 0600);

ares_json_response(201, [
    'accepted' => true,
    'status' => 'stored',
    'filename' => $filename,
    'school' => $metadata['school'],
    'collection' => $metadata['collection'],
    'sha256' => $incomingSha256,
    'bytes' => filesize($targetPath),
]);
