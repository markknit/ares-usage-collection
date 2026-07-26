<?php
$school=preg_replace('/[^A-Z0-9_-]/','',strtoupper($_GET['school']??'UNKNOWN'));
$stamp=gmdate('Y-m-d_H-i-s');$name="ARES_SETUP_TEST_{$school}_{$stamp}.txt";
header('Content-Type: text/plain');header('Content-Disposition: attachment; filename="'.$name.'"');header('Cache-Control: no-store');
echo "ARES setup test\nSchool: {$school}\nGenerated UTC: ".gmdate('c')."\nMove this file through the configured Round Sync task.\n";
