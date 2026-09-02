<?php
declare(strict_types=1);

require __DIR__ . '/upload_lib.php';
require __DIR__ . '/enrollment_lib.php';

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    header('Allow: GET');
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

$registryPath = (string)($config['school_registry_path'] ?? (__DIR__ . '/data/schools.json'));
$registry = ares_load_school_registry($registryPath);
if ($registry === null) {
    ares_json_response(503, ['ok' => false, 'error' => 'school-registry-not-ready']);
}

$query = trim((string)($_GET['q'] ?? ''));
if (strlen($query) < 2) {
    ares_json_response(400, ['ok' => false, 'error' => 'school-query-too-short']);
}

$matches = ares_search_schools($registry, $query, 8);
ares_json_response(200, [
    'ok' => true,
    'query' => $query,
    'matches' => $matches,
]);
