<?php
header('Content-Type: application/json');
$input=json_decode(file_get_contents('php://input'),true)?:[];
$school=preg_replace('/[^A-Z0-9_-]/','',strtoupper($input['school']??'UNKNOWN'));
$event=preg_replace('/[^a-z0-9_-]/','',strtolower($input['event']??'unknown'));
$ua=substr($input['user_agent']??($_SERVER['HTTP_USER_AGENT']??''),0,500);
$dir=realpath(__DIR__.'/../../data')?:__DIR__.'/../../data';if(!is_dir($dir))mkdir($dir,0770,true);
$line=json_encode(['created_at'=>gmdate('c'),'school'=>$school,'event'=>$event,'ip'=>$_SERVER['REMOTE_ADDR']??'','user_agent'=>$ua],JSON_UNESCAPED_SLASHES)."\n";
$ok=file_put_contents($dir.'/events.jsonl',$line,FILE_APPEND|LOCK_EX)!==false;echo json_encode(['ok'=>$ok]);
