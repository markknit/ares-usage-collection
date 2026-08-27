<?php
declare(strict_types=1);

const ARES_USAGE_FILENAME_PATTERN = '/^ARES_USAGE_([A-Z0-9_-]+)_((?:20\d{2}-Q[1-4]-(?:MID|END))|AUTO)_(20\d{2}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.csv$/';

function ares_parse_usage_filename(string $name): ?array
{
    if ($name === '' || basename($name) !== $name) {
        return null;
    }

    if (!preg_match(ARES_USAGE_FILENAME_PATTERN, $name, $matches)) {
        return null;
    }

    return [
        'filename' => $name,
        'school' => $matches[1],
        'collection' => $matches[2],
        'timestamp' => $matches[3],
    ];
}

function ares_is_https(array $server): bool
{
    if (isset($server['HTTPS']) && $server['HTTPS'] !== '' && strtolower((string)$server['HTTPS']) !== 'off') {
        return true;
    }

    if (isset($server['HTTP_X_FORWARDED_PROTO'])) {
        $proto = strtolower(trim(explode(',', (string)$server['HTTP_X_FORWARDED_PROTO'])[0]));
        return $proto === 'https';
    }

    return false;
}

function ares_extract_upload_key(array $server): string
{
    if (!empty($server['HTTP_X_ARES_UPLOAD_KEY'])) {
        return trim((string)$server['HTTP_X_ARES_UPLOAD_KEY']);
    }

    if (!empty($server['HTTP_AUTHORIZATION'])) {
        $authorization = trim((string)$server['HTTP_AUTHORIZATION']);
        if (stripos($authorization, 'Bearer ') === 0) {
            return trim(substr($authorization, 7));
        }
    }

    return '';
}

function ares_plausible_csv(string $path, int $maxBytes): bool
{
    if (!is_file($path)) {
        return false;
    }

    $size = filesize($path);
    if ($size === false || $size < 10 || $size > $maxBytes) {
        return false;
    }

    $handle = fopen($path, 'rb');
    if ($handle === false) {
        return false;
    }

    $sample = fread($handle, min(4096, $size));
    fclose($handle);

    if ($sample === false || strpos($sample, "\0") !== false) {
        return false;
    }

    return strpos($sample, ',') !== false
        && (strpos($sample, "\n") !== false || strpos($sample, "\r") !== false);
}

function ares_target_state(string $targetPath, string $incomingSha256): string
{
    if (!file_exists($targetPath)) {
        return 'new';
    }

    if (!is_file($targetPath)) {
        return 'conflict';
    }

    $existingSha256 = hash_file('sha256', $targetPath);
    if ($existingSha256 !== false && hash_equals($existingSha256, $incomingSha256)) {
        return 'duplicate';
    }

    return 'conflict';
}

function ares_json_response(int $status, array $payload): void
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    header('X-Content-Type-Options: nosniff');
    echo json_encode($payload, JSON_UNESCAPED_SLASHES) . "\n";
    exit;
}
