<?php
declare(strict_types=1);

function ares_extract_enrollment_admin_key(array $server): string
{
    if (!empty($server['HTTP_X_ARES_ADMIN_KEY'])) {
        return trim((string)$server['HTTP_X_ARES_ADMIN_KEY']);
    }

    if (!empty($server['HTTP_AUTHORIZATION'])) {
        $authorization = trim((string)$server['HTTP_AUTHORIZATION']);
        if (stripos($authorization, 'Bearer ') === 0) {
            return trim(substr($authorization, 7));
        }
    }

    return '';
}

function ares_generate_enrollment_code_for_school(
    string $statePath,
    array $registry,
    string $schoolId,
    string $secret,
    bool $rotate = false
): array {
    if (!ares_validate_school_registry($registry)) {
        return ['ok' => false, 'error' => 'invalid-school-registry'];
    }

    $school = ares_find_school($registry, $schoolId);
    if ($school === null) {
        return ['ok' => false, 'error' => 'unknown-school'];
    }

    if (strlen($secret) < 32 || str_starts_with($secret, 'REPLACE_')) {
        return ['ok' => false, 'error' => 'enrollment-secret-not-configured'];
    }

    $directory = dirname($statePath);
    if (!is_dir($directory) && !mkdir($directory, 0700, true) && !is_dir($directory)) {
        return ['ok' => false, 'error' => 'enrollment-storage-unavailable'];
    }

    $handle = fopen($statePath, 'c+');
    if ($handle === false || !flock($handle, LOCK_EX)) {
        if (is_resource($handle)) {
            fclose($handle);
        }
        return ['ok' => false, 'error' => 'enrollment-storage-unavailable'];
    }

    rewind($handle);
    $raw = stream_get_contents($handle);
    $state = ['version' => 1, 'codes' => [], 'devices' => []];
    if (is_string($raw) && trim($raw) !== '') {
        $decoded = json_decode($raw, true);
        if (!is_array($decoded)
            || !isset($decoded['codes'], $decoded['devices'])
            || !is_array($decoded['codes'])
            || !is_array($decoded['devices'])) {
            flock($handle, LOCK_UN);
            fclose($handle);
            return ['ok' => false, 'error' => 'invalid-enrollment-state'];
        }
        $state = $decoded;
    }

    $now = gmdate('c');
    $hasUnused = false;
    foreach ($state['codes'] as &$entry) {
        if (!is_array($entry) || (string)($entry['school_id'] ?? '') !== $schoolId) {
            continue;
        }

        $unused = empty($entry['used_at']) && empty($entry['revoked_at']);
        if (!$unused) {
            continue;
        }

        if ($rotate) {
            $entry['revoked_at'] = $now;
        } else {
            $hasUnused = true;
        }
    }
    unset($entry);

    if ($hasUnused) {
        flock($handle, LOCK_UN);
        fclose($handle);
        return ['ok' => false, 'error' => 'active-enrollment-code-exists'];
    }

    try {
        $code = ares_new_enrollment_code();
    } catch (Throwable $error) {
        flock($handle, LOCK_UN);
        fclose($handle);
        return ['ok' => false, 'error' => 'enrollment-code-generation-failed'];
    }

    $state['codes'][] = [
        'school_id' => $schoolId,
        'code_hash' => ares_enrollment_code_hash($code, $secret),
        'created_at' => $now,
        'used_at' => null,
        'used_by_device_id' => null,
        'revoked_at' => null,
    ];

    if (!ares_write_locked_json($handle, $state)) {
        flock($handle, LOCK_UN);
        fclose($handle);
        return ['ok' => false, 'error' => 'enrollment-storage-write-failed'];
    }

    flock($handle, LOCK_UN);
    fclose($handle);
    @chmod($statePath, 0600);

    return [
        'ok' => true,
        'status' => 'code-generated',
        'school_id' => $schoolId,
        'canonical_name' => (string)$school['canonical_name'],
        'enrollment_code' => $code,
    ];
}
