<?php
return [
    // Generate a private key, for example:
    // php -r "echo bin2hex(random_bytes(32)), PHP_EOL;"
    // Never commit the real key.
    'upload_key' => 'REPLACE_WITH_RANDOM_64_CHARACTER_SECRET',

    // Separate secret used to HMAC short enrollment codes before they are stored.
    // Generate this independently from upload_key.
    'enrollment_secret' => 'REPLACE_WITH_DIFFERENT_RANDOM_64_CHARACTER_SECRET',

    // For the pilot these protected directories can live beside index.php.
    // If the host allows it, absolute paths outside the public web root are even better.
    'storage_dir' => __DIR__ . '/incoming',
    'school_registry_path' => __DIR__ . '/data/schools.json',
    'enrollment_state_path' => __DIR__ . '/data/enrollment_state.json',

    // Current ARES usage files are small; 2 MiB leaves ample headroom.
    'max_bytes' => 2 * 1024 * 1024,

    // Production uploads and enrollment must use HTTPS.
    'require_https' => true,
];
