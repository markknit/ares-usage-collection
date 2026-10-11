<?php
// Deploy under /tracker/. Adjust SCRIPT and ALLOWED_COLLECTIONS for the local server.
const SCRIPT='/usr/local/sbin/ares_prepare_usage_upload.sh';
$collection=preg_replace('/[^A-Z0-9_-]/','',strtoupper($_GET['collection']??'AUTO'));
$cmd='sudo '.escapeshellarg(SCRIPT).' '.escapeshellarg($collection).' 2>&1';
exec($cmd,$out,$status);if($status!==0){http_response_code(500);header('Content-Type:text/plain');echo "Unable to prepare report.\n".implode("\n",$out);exit;}
$meta=json_decode(end($out),true);if(!$meta||empty($meta['path'])||!is_file($meta['path'])){http_response_code(500);exit('Invalid report metadata');}
header('Content-Type:text/csv');header('Content-Length:'.filesize($meta['path']));header('Content-Disposition:attachment; filename="'.basename($meta['path']).'"');header('Cache-Control:no-store');readfile($meta['path']);
