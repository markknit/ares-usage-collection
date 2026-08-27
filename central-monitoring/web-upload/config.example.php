<?php
return [
    // Generate a private key, for example:
    // php -r "echo bin2hex(random_bytes(32)), PHP_EOL;"
    // Never commit the real key.
    'upload_key' => 'REPLACE_WITH_RANDOM_64_CHARACTER_SECRET',

    // For the pilot this protected directory can live beside index.php.
    // If the host allows it, an absolute path outside the public web root is even better.
    'storage_dir' => __DIR__ . '/incoming',

    // Current ARES usage files are small; 2 MiB leaves ample headroom.
    'max_bytes' => 2 * 1024 * 1024,

    // Production uploads must use HTTPS.
    'require_https' => true,
];
