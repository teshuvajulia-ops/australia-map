/* Builds a calendar (.ics) file for one CITYSIDE event. Used by the main site and by the event pages. */
(function(){
  var TZ = {melbourne:'Australia/Melbourne', sydney:'Australia/Sydney'};
  function today(tz){ return new Intl.DateTimeFormat('en-CA',{timeZone:tz,year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date()); }
  function add(iso,n){ var d=new Date(iso+'T12:00:00Z'); d.setUTCDate(d.getUTCDate()+n); return d.toISOString().slice(0,10); }
  function dow(iso){ return new Date(iso+'T12:00:00Z').getUTCDay(); }
  function days(e){ return Array.isArray(e.weekdays)&&e.weekdays.length ? e.weekdays : (typeof e.weekday==='number'?[e.weekday]:[]); }
  function esc(s){ return String(s||'').replace(/\\/g,'\\\\').replace(/;/g,'\;').replace(/,/g,'\\,').replace(/\r?\n/g,'\\n'); }
  function fold(l){ var o=[]; while(l.length>74){ o.push(l.slice(0,74)); l=' '+l.slice(74); } o.push(l); return o.join('\r\n'); }
  function nextDate(e,tz){
    var t0 = today(tz), d;
    if(e.repeat==='weekly' && days(e).length){
      d = t0; if(e.date && e.date>d) d=e.date;
      for(var i=0;i<8 && days(e).indexOf(dow(d))<0;i++) d=add(d,1);
      return d;
    }
    if(e.dates && e.dates.length){
      var f = e.dates.slice().sort().filter(function(x){return x>=t0;});
      return f[0] || null;
    }
    if(!e.date) return null;
    if(e.endDate && e.endDate>=t0 && e.date<t0) return t0;
    return e.date>=t0 ? e.date : null;
  }
  function hm(s){ var m=/(\d{1,2}):(\d{2})/.exec(s||''); return m?[+m[1],+m[2]]:null; }
  function p2(n){ return (n<10?'0':'')+n; }
  function compact(iso){ return iso.replace(/-/g,''); }
  function build(e, o){
    o = o||{}; var tz = TZ[e.city]||TZ.melbourne, d = nextDate(e,tz);
    if(!d) return null;
    var title = o.title||e.title_en||e.title, loc = e.address||'';
    var parts = String(e.time||'').split(/[–-]/), a = hm(parts[0]), b = hm(parts[1]);
    var L = ['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//CITYSIDE//cityside.app//EN','CALSCALE:GREGORIAN','BEGIN:VEVENT',
      'UID:'+e.id+'-'+compact(d)+'@cityside.app','DTSTAMP:'+new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d+/,'')];
    if(a){
      var sh=a[0], sm=a[1], eh, em, endDay = d;
      if(b){ eh=b[0]; em=b[1]; if(eh*60+em<=sh*60+sm) endDay=add(d,1); } else { var t=sh*60+sm+90; eh=Math.floor(t/60)%24; em=t%60; if(t>=1440) endDay=add(d,1); }
      L.push('DTSTART;TZID='+tz+':'+compact(d)+'T'+p2(sh)+p2(sm)+'00','DTEND;TZID='+tz+':'+compact(endDay)+'T'+p2(eh)+p2(em)+'00');
    } else {
      L.push('DTSTART;VALUE=DATE:'+compact(d),'DTEND;VALUE=DATE:'+compact(add(d,1)));
    }
    if(e.repeat==='weekly' && days(e).length){
      var N=['SU','MO','TU','WE','TH','FR','SA'], r='RRULE:FREQ=WEEKLY;BYDAY='+days(e).slice().sort().map(function(x){return N[x];}).join(',');
      if(e.endDate) r += ';UNTIL='+compact(e.endDate)+'T235959Z';
      L.push(r);
    }
    L.push(fold('SUMMARY:'+esc(title)), fold('LOCATION:'+esc(loc)));
    var desc = (o.desc||e.desc_en||e.desc||'') + (o.url ? '\n' + o.url : '');
    if(desc) L.push(fold('DESCRIPTION:'+esc(desc)));
    if(e.lat && e.lng) L.push('GEO:'+e.lat+';'+e.lng);
    if(o.url) L.push(fold('URL:'+o.url));
    L.push('END:VEVENT','END:VCALENDAR');
    return {text:L.join('\r\n')+'\r\n', name:(e.id||'event')+'.ics'};
  }
  function download(e,o){
    var r = build(e,o); if(!r) return false;
    var blob = new Blob([r.text],{type:'text/calendar;charset=utf-8'}), a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = r.name; document.body.appendChild(a); a.click();
    setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); },1500);
    return true;
  }
  window.CSIcs = {build:build, download:download, nextDate:nextDate};
})();
