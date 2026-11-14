#!/usr/bin/env python3
"""Builds one static page per event (e/<id>/index.html), plus sitemap.xml and robots.txt.
Run after editing events.json:  python3 build_event_pages.py"""
import json, html, os, shutil, datetime
SITE = 'https://cityside.app'
ev = json.load(open('events.json', encoding='utf-8'))
groups = json.load(open('groups.json', encoding='utf-8'))
cfg = json.load(open('config.json', encoding='utf-8'))
CITY = {'melbourne': 'Melbourne', 'sydney': 'Sydney'}
CATS = {'running':'Run clubs','surf':'Surfing','volleyball':'Volleyball','music':'Music','food':'Food','markets':'Markets','parties':'Parties','culture':'Culture','family':'Family','outdoors':'Outdoors','sports':'Sports','community':'Community'}
DAYS = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
E = lambda s: html.escape(str(s or ''), quote=True)

def days(e):
    if e.get('weekdays'): return e['weekdays']
    return [e['weekday']] if isinstance(e.get('weekday'), int) else []

def nice(d):
    return datetime.date.fromisoformat(d).strftime('%a %-d %b %Y')

def when(e):
    out = []
    if e.get('repeat') == 'weekly' and days(e):
        names = [DAYS[x] for x in sorted(days(e))]
        out.append('Every ' + (', '.join(names[:-1]) + ' and ' + names[-1] if len(names) > 1 else names[0]))
    elif e.get('date'):
        out.append(nice(e['date']) + (' – ' + nice(e['endDate']) if e.get('endDate') and e['endDate'] != e['date'] else ''))
    if e.get('time'): out.append(e['time'])
    return ' · '.join(out)

def iso_start(e):
    if e.get('repeat') == 'weekly' or not e.get('date'): return None
    t = (e.get('time') or '').split('–')[0].strip()
    return e['date'] + ('T' + t + ':00' if t else '')

TEMPLATE = open('event_template.html', encoding='utf-8').read()
CITY_TPL = open('city_template.html', encoding='utf-8').read()
TODAY = datetime.date.today().isoformat()

def last_day(e):
    if e.get('repeat') == 'weekly': return None
    ds = list(e.get('dates') or [])
    for k in ('endDate', 'date'):
        if e.get(k): ds.append(e[k])
    return max(ds) if ds else None

def expired(e):
    ld_ = last_day(e)
    return bool(ld_ and ld_ < TODAY)

def first_day(e):
    ds = list(e.get('dates') or []) or ([e['date']] if e.get('date') else [])
    return min([d for d in ds if d >= TODAY] or ds or ['9999'])

shutil.rmtree('e', ignore_errors=True)
urls = [SITE + '/']
for e in ev:
    title = e.get('title_en') or e.get('title')
    desc = e.get('desc_en') or e.get('desc') or ''
    city = CITY.get(e['city'], e['city'])
    page = SITE + '/e/' + e['id'] + '/'
    if not expired(e): urls.append(page)
    wa = e.get('whatsapp') or groups.get(e['city'], '')
    facts = ''.join('<div><b>%s</b>%s</div>' % (lbl, E(e.get(k + '_en') or e.get(k)))
                    for lbl, k in (('Price', 'price'), ('Level', 'level'), ('Bring', 'bring')) if e.get(k + '_en') or e.get(k))
    cats = ' · '.join(CATS.get(c, c) for c in e.get('cats', []))
    img = e.get('image') or ''
    img_abs = (img if img.startswith('http') else SITE + '/' + img) if img else SITE + '/icon-512.png'
    ld = {'@context': 'https://schema.org', '@type': 'Event', 'name': title, 'description': desc,
          'eventAttendanceMode': 'https://schema.org/OfflineEventAttendanceMode',
          'location': {'@type': 'Place', 'name': e.get('address', ''), 'address': e.get('address', '')},
          'image': [img_abs], 'url': page}
    st = iso_start(e)
    if st: ld['startDate'] = st
    if e.get('endDate') and not e.get('repeat'): ld['endDate'] = e['endDate']
    ld['isAccessibleForFree'] = 'free' in ((e.get('price_en') or '') + desc).lower()
    mapq = 'https://www.google.com/maps/search/?api=1&query=%s,%s' % (e.get('lat'), e.get('lng'))
    ctx = {
        'TITLE': E(title), 'DESC': E(desc), 'DESC_SHORT': E(desc[:180]), 'CITY': city, 'PAGE': page,
        'EMOJI': E(e.get('emoji') or '📍'), 'WHEN': E(when(e) or 'Dates to be confirmed'), 'ADDRESS': E(e.get('address')),
        'CATS': E(cats), 'FACTS': facts, 'IMG_TAG': ('<img class="hero" alt="" src="/%s">' % E(img) if img and not img.startswith('http') else ('<img class="hero" alt="" src="%s">' % E(img) if img else '')),
        'OG_IMG': E(img_abs), 'MAP': E(mapq), 'APPLINK': SITE + '/?e=' + e['id'],
        'WA_BTN': ('<a class="btn wa" href="%s" target="_blank" rel="noopener">👥 Join the %s WhatsApp group</a>' % (E(wa), city)) if wa else '',
        'MORE_BTN': ('<a class="btn ghost" href="%s" target="_blank" rel="noopener">Official details ↗</a>' % E(e['url'])) if str(e.get('url', '')).startswith('http') else '',
        'LD': json.dumps(ld, ensure_ascii=False).replace('</', '<\\/'),
        'EVJSON': json.dumps({k: e.get(k) for k in ('id', 'city', 'title', 'title_en', 'desc', 'desc_en', 'date', 'endDate', 'dates', 'time', 'address', 'lat', 'lng', 'repeat', 'weekday', 'weekdays')}, ensure_ascii=False).replace('</', '<\\/'),
        'ROBOTS': '<meta name="robots" content="noindex">' if expired(e) else '',
        'SHARE': E('https://wa.me/?text=' + __import__('urllib.parse').parse.quote('🙋 Come with me!\n*%s*\n📅 %s\n📍 %s\n\n%s' % (title, when(e), e.get('address', ''), page))),
    }
    out = TEMPLATE
    for k, v in ctx.items(): out = out.replace('{{%s}}' % k, str(v))
    os.makedirs('e/' + e['id'], exist_ok=True)
    open('e/%s/index.html' % e['id'], 'w', encoding='utf-8').write(out)

today = TODAY
INTRO = {
 'melbourne': "Looking for things to do in Melbourne this week? CITYSIDE gathers the city's festivals, markets, parties and weekly run clubs on one map, and marks the newcomer-friendly ones so you can turn up on your own and meet people.",
 'sydney': "Looking for things to do in Sydney this week? CITYSIDE gathers the city's festivals, markets, parties and sunrise run clubs on one map, and marks the newcomer-friendly ones so you can turn up on your own and meet people.",
}
for slug, name in CITY.items():
    other = 'sydney' if slug == 'melbourne' else 'melbourne'
    mine = [e for e in ev if e['city'] == slug]
    up = sorted([e for e in mine if e.get('repeat') != 'weekly' and not expired(e)], key=first_day)
    wk = [e for e in mine if e.get('repeat') == 'weekly']
    item = lambda e: '<li><a href="/e/%s/"><span class="em">%s</span><div><b>%s</b><span>%s%s</span></div></a></li>' % (
        e['id'], E(e.get('emoji') or '📍'), E(e.get('title_en') or e.get('title')), E(when(e)),
        (' · ' + E(e.get('address', '').split(',')[0])) if e.get('address') else '')
    page = SITE + '/' + slug + '/'
    desc = "What's on in %s: festivals, markets, parties and weekly run clubs, plus a friendly WhatsApp group to meet people. Updated weekly." % name
    wa = groups.get(slug, '')
    ldc = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'Events & run clubs in ' + name, 'url': page, 'description': desc,
           'mainEntity': {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': SITE + '/e/' + e['id'] + '/', 'name': e.get('title_en') or e.get('title')} for i, e in enumerate(up + wk)]}}
    out = CITY_TPL
    for k, v in {'CITYNAME': name, 'SLUG': slug, 'DESC': E(desc), 'PAGE': page, 'INTRO': E(INTRO[slug]),
                 'UPCOMING': ''.join(item(e) for e in up) or '<li><a href="/"><div><b>Check the map for new events</b></div></a></li>',
                 'WEEKLY': ''.join(item(e) for e in wk),
                 'WA_BTN': ('<a class="btn wa" href="%s" target="_blank" rel="noopener">👥 Join the %s WhatsApp group</a>' % (E(wa), name)) if wa else '',
                 'OTHERPAGE': '/' + other + '/', 'OTHERNAME': CITY[other],
                 'LD': json.dumps(ldc, ensure_ascii=False).replace('</', '<\\/')}.items():
        out = out.replace('{{%s}}' % k, str(v))
    os.makedirs(slug, exist_ok=True)
    open(slug + '/index.html', 'w', encoding='utf-8').write(out)
    urls.insert(1, page)
open('sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    ''.join('<url><loc>%s</loc><lastmod>%s</lastmod></url>\n' % (u, today) for u in urls) + '</urlset>\n')
open('robots.txt', 'w').write('User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n' % SITE)
print(len(ev), 'event pages built')
