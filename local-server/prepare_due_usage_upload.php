<?php
declare(strict_types=1);

// Deploy under /tracker/ beside collection_schedule.json.
// Production defaults can be overridden with environment variables for validation.
$script = getenv('ARES_UPLOAD_SCRIPT') ?: '/usr/local/sbin/ares_prepare_usage_upload.sh';
$scheduleFile = getenv('ARES_COLLECTION_SCHEDULE') ?: __DIR__ . '/collection_schedule.json';
$testDate = getenv('ARES_TEST_DATE') ?: null;
$sudo = getenv('ARES_SUDO');
if ($sudo === false) {
    $sudo = 'sudo';
}

function fail_response(int $status, string $message): never
{
    http_response_code($status);
    header('Content-Type: text/plain; charset=utf-8');
    header('Cache-Control: no-store');
    echo $message . "\n";
    exit;
}

if (!is_file($scheduleFile) || !is_readable($scheduleFile)) {
    fail_response(500, 'Collection schedule is unavailable.');
}

try {
    $schedule = json_decode((string) file_get_contents($scheduleFile), true, 512, JSON_THROW_ON_ERROR);
} catch (Throwable $e) {
    fail_response(500, 'Collection schedule is invalid.');
}

$timezoneName = $schedule['timezone'] ?? 'Africa/Nairobi';
try {
    $timezone = new DateTimeZone((string) $timezoneName);
    $today = $testDate
        ? new DateTimeImmutable($testDate, $timezone)
        : new DateTimeImmutable('today', $timezone);
} catch (Throwable $e) {
    fail_response(500, 'Collection schedule timezone or date is invalid.');
}

$collections = $schedule['collections'] ?? null;
if (!is_array($collections)) {
    fail_response(500, 'Collection schedule has no collections array.');
}

usort($collections, static function (array $a, array $b): int {
    return strcmp((string) ($a['due_date'] ?? ''), (string) ($b['due_date'] ?? ''));
});

$lastCompleted = strtoupper((string) ($_GET['last_completed'] ?? ''));
$lastCompleted = preg_replace('/[^A-Z0-9_-]/', '', $lastCompleted) ?? '';
$afterLastCompleted = ($lastCompleted === '');
$dueCollection = null;

foreach ($collections as $collection) {
    $id = strtoupper((string) ($collection['id'] ?? ''));
    $id = preg_replace('/[^A-Z0-9_-]/', '', $id) ?? '';
    $dueDateRaw = (string) ($collection['due_date'] ?? '');

    if ($id === '' || !preg_match('/^\d{4}-\d{2}-\d{2}$/', $dueDateRaw)) {
        fail_response(500, 'Collection schedule contains an invalid collection.');
    }

    if (!$afterLastCompleted) {
        if ($id === $lastCompleted) {
            $afterLastCompleted = true;
        }
        continue;
    }

    try {
        $dueDate = new DateTimeImmutable($dueDateRaw, $timezone);
    } catch (Throwable $e) {
        fail_response(500, 'Collection schedule contains an invalid due date.');
    }

    if ($dueDate <= $today) {
        $dueCollection = [
            'id' => $id,
            'due_date' => $dueDateRaw,
            'label' => (string) ($collection['label'] ?? $id),
        ];
        break;
    }
}

if ($lastCompleted !== '' && !$afterLastCompleted) {
    fail_response(400, 'last_completed is not present in the collection schedule.');
}

if ($dueCollection === null) {
    http_response_code(204);
    header('Cache-Control: no-store');
    header('X-ARES-Reason: no-due-collection');
    exit;
}

if (!is_file($script) || !is_executable($script)) {
    fail_response(500, 'Usage export script is unavailable.');
}

$command = ($sudo !== '' ? escapeshellcmd($sudo) . ' ' : '') . escapeshellarg($script) . ' ' . escapeshellarg($dueCollection['id']) . ' 2>&1';
exec($command, $output, $status);
if ($status !== 0) {
    fail_response(500, "Unable to prepare usage report.\n" . implode("\n", $output));
}

$metadata = json_decode((string) end($output), true);
if (!is_array($metadata) || empty($metadata['path']) || !is_file($metadata['path'])) {
    fail_response(500, 'Usage export returned invalid metadata.');
}

$path = (string) $metadata['path'];
$filename = basename($path);
header('Content-Type: text/csv');
header('Content-Length: ' . filesize($path));
header('Content-Disposition: attachment; filename="' . $filename . '"');
header('Cache-Control: no-store');
header('X-ARES-Collection: ' . $dueCollection['id']);
header('X-ARES-Due-Date: ' . $dueCollection['due_date']);
readfile($path);
