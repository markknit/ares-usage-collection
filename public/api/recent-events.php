<?php
header('Content-Type: application/json');$f=__DIR__.'/../../data/events.jsonl';$events=[];
if(is_file($f)){foreach(array_slice(file($f,FILE_IGNORE_NEW_LINES|FILE_SKIP_EMPTY_LINES),-100) as $l){$j=json_decode($l,true);if($j)$events[]=$j;}}
$events=array_reverse($events);echo json_encode(['events'=>$events],JSON_PRETTY_PRINT);
