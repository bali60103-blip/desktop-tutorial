
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

/* ============================== helpers ============================== */
function rectPts(x,y,w,h){ return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]; }
function bandPts(center,halfW){
  var left=center.map(function(p){return [p[0]-halfW,p[1]];});
  var right=center.map(function(p){return [p[0]+halfW,p[1]];}).reverse();
  return left.concat(right);
}
function vBandPts(center,halfW){ // for a mostly-vertical corridor: offset in X
  return bandPts(center,halfW);
}
function hBandPts(center,halfW){ // for a mostly-horizontal corridor: offset in Y(depth)
  var top=center.map(function(p){return [p[0],p[1]-halfW];});
  var bot=center.map(function(p){return [p[0],p[1]+halfW];}).reverse();
  return top.concat(bot);
}
function footprint(pts2D,height,color,opts){
  opts=opts||{};
  var shape=new THREE.Shape();
  // ExtrudeGeometry + rotateX(-90deg) maps the shape's local Y to world -Z;
  // negate Y here so callers can keep using the same (x, z-as-"y") convention
  // as pier()/cone()/labels/camera targets everywhere else in this file.
  pts2D.forEach(function(p,i){ i===0?shape.moveTo(p[0],-p[1]):shape.lineTo(p[0],-p[1]); });
  shape.closePath();
  var h=Math.max(height,0.08);
  var geo=new THREE.ExtrudeGeometry(shape,{depth:h,bevelEnabled:false});
  geo.rotateX(-Math.PI/2);
  if(opts.baseY) geo.translate(0,opts.baseY,0);
  var mat=new THREE.MeshLambertMaterial({color:color,side:THREE.DoubleSide,transparent:opts.opacity!==undefined,opacity:opts.opacity!==undefined?opts.opacity:1});
  var mesh=new THREE.Mesh(geo,mat);
  mesh.userData.edge=true;
  var edges=new THREE.LineSegments(new THREE.EdgesGeometry(geo,25),new THREE.LineBasicMaterial({color:0x000000,transparent:true,opacity:0.18}));
  mesh.add(edges);
  return mesh;
}
function pier(x,z,rTop,rBot,h,baseY,color){
  var geo=new THREE.CylinderGeometry(rTop,rBot,h,10);
  geo.translate(0,baseY+h/2,0);
  var mesh=new THREE.Mesh(geo,new THREE.MeshLambertMaterial({color:color}));
  mesh.position.set(x,0,z);
  return mesh;
}
function cone(x,z,r,h,baseY,color){
  var geo=new THREE.ConeGeometry(r,h,10);
  geo.translate(0,baseY+h/2,0);
  var mesh=new THREE.Mesh(geo,new THREE.MeshLambertMaterial({color:color}));
  mesh.position.set(x,0,z);
  return mesh;
}
function mulberry32(a){ return function(){ a|=0;a=a+0x6D2B79F5|0; var t=Math.imul(a^a>>>15,1|a); t=t+Math.imul(t^t>>>7,61|t)^t; return ((t^t>>>14)>>>0)/4294967296; }; }
function scatterLots(x0,y0,w,h,seed,target,minH,maxH){
  var rng=mulberry32(seed);
  var cols=Math.max(1,Math.round(w/target)), rows=Math.max(1,Math.round(h/target));
  var cw=w/cols, ch=h/rows, out=[];
  for(var r=0;r<rows;r++) for(var c=0;c<cols;c++){
    var pad=Math.min(cw,ch)*0.14;
    out.push({x:x0+c*cw+pad/2, y:y0+r*ch+pad/2, w:cw-pad, h:ch-pad, height:minH+rng()*(maxH-minH)});
  }
  return out;
}
function makeText(text,color){
  var cnv=document.createElement('canvas'); var pad=16, fs=44;
  var ctx=cnv.getContext('2d'); ctx.font='700 '+fs+'px "Noto Sans TC",sans-serif';
  var w=Math.ceil(ctx.measureText(text).width)+pad*2, h=fs+pad*1.6;
  cnv.width=w; cnv.height=h;
  ctx=cnv.getContext('2d'); ctx.font='700 '+fs+'px "Noto Sans TC",sans-serif';
  ctx.fillStyle='rgba(251,249,244,0.88)'; ctx.fillRect(0,0,w,h);
  ctx.fillStyle=color||'#231f19'; ctx.textBaseline='middle'; ctx.fillText(text,pad,h/2+2);
  var tex=new THREE.CanvasTexture(cnv);
  tex.colorSpace=THREE.SRGBColorSpace;
  var mat=new THREE.SpriteMaterial({map:tex,depthTest:false,transparent:true});
  var spr=new THREE.Sprite(mat);
  var scale=0.16;
  spr.scale.set(w*scale,h*scale,1);
  spr.renderOrder=999;
  return spr;
}

/* ============================== city data ============================== */
var GOLD='#cf9f3f', GOLD_L='#8a6a24', LOT='#e6dfcd', LOT_L='#c3b795',
    RIVER='#a9cde3', PARK='#bcd9a8', OLD='#c7b88e', NEW='#3f6f97', NEW_L='#22405a',
    HWY='#6c7280', HWY_L='#33384a', CAP='#4f8a44', RW='#4f8a44', CRASH='#c0392b';

var CITIES={};

// ---------- NIHONBASHI ----------
(function(){
  var RIVER_LEFT=[[475,-30],[462,140],[450,300],[448,430],[462,540],[472,560],[492,650],[520,760],[552,880],[590,980],[630,1090],[665,1200],[690,1330]];
  var RIVER_RIGHT=[[525,-30],[512,140],[500,300],[498,430],[512,540],[522,560],[542,650],[570,760],[602,880],[640,980],[680,1090],[715,1200],[740,1330]];
  var CENTER=RIVER_LEFT.map(function(p,i){return [(p[0]+RIVER_RIGHT[i][0])/2,p[1]];});
  var UG=[150,1100];
  CITIES.nihonbashi={
    label:'日本橋首都高地下化',
    w:900,d:1300,
    lots:[{x:20,y:-30,w:860,h:1360,seed:7,target:70,minH:8,maxH:16}],
    river:RIVER_LEFT.concat(RIVER_RIGHT.slice().reverse()),
    landmarks:[
      {x:338,y:436,w:128,h:96,height:34,name:'三井本館・三井タワー'},
      {x:274,y:606,w:154,h:112,height:24,name:'日本銀行本店'},
      {x:544,y:426,w:132,h:100,height:22,name:'三越日本橋本店'},
      {x:552,y:602,w:92,h:70,height:55,name:'COREDO日本橋'},
      {x:558,y:816,w:142,h:112,height:42,name:'日本橋高島屋S.C.'}
    ],
    redev:[
      {x:118,y:86,w:264,h:172,before:16,after:230,name:'常盤橋タワー（TOKYO TORCH）'},
      {x:96,y:296,w:204,h:112,before:14,after:70,name:'呉服橋プロジェクト'},
      {x:556,y:996,w:206,h:132,before:14,after:90,name:'河岸再開発街区'}
    ],
    highway:{center:CENTER,halfW:13,deckY:11,deckH:2,vertical:true},
    riverwalk:{leftPts:RIVER_LEFT,rightPts:RIVER_RIGHT,range:UG,offset:16},
    tunnelRange:UG,
    cam:{pos:[560,420,900],target:[450,0,620]},
    beforeCaption:'首都高速都心環状線高架橋（1963年通車）直接跨越日本橋川與日本橋上空。',
    afterCaption:'高架拆除、車流改走地下隧道，日本橋重見天空，沿岸整建為親水步道與再開發高樓。'
  };
})();

// ---------- CROSS-BRONX ----------
(function(){
  var BANK_W=[[605,-30],[612,120],[618,260],[608,380],[598,500],[600,640],[610,780],[618,850]];
  var BANK_E=[[655,-30],[662,120],[668,260],[658,380],[648,500],[650,640],[660,780],[668,850]];
  var HWY_CENTER=[[-30,430],[120,428],[260,425],[400,420],[500,415],[560,410],[630,405],[700,408],[800,415],[900,425],[1000,435],[1120,445],[1330,450]];
  CITIES.crossbronx={
    label:'Cross-Bronx Expressway 重新想像',
    w:1300,d:820,
    lots:[{x:20,y:10,w:1260,h:800,seed:11,target:75,minH:6,maxH:14}],
    river:BANK_W.concat(BANK_E.slice().reverse()),
    landmarks:[
      {x:870,y:520,w:190,h:150,height:12,name:'West Farms Bus Depot'},
      {x:790,y:560,w:70,h:60,height:16,name:'混凝土廠'}
    ],
    park:[
      {x:470,y:120,w:130,h:250,height:1,name:'Starlight Park（西岸）'},
      {x:670,y:120,w:140,h:250,height:1,name:'Starlight Park（東岸）'},
      {x:80,y:380,w:110,h:80,height:1,name:'Prospect Playground'}
    ],
    highway:{center:HWY_CENTER,halfW:22,deckY:11,deckH:2,vertical:false,trenchMaxX:560},
    cap:{x:[340,560],center:HWY_CENTER},
    cam:{pos:[650,480,1350],target:[650,0,410]},
    beforeCaption:'CBE以下凹式路堑（西段)／跨河高架（東段)切穿West Farms社區，Starlight Park被阻隔於Bronx River兩岸。',
    afterCaption:'願景概念（非定案）：路堑段加蓋覆土為公園。公路本身仍在原地運作，這是「加蓋」而非拆除或地下化。'
  };
})();

// ---------- WEST SIDE HIGHWAY ----------
(function(){
  var BANK=[[190,-30],[185,150],[192,300],[178,420],[170,520],[165,650],[172,800],[180,950],[188,1100],[195,1330]];
  var HWY_CENTER=[[228,-30],[226,150],[230,300],[222,420],[224,520],[227,650],[225,800],[229,950],[226,1100],[228,1330]];
  CITIES.westside={
    label:'West Side Highway',
    w:900,d:1300,
    lots:[{x:230,y:-30,w:640,h:1360,seed:17,target:70,minH:10,maxH:20}],
    river:[[0,-30]].concat(BANK).concat([[0,1330]]),
    landmarks:[{x:378,y:388,w:112,h:88,height:20,name:'Whitney Museum'}],
    piers:[
      {yr:[210,340],before:3,little:true,nameBefore:'Pier 54/55（舊,已拆）',nameAfter:'Little Island（2021）'},
      {yr:[580,700],before:2,little:false,nameBefore:'舊工業碼頭邊坡',nameAfter:'Gansevoort Peninsula（2023）'}
    ],
    crash:{y:[420,520]},
    highway:{center:HWY_CENTER,halfW:20,deckY:11,deckH:2,vertical:true},
    riverwalkBank:BANK,
    cam:{pos:[560,480,1000],target:[330,0,470]},
    beforeCaption:'Miller Highway（1929–1973）沿Hudson River東岸高架而建，阻隔市區與水岸。',
    afterCaption:'高架於1989年拆除，改建為Route 9A平面大道；水岸整建為Hudson River Park與新公園碼頭。'
  };
})();

/* ============================== scene setup ============================== */
var host=document.getElementById('canvasHost');
var renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
host.appendChild(renderer.domElement);

var scene=new THREE.Scene();
scene.background=new THREE.Color(0xdfe7ec);

var camera=new THREE.PerspectiveCamera(45,1,1,6000);
var controls=new OrbitControls(camera,renderer.domElement);
controls.enableDamping=true; controls.dampingFactor=0.08;
controls.maxPolarAngle=Math.PI*0.49;
controls.minDistance=60; controls.maxDistance=2200;

scene.add(new THREE.AmbientLight(0xffffff,0.65));
var sun=new THREE.DirectionalLight(0xfff3d8,0.9);
sun.position.set(600,900,400);
scene.add(sun);
var fill=new THREE.DirectionalLight(0xcfe0ff,0.35);
fill.position.set(-500,400,-600);
scene.add(fill);

function resize(){
  var w=host.clientWidth,h=host.clientHeight;
  renderer.setSize(w,h,false);
  camera.aspect=w/Math.max(h,1);
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(host);

var world=new THREE.Group(); scene.add(world);
var groupCommon, groupBefore, groupAfter, groupLots, groupLabels;

var uiState={city:'nihonbashi',state:'before',lots:true,labels:true};

function clearWorld(){
  while(world.children.length) world.remove(world.children[0]);
}

function buildCity(key){
  clearWorld();
  var d=CITIES[key];
  groupCommon=new THREE.Group(); groupBefore=new THREE.Group(); groupAfter=new THREE.Group();
  groupLots=new THREE.Group(); groupLabels=new THREE.Group();
  world.add(groupCommon,groupBefore,groupAfter,groupLots,groupLabels);

  // ground
  var groundShape=rectPts(0,0,d.w,d.d);
  groupCommon.add(footprint(groundShape,0.3,'#efe9da'));

  // generic lots
  (d.lots||[]).forEach(function(L){
    scatterLots(L.x,L.y,L.w,L.h,L.seed,L.target,L.minH,L.maxH).forEach(function(b){
      groupLots.add(footprint(rectPts(b.x,b.y,b.w,b.h),b.height,LOT,{}));
    });
  });

  // river
  if(d.river) groupCommon.add(footprint(d.river,0.6,RIVER,{baseY:0.35}));

  // park (Cross-Bronx)
  (d.park||[]).forEach(function(p){
    groupCommon.add(footprint(rectPts(p.x,p.y,p.w,p.h),1,PARK,{baseY:0.35}));
    var t=makeText(p.name,'#2f5327'); t.position.set(p.x+p.w/2,14,p.y+p.h/2); groupLabels.add(t);
  });
  if(key==='crossbronx'){
    groupCommon.add(footprint(rectPts(600,225,55,22),4,'#8a7757',{})); // pedestrian bridge
  }

  // landmarks (common, unaffected)
  (d.landmarks||[]).forEach(function(b){
    groupCommon.add(footprint(rectPts(b.x,b.y,b.w,b.h),b.height,GOLD,{}));
    var t=makeText(b.name); t.position.set(b.x+b.w/2,b.height+14,b.y+b.h/2); groupLabels.add(t);
  });

  // redev (Nihonbashi)
  (d.redev||[]).forEach(function(b){
    groupBefore.add(footprint(rectPts(b.x,b.y,b.w,b.h),b.before,OLD,{}));
    groupAfter.add(footprint(rectPts(b.x,b.y,b.w,b.h),b.after,NEW,{}));
    var tb=makeText('旧',  '#5b4c33'); tb.position.set(b.x+b.w/2,b.before+12,b.y+b.h/2); tb.userData.only='before'; groupLabels.add(tb);
    var ta=makeText(b.name,'#22405a'); ta.position.set(b.x+b.w/2,b.after+14,b.y+b.h/2); ta.userData.only='after'; groupLabels.add(ta);
  });

  // piers (West Side Highway)
  (d.piers||[]).forEach(function(p){
    var ymid=(p.yr[0]+p.yr[1])/2, bx=bankXAt(d,ymid)-70;
    groupBefore.add(footprint(rectPts(bx,p.yr[0],74,p.yr[1]-p.yr[0]),p.before,OLD,{}));
    var tb=makeText(p.nameBefore,'#5b4c33'); tb.position.set(bx+37,p.before+10,p.yr[0]-12); tb.userData.only='before'; groupLabels.add(tb);
    if(p.little){
      [0,1,2].forEach(function(i){
        groupAfter.add(pier(bx-25+i*22,ymid-40+i*38,26-i*3,26-i*3,8+ (2-i)*6,0,NEW));
      });
    } else {
      groupAfter.add(footprint(rectPts(bx-25,p.yr[0],99,p.yr[1]-p.yr[0]),3,NEW,{}));
    }
    var ta=makeText(p.nameAfter,'#22405a'); ta.position.set(bx+37,14,p.yr[1]+16); ta.userData.only='after'; groupLabels.add(ta);
  });

  // crash marker (West Side Highway, before only)
  if(d.crash){
    var cy=(d.crash.y[0]+d.crash.y[1])/2, cx=xAtY(d.highway.center,cy);
    var mk=new THREE.Mesh(new THREE.SphereGeometry(6,12,12),new THREE.MeshLambertMaterial({color:CRASH}));
    mk.position.set(cx,13,cy); groupBefore.add(mk);
    var t=makeText('1973/12/15 崩塌處','#8a2d1f'); t.position.set(cx+40,20,cy); t.userData.only='before'; groupLabels.add(t);
  }

  // highway
  buildHighway(d,key);

  // center the whole scene at the origin, then place the camera using the
  // same un-shifted coordinates the per-city data was authored in
  world.position.set(-d.w/2,0,-d.d/2);
  var c=d.cam, shift=new THREE.Vector3(d.w/2,0,d.d/2);
  camera.position.set(c.pos[0],c.pos[1],c.pos[2]).sub(shift);
  controls.target.set(c.target[0],c.target[1],c.target[2]).sub(shift);
  controls.update();

  updateLegend(key);
  updateFooter(key);
}

function xAtY(center,y){
  for(var i=0;i<center.length-1;i++){
    var a=center[i],b=center[i+1];
    if(y>=a[1]&&y<=b[1]){ var t=(y-a[1])/(b[1]-a[1]||1); return a[0]+(b[0]-a[0])*t; }
  }
  return center[0][0];
}
function bankXAt(d,y){ return xAtY(d.riverwalkBank||d.highway.center,y); }

function buildHighway(d,key){
  var hw=d.highway;
  if(key==='crossbronx'){
    // trench (west of trenchMaxX): flat strip + low walls, common to both states
    var trenchPts=hw.center.filter(function(p){return p[0]<=hw.trenchMaxX;});
    if(trenchPts.length>1){
      groupCommon.add(footprint(hBandPts(trenchPts,hw.halfW),0.6,HWY,{baseY:0.4}));
      groupCommon.add(footprint(hBandPts(trenchPts,hw.halfW+1),3,'#8f96a3',{opacity:0.35}));
    }
    // elevated (east of trenchMaxX): deck + columns, common to both states
    var elevPts=hw.center.filter(function(p){return p[0]>=hw.trenchMaxX-10;});
    if(elevPts.length>1){
      groupCommon.add(footprint(hBandPts(elevPts,hw.halfW),hw.deckH,HWY,{baseY:hw.deckY}));
      elevPts.forEach(function(p,i){ if(i%2===0) groupCommon.add(pier(p[0],p[1],2.2,2.2,hw.deckY,0,HWY_L)); });
    }
    // cap (after only): green deck over illustrative capped segment
    if(d.cap){
      var capPts=hw.center.filter(function(p){return p[0]>=d.cap.x[0]&&p[0]<=d.cap.x[1];});
      if(capPts.length>1){
        groupAfter.add(footprint(hBandPts(capPts,hw.halfW+2),1.2,CAP,{baseY:0.9}));
        var seed=mulberry32(21);
        for(var i=0;i<10;i++){
          var x=d.cap.x[0]+seed()*(d.cap.x[1]-d.cap.x[0]);
          groupAfter.add(cone(x,410+(seed()-0.5)*30,2.6,7,2,0x3d6a34));
        }
        var t=makeText('願景：加蓋覆土公園段（概念)','#2f5327'); t.position.set((d.cap.x[0]+d.cap.x[1])/2,16,470); t.userData.only='after'; groupLabels.add(t);
      }
    }
    return;
  }

  // Nihonbashi & West Side Highway: elevated ribbon (before only) along a mostly-vertical corridor
  var pts=vBandPts(hw.center,hw.halfW);
  groupBefore.add(footprint(pts,hw.deckH,HWY,{baseY:hw.deckY}));
  hw.center.forEach(function(p,i){ if(i%2===0 && p[1]>0 && p[1]<d.d) groupBefore.add(pier(p[0],p[1],1.8,1.8,hw.deckY,0,HWY_L)); });

  if(key==='nihonbashi' && d.tunnelRange){
    // after: recessed strip indicating the tunnel route + riverwalk
    var tp=hw.center.filter(function(p){return p[1]>=d.tunnelRange[0]&&p[1]<=d.tunnelRange[1];});
    groupAfter.add(footprint(vBandPts(tp,4),0.15,'#7a56c2',{baseY:0.4,opacity:0.55}));
    var rw=d.riverwalk;
    if(rw){
      var lp=rw.leftPts.filter(function(p){return p[1]>=rw.range[0]-40&&p[1]<=rw.range[1]+40;}).map(function(p){return [p[0]-rw.offset,p[1]];});
      var rp=rw.rightPts.filter(function(p){return p[1]>=rw.range[0]-40&&p[1]<=rw.range[1]+40;}).map(function(p){return [p[0]+rw.offset,p[1]];});
      groupAfter.add(footprint(vBandPts(lp,1.5),0.2,RW,{baseY:0.45}));
      groupAfter.add(footprint(vBandPts(rp,1.5),0.2,RW,{baseY:0.45}));
      var seed2=mulberry32(31);
      for(var i=0;i<18;i++){
        var yy=rw.range[0]+seed2()*(rw.range[1]-rw.range[0]);
        var side=seed2()<0.5?lp:rp;
        var xx=xAtY(side,yy);
        groupAfter.add(cone(xx,yy,2.4,7,2,0x3d6a34));
      }
    }
    var t=makeText('日本橋リバーウォーク（親水空間）','#2f5327'); t.position.set(hw.center[0][0]+40,16,d.tunnelRange[0]+20); t.userData.only='after'; groupLabels.add(t);
  }

  if(key==='westside'){
    var rwb=d.riverwalkBank;
    if(rwb){
      var pts2=rwb.map(function(p){return [p[0]-8,p[1]];});
      groupAfter.add(footprint(vBandPts(pts2,1.5),0.2,RW,{baseY:0.45}));
      var seed3=mulberry32(33);
      for(var i=0;i<20;i++){
        var yy2=-20+seed3()*(d.d+40);
        var xx2=xAtY(rwb,Math.max(0,Math.min(d.d,yy2)))+14+seed3()*30;
        groupAfter.add(cone(xx2,yy2,2.2,6,2,0x3d6a34));
      }
    }
  }
}

/* ============================== state / UI ============================== */
function applyVisibility(){
  groupBefore.visible=uiState.state==='before';
  groupAfter.visible=uiState.state==='after';
  groupLots.visible=uiState.lots;
  groupLabels.visible=uiState.labels;
  groupLabels.children.forEach(function(t){
    if(!t.userData.only) t.visible=true; else t.visible=(t.userData.only===uiState.state);
  });
}

function updateLegend(key){
  var html='';
  html+='<div class="row"><span class="swatch" style="background:'+LOT+'"></span>街廓量體（示意）</div>';
  html+='<div class="row"><span class="swatch" style="background:'+RIVER+'"></span>水岸</div>';
  html+='<div class="row"><span class="swatch" style="background:'+GOLD+'"></span>知名地標</div>';
  if(key==='nihonbashi'){
    html+='<div class="row"><span class="swatch" style="background:'+HWY+'"></span>首都高高架（Before）</div>';
    html+='<div class="row"><span class="swatch" style="background:'+OLD+'"></span>再開發－舊（Before）</div>';
    html+='<div class="row"><span class="swatch" style="background:'+NEW+'"></span>再開發－新（After）</div>';
  } else if(key==='crossbronx'){
    html+='<div class="row"><span class="swatch" style="background:'+HWY+'"></span>CBE 路堑／高架（共通）</div>';
    html+='<div class="row"><span class="swatch" style="background:'+CAP+'"></span>加蓋覆土段（After・願景）</div>';
    html+='<div class="row"><span class="swatch" style="background:'+PARK+'"></span>既有公園</div>';
  } else {
    html+='<div class="row"><span class="swatch" style="background:'+HWY+'"></span>Miller Highway（Before）</div>';
    html+='<div class="row"><span class="swatch" style="background:'+OLD+'"></span>碼頭－舊（Before）</div>';
    html+='<div class="row"><span class="swatch" style="background:'+NEW+'"></span>公園碼頭－新（After）</div>';
  }
  document.getElementById('legend').innerHTML=html;
}

var FOOTERS={
  nihonbashi:'資料來源：首都高速道路株式会社／東京都都市整備局／国土交通省（詳見 <a href="../nihonbashi-shutoko-undergrounding/" target="_blank" rel="noopener">2D對比頁</a>）。建物高度為示意量體，Tokiwabashi Tower取約390m等公開規劃高度，其餘為概略估計。',
  crossbronx:'資料來源：NYC DOT「Reimagine the Cross Bronx Expressway」（詳見 <a href="../cross-bronx-expressway-reimagined/" target="_blank" rel="noopener">2D對比頁</a>）。加蓋範圍與高度為示意，非官方定案。',
  westside:'資料來源：Wikipedia／Hudson River Park官方網站等（詳見 <a href="../west-side-highway-manhattan/" target="_blank" rel="noopener">2D對比頁</a>）。'
};
function updateFooter(key){
  document.getElementById('srcFooter').innerHTML=
    '本頁為示意3D量體，建物／公路尺寸依對應2D平面圖資料換算，非實測模型（本次作業環境無法連線 OpenStreetMap／GSI／Google Maps 等地圖資料源）。'+FOOTERS[key];
}

function updateCaption(){
  var d=CITIES[uiState.city];
  var cap=document.getElementById('stateCap');
  cap.innerHTML='<span class="tag">'+(uiState.state==='before'?'Before':'After')+'</span>'+(uiState.state==='before'?d.beforeCaption:d.afterCaption);
}

document.querySelectorAll('#citySeg button').forEach(function(btn){
  btn.addEventListener('click',function(){
    document.querySelectorAll('#citySeg button').forEach(function(b){b.classList.remove('active');});
    btn.classList.add('active');
    uiState.city=btn.dataset.city;
    buildCity(uiState.city);
    applyVisibility();
    updateCaption();
  });
});
document.querySelectorAll('#stateSeg button').forEach(function(btn){
  btn.addEventListener('click',function(){
    document.querySelectorAll('#stateSeg button').forEach(function(b){b.classList.remove('active');});
    btn.classList.add('active');
    uiState.state=btn.dataset.state;
    applyVisibility();
    updateCaption();
  });
});
document.getElementById('chkLots').addEventListener('change',function(e){ uiState.lots=e.target.checked; applyVisibility(); });
document.getElementById('chkLabels').addEventListener('change',function(e){ uiState.labels=e.target.checked; applyVisibility(); });
document.getElementById('resetBtn').addEventListener('click',function(){
  var d=CITIES[uiState.city];
  camera.position.set(d.cam.pos[0]-d.w/2,d.cam.pos[1],d.cam.pos[2]-d.d/2);
  controls.target.set(d.cam.target[0]-d.w/2,d.cam.target[1],d.cam.target[2]-d.d/2);
  controls.update();
});

function animate(){
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene,camera);
}

resize();
buildCity(uiState.city);
applyVisibility();
updateCaption();
document.getElementById('loading').hidden=true;
animate();
