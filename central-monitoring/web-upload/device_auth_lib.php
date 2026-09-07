<?php
declare(strict_types=1);

require_once __DIR__ . '/enrollment_lib.php';

function ares_extract_device_id(array $server): string
{
    return trim((string)($server['HTTP_X_ARES_DEVICE_ID'] ?? ''));
}

function ares_extract_device_credential(array $server): string
{
    return trim((string)($server['HTTP_X_ARES_DEVICE_CREDENTIAL'] ?? ''));
}

function ares_authenticate_device(string $statePath, string $deviceId, string $credential): array
{
    $deviceId = strtoupper(trim($deviceId));
    $credential = strtolower(trim($credential));

    if (!preg_match('/^ARES-D-[A-F0-9]{12}$/', $deviceId)
        || !preg_match('/^[a-f0-9]{64}$/', $credential)) {
        return ['ok' => false, 'error' => 'unauthorized'];
    }

    if ($statePath === '' || !is_file($statePath) || !is_readable($statePath)) {
        return ['ok' => false, 'error' => 'device-auth-not-ready'];
    }

    $handle = fopen($statePath, 'rb');
    if ($handle === false) {
        return ['ok' => false, 'error' => 'device-auth-not-ready'];
    }

    if (!flock($handle, LOCK_SH)) {
        fclose($handle);
        return ['ok' => false, 'error' => 'device-auth-not-ready'];
    }

    $raw = stream_get_contents($handle);
    flock($handle, LOCK_UN);
    fclose($handle);

    if ($raw === false || trim($raw) === '') {
        return ['ok' => false, 'error' => 'device-auth-not-ready'];
    }

    $state = json_decode($raw, true);
    if (!is_array($state) || !isset($state['devices']) || !is_array($state['devices'])) {
        return ['ok' => false, 'error' => 'device-auth-not-ready'];
    }

    $candidateHash = hash('sha256', $credential);
    foreach ($state['devices'] as $device) {
        if (!is_array($device)) {
            continue;
        }

        if (strtoupper((string)($device['device_id'] ?? '')) !== $deviceId) {
            continue;
        }

        if (!empty($device['revoked_at'])) {
            return ['ok' => false, 'error' => 'unauthorized'];
        }

        $storedHash = strtolower(trim((string)($device['credential_hash'] ?? '')));
        $schoolId = strtoupper(trim((string)($device['school_id'] ?? '')));
        if (!preg_match('/^[a-f0-9]{64}$/', $storedHash)
            || !preg_match('/^[A-Z0-9][A-Z0-9_-]{2,31}$/', $schoolId)
            || !hash_equals($storedHash, $candidateHash)) {
            return ['ok' => false, 'error' => 'unauthorized'];
        }

        return [
            'ok' => true,
            'device_id' => $deviceId,
            'school_id' => $schoolId,
        ];
    }

    return ['ok' => false, 'error' => 'unauthorized'];
}
