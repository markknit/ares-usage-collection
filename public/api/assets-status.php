<?php
header('Content-Type: application/json');
$base=realpath(__DIR__.'/../assets/downloads');
$items=[
 ['label'=>'Approved Round Sync APK','file'=>'roundsync-approved.apk'],
 ['label'=>'Exported Round Sync configuration','file'=>'ARES-RoundSync-Config.zip'],
 ['label'=>'Misuuni MacroDroid automation','file'=>'ARES-MISUUNI-Automation.macro']
];
$out=[];foreach($items as $i){$p=$base.'/'.$i['file'];$out[]=['label'=>$i['label'],'path'=>'assets/downloads/'.$i['file'],'exists'=>is_file($p)&&filesize($p)>0,'bytes'=>is_file($p)?filesize($p):0];}
echo json_encode(['assets'=>$out],JSON_PRETTY_PRINT);
