<?php
declare(strict_types=1);

function ares_load_json_array(string $path): ?array
{
    if ($path === '' || !is_file($path) || !is_readable($path)) {
        return null;
    }

    $raw = file_get_contents($path);
    if ($raw === false || trim($raw) === '') {
        return null;
    }

    $decoded = json_decode($raw, true);
    return is_array($decoded) ? $decoded : null;
}

function ares_validate_school_registry(array $registry): bool
{
    if (!isset($registry['schools']) || !is_array($registry['schools'])) {
        return false;
    }

    $seenIds = [];
    foreach ($registry['schools'] as $school) {
        if (!is_array($school)) {
            return false;
        }

        $schoolId = trim((string)($school['school_id'] ?? ''));
        $name = trim((string)($school['canonical_name'] ?? ''));
        $aliases = $school['aliases'] ?? [];
        $active = $school['active'] ?? true;

        if (!preg_match('/^[A-Z0-9][A-Z0-9_-]{2,31}$/', $schoolId)) {
            return false;
        }
        if ($name === '' || strlen($name) > 160) {
            return false;
        }
        if (!is_array($aliases) || !is_bool($active)) {
            return false;
        }
        foreach ($aliases as $alias) {
            if (!is_string($alias) || trim($alias) === '' || strlen($alias) > 160) {
                return false;
            }
        }
        if (isset($seenIds[$schoolId])) {
            return false;
        }
        $seenIds[$schoolId] = true;
    }

    return true;
}

function ares_load_school_registry(string $path): ?array
{
    $registry = ares_load_json_array($path);
    if ($registry === null || !ares_validate_school_registry($registry)) {
        return null;
    }
    return $registry;
}

function ares_normalize_school_text(string $value): string
{
    $value = strtolower(trim($value));
    $value = preg_replace('/[^a-z0-9]+/', ' ', $value) ?? '';
    $tokens = preg_split('/\s+/', trim($value)) ?: [];

    $mapped = [];
    foreach ($tokens as $token) {
        if ($token === '' || $token === 'school' || $token === 'sch') {
            continue;
        }
        if ($token === 'secondary' || $token === 'secs') {
            $token = 'sec';
        } elseif ($token === 'primary' || $token === 'pri') {
            $token = 'pry';
        } elseif ($token === 'saint') {
            $token = 'st';
        } elseif ($token === 'girl') {
            $token = 'girls';
        } elseif ($token === 'boy') {
            $token = 'boys';
        } elseif ($token === 'airbase') {
            $mapped[] = 'air';
            $token = 'base';
        }
        $mapped[] = $token;
    }

    return implode(' ', $mapped);
}

function ares_school_match_score(string $query, string $candidate): int
{
    $query = ares_normalize_school_text($query);
    $candidate = ares_normalize_school_text($candidate);
    if ($query === '' || $candidate === '') {
        return 0;
    }

    if ($query === $candidate) {
        return 10000;
    }

    $score = 0;
    if (str_starts_with($candidate, $query)) {
        $score = max($score, 9000 - abs(strlen($candidate) - strlen($query)));
    }
    if (str_contains($candidate, $query)) {
        $score = max($score, 8200 - abs(strlen($candidate) - strlen($query)));
    }

    $queryTokens = array_values(array_filter(explode(' ', $query)));
    $candidateTokens = array_values(array_filter(explode(' ', $candidate)));
    if ($queryTokens !== []) {
        $matched = 0;
        foreach ($queryTokens as $token) {
            foreach ($candidateTokens as $candidateToken) {
                if ($token === $candidateToken || str_starts_with($candidateToken, $token)) {
                    $matched++;
                    break;
                }
            }
        }
        $coverage = $matched / count($queryTokens);
        if ($coverage > 0) {
            $score = max($score, (int)round(6000 + (3000 * $coverage)));
        }
    }

    $distance = levenshtein($query, $candidate);
    $maxLen = max(strlen($query), strlen($candidate));
    if ($maxLen > 0) {
        $similarity = 1.0 - min(1.0, $distance / $maxLen);
        $score = max($score, (int)round(5000 * $similarity));
    }

    return $score;
}

function ares_search_schools(array $registry, string $query, int $limit = 8): array
{
    if (!ares_validate_school_registry($registry)) {
        return [];
    }

    $query = trim($query);
    if (strlen($query) < 2) {
        return [];
    }

    $matches = [];
    foreach ($registry['schools'] as $school) {
        if (($school['active'] ?? true) !== true) {
            continue;
        }

        $score = ares_school_match_score($query, (string)$school['canonical_name']);
        foreach (($school['aliases'] ?? []) as $alias) {
            $score = max($score, ares_school_match_score($query, (string)$alias));
        }
        if ($score < 5500) {
            continue;
        }

        $matches[] = [
            'school_id' => (string)$school['school_id'],
            'canonical_name' => (string)$school['canonical_name'],
            'score' => $score,
        ];
    }

    usort($matches, static function (array $left, array $right): int {
        $byScore = $right['score'] <=> $left['score'];
        if ($byScore !== 0) {
            return $byScore;
        }
        return strcasecmp((string)$left['canonical_name'], (string)$right['canonical_name']);
    });

    $limit = max(1, min(20, $limit));
    $matches = array_slice($matches, 0, $limit);
    foreach ($matches as &$match) {
        unset($match['score']);
    }
    unset($match);

    return $matches;
}

function ares_find_school(array $registry, string $schoolId): ?array
{
    foreach (($registry['schools'] ?? []) as $school) {
        if (is_array($school)
            && ($school['active'] ?? true) === true
            && (string)($school['school_id'] ?? '') === $schoolId) {
            return $school;
        }
    }
    return null;
}

function ares_normalize_enrollment_code(string $code): string
{
    return preg_replace('/[^A-Z0-9]/', '', strtoupper(trim($code))) ?? '';
}

function ares_enrollment_code_hash(string $code, string $secret): string
{
    return hash_hmac('sha256', ares_normalize_enrollment_code($code), $secret);
}

function ares_new_enrollment_code(): string
{
    $alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    $raw = '';
    for ($index = 0; $index < 8; $index++) {
        $raw .= $alphabet[random_int(0, strlen($alphabet) - 1)];
    }
    return substr($raw, 0, 4) . '-' . substr($raw, 4, 4);
}

function ares_write_locked_json($handle, array $data): bool
{
    $encoded = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    if ($encoded === false) {
        return false;
    }

    rewind($handle);
    if (!ftruncate($handle, 0)) {
        return false;
    }
    if (fwrite($handle, $encoded . "\n") === false) {
        return false;
    }
    return fflush($handle);
}

function ares_issue_device_credential(
    string $statePath,
    array $registry,
    string $schoolId,
    string $enrollmentCode,
    string $secret,
    string $deviceLabel = ''
): array {
    if (!ares_validate_school_registry($registry)) {
        return ['ok' => false, 'error' => 'invalid-school-registry'];
    }
    if (ares_find_school($registry, $schoolId) === null) {
        return ['ok' => false, 'error' => 'unknown-school'];
    }
    if (strlen($secret) < 32 || str_starts_with($secret, 'REPLACE_')) {
        return ['ok' => false, 'error' => 'enrollment-secret-not-configured'];
    }

    $normalizedCode = ares_normalize_enrollment_code($enrollmentCode);
    if (strlen($normalizedCode) < 6 || strlen($normalizedCode) > 16) {
        return ['ok' => false, 'error' => 'invalid-enrollment-code'];
    }

    $directory = dirname($statePath);
    if (!is_dir($directory) && !mkdir($directory, 0700, true) && !is_dir($directory)) {
        return ['ok' => false, 'error' => 'enrollment-storage-unavailable'];
    }

    $handle = fopen($statePath, 'c+');
    if ($handle === false) {
        return ['ok' => false, 'error' => 'enrollment-storage-unavailable'];
    }
    if (!flock($handle, LOCK_EX)) {
        fclose($handle);
        return ['ok' => false, 'error' => 'enrollment-storage-unavailable'];
    }

    rewind($handle);
    $raw = stream_get_contents($handle);
    $state = null;
    if ($raw !== false && trim($raw) !== '') {
        $decoded = json_decode($raw, true);
        if (is_array($decoded)) {
            $state = $decoded;
        }
    }
    if ($state === null) {
        $state = ['version' => 1, 'codes' => [], 'devices' => []];
    }
    if (!isset($state['codes']) || !is_array($state['codes'])
        || !isset($state['devices']) || !is_array($state['devices'])) {
        flock($handle, LOCK_UN);
        fclose($handle);
        return ['ok' => false, 'error' => 'invalid-enrollment-state'];
    }

    $candidateHash = ares_enrollment_code_hash($normalizedCode, $secret);
    $matchedIndex = null;
    $matchedSchool = null;
    $matchedUsed = false;
    $matchedRevoked = false;

    foreach ($state['codes'] as $index => $entry) {
        if (!is_array($entry)) {
            continue;
        }
        $storedHash = (string)($entry['code_hash'] ?? '');
        if ($storedHash !== '' && hash_equals($storedHash, $candidateHash)) {
            $matchedIndex = $index;
            $matchedSchool = (string)($entry['school_id'] ?? '');
            $matchedUsed = !empty($entry['used_at']);
            $matchedRevoked = !empty($entry['revoked_at']);
            break;
        }
    }

    if ($matchedIndex === null) {
        flock($handle, LOCK_UN);
        fclose($handle);
        return ['ok' => false, 'error' => 'invalid-enrollment-code'];
    }
    if ($matchedRevoked) {
        flock($handle, LOCK_UN);
        fclose($handle);
        return ['ok' => false, 'error' => 'invalid-enrollment-code'];
    }
    if ($matchedSchool !== $schoolId) {
        flock($handle, LOCK_UN);
        fclose($handle);
        return ['ok' => false, 'error' => 'school-code-mismatch'];
    }
    if ($matchedUsed) {
        flock($handle, LOCK_UN);
        fclose($handle);
        return ['ok' => false, 'error' => 'enrollment-code-used'];
    }

    try {
        $deviceId = 'ARES-D-' . strtoupper(bin2hex(random_bytes(6)));
        $credential = bin2hex(random_bytes(32));
    } catch (Throwable $error) {
        flock($handle, LOCK_UN);
        fclose($handle);
        return ['ok' => false, 'error' => 'credential-generation-failed'];
    }

    $now = gmdate('c');
    $deviceLabel = trim($deviceLabel);
    if (strlen($deviceLabel) > 80) {
        $deviceLabel = substr($deviceLabel, 0, 80);
    }

    $state['codes'][$matchedIndex]['used_at'] = $now;
    $state['codes'][$matchedIndex]['used_by_device_id'] = $deviceId;
    $state['devices'][] = [
        'device_id' => $deviceId,
        'school_id' => $schoolId,
        'credential_hash' => hash('sha256', $credential),
        'created_at' => $now,
        'label' => $deviceLabel,
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

    $school = ares_find_school($registry, $schoolId);
    return [
        'ok' => true,
        'status' => 'enrolled',
        'school_id' => $schoolId,
        'canonical_name' => (string)($school['canonical_name'] ?? ''),
        'device_id' => $deviceId,
        'device_credential' => $credential,
    ];
}
