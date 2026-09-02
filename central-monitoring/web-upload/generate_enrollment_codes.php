<?php
declare(strict_types=1);

require __DIR__ . '/enrollment_lib.php';

if (PHP_SAPI !== 'cli') {
    http_response_code(403);
    echo "CLI only\n";
    exit(1);
}

$configPath = __DIR__ . '/config.php';
if (!is_file($configPath)) {
    fwrite(STDERR, "config.php is missing\n");
    exit(1);
}

$config = require $configPath;
if (!is_array($config)) {
    fwrite(STDERR, "config.php is invalid\n");
    exit(1);
}

$registryPath = (string)($config['school_registry_path'] ?? (__DIR__ . '/data/schools.json'));
$statePath = (string)($config['enrollment_state_path'] ?? (__DIR__ . '/data/enrollment_state.json'));
$secret = trim((string)($config['enrollment_secret'] ?? ''));
if (strlen($secret) < 32 || str_starts_with($secret, 'REPLACE_')) {
    fwrite(STDERR, "enrollment_secret is not configured\n");
    exit(1);
}

$registry = ares_load_school_registry($registryPath);
if ($registry === null) {
    fwrite(STDERR, "school registry is missing or invalid\n");
    exit(1);
}

$all = in_array('--all', $argv, true);
$schoolId = '';
$rotate = in_array('--rotate', $argv, true);
foreach ($argv as $arg) {
    if (str_starts_with($arg, '--school=')) {
        $schoolId = substr($arg, strlen('--school='));
    }
}
if (!$all && $schoolId === '') {
    fwrite(STDERR, "Usage: php generate_enrollment_codes.php --all OR --school=ARES-S0001 [--rotate]\n");
    exit(1);
}

$targets = [];
foreach ($registry['schools'] as $school) {
    if (($school['active'] ?? true) !== true) {
        continue;
    }
    if ($all || (string)$school['school_id'] === $schoolId) {
        $targets[] = $school;
    }
}
if ($targets === []) {
    fwrite(STDERR, "No matching active school found\n");
    exit(1);
}

$directory = dirname($statePath);
if (!is_dir($directory) && !mkdir($directory, 0700, true) && !is_dir($directory)) {
    fwrite(STDERR, "Unable to create enrollment data directory\n");
    exit(1);
}

$handle = fopen($statePath, 'c+');
if ($handle === false || !flock($handle, LOCK_EX)) {
    fwrite(STDERR, "Unable to lock enrollment state\n");
    exit(1);
}
rewind($handle);
$raw = stream_get_contents($handle);
$state = ['version' => 1, 'codes' => [], 'devices' => []];
if (is_string($raw) && trim($raw) !== '') {
    $decoded = json_decode($raw, true);
    if (!is_array($decoded) || !isset($decoded['codes'], $decoded['devices'])
        || !is_array($decoded['codes']) || !is_array($decoded['devices'])) {
        flock($handle, LOCK_UN);
        fclose($handle);
        fwrite(STDERR, "Enrollment state is invalid\n");
        exit(1);
    }
    $state = $decoded;
}

$output = fopen('php://stdout', 'wb');
fputcsv($output, ['school_id', 'canonical_name', 'enrollment_code']);
foreach ($targets as $school) {
    $id = (string)$school['school_id'];
    $hasUnused = false;
    foreach ($state['codes'] as &$entry) {
        if (!is_array($entry) || (string)($entry['school_id'] ?? '') !== $id) {
            continue;
        }
        if (empty($entry['used_at']) && empty($entry['revoked_at'])) {
            if ($rotate) {
                $entry['revoked_at'] = gmdate('c');
            } else {
                $hasUnused = true;
            }
        }
    }
    unset($entry);

    if ($hasUnused) {
        continue;
    }

    $code = ares_new_enrollment_code();
    $state['codes'][] = [
        'school_id' => $id,
        'code_hash' => ares_enrollment_code_hash($code, $secret),
        'created_at' => gmdate('c'),
        'used_at' => null,
        'used_by_device_id' => null,
        'revoked_at' => null,
    ];
    fputcsv($output, [$id, (string)$school['canonical_name'], $code]);
}

if (!ares_write_locked_json($handle, $state)) {
    flock($handle, LOCK_UN);
    fclose($handle);
    fwrite(STDERR, "Unable to write enrollment state\n");
    exit(1);
}
flock($handle, LOCK_UN);
fclose($handle);
@chmod($statePath, 0600);
