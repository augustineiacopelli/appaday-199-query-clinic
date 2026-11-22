# End to end check of Query Clinic (AppADay 199) in Chromium at 375px, with the iPhone user agent.
# Serve the parent folder that holds this repo and the appaday portal clone side by side:
#   cd .. && python3 -m http.server 8199   then   python3 appaday-199-query-clinic/test/e2e_query_clinic.py
# Only same origin requests are served; fonts and save.js are blocked, so the test runs offline.
import os
from playwright.sync_api import sync_playwright

PORT = os.environ.get('QC_PORT', '8199')
BASE = 'http://127.0.0.1:' + PORT + '/'
URL = BASE + 'appaday-199-query-clinic/'
SHOT = os.environ.get('QC_SHOTS', '/tmp/shots199/')
os.makedirs(SHOT, exist_ok=True)
UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'
results = []

def ok(name, cond, extra=''):
    results.append((name, bool(cond))); print(('PASS ' if cond else 'FAIL ') + name + ('  ' + str(extra) if extra else ''))

def route_all(route):
    return route.continue_() if route.request.url.startswith(BASE) else route.abort()

def q(page, name):
    return page.locator('#clinic [data-qc="' + name + '"]')

def booted(page):
    page.wait_for_function("window.QueryClinic && QueryClinic.app && QueryClinic.app.state.p && QueryClinic.app.state.integrity", timeout=30000)

def sideways(page):
    return page.evaluate("document.documentElement.scrollWidth <= window.innerWidth && document.body.scrollWidth <= window.innerWidth")

def rec(page, ex):
    return page.evaluate("id => QDClinic.progress(QueryClinic.app.project()).byId[id] || null", ex)

def solve(page, ex, sql):
    q(page, 'editor').fill(sql); q(page, 'btnCheck').click()

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 375, 'height': 812}, user_agent=UA, device_scale_factor=2, is_mobile=True, has_touch=True, accept_downloads=True)
    ctx.route('**/*', route_all)
    page = ctx.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append('pageerror ' + str(e)))
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' and 'net::ERR_FAILED' not in m.text and 'Failed to load resource' not in m.text else None)

    page.goto(URL); booted(page)
    ok('boots with the stored project named Query Clinic', page.evaluate("QueryClinic.app.project().name") == 'Query Clinic')
    ok('practice data passes the pinned sha256 check', page.evaluate("QueryClinic.app.state.integrity.ok && QueryClinic.app.state.integrity.method === 'sha256'"))
    ok('ten units listed', page.locator('#clinic .unit').count() == 10)
    ok('tab title', page.title() == 'Query Clinic | AppADay 199')
    ok('no sideways scroll on the unit list', sideways(page))
    page.screenshot(path=SHOT + '01-units.png', full_page=True)

    # every element the component uses lives under its root
    ok('every data-qc element is inside the mount root', page.evaluate(
        "Array.from(document.querySelectorAll('[data-qc]')).every(el => document.getElementById('clinic').contains(el))"))

    # all ten units reachable on a phone
    reach = True
    for u in range(1, 11):
        page.locator('#clinic [data-qc-unit="%d"]' % u).click()
        first = page.locator('#clinic .unit[data-unit="%d"] [data-qc-ex]' % u).first
        exid = first.get_attribute('data-qc-ex')
        first.click()
        reach = reach and q(page, 'viewEx').is_visible() and exid in q(page, 'exTitle').inner_text()
        q(page, 'btnBack').click()
    ok('all ten units open an exercise and come back', reach)

    # 1.1: run is ungraded, check fails with a reason and the expected shape
    page.locator('#clinic [data-qc-unit="1"]').click()
    page.locator('#clinic [data-qc-ex="1.1"]').click()
    q(page, 'editor').fill('SELECT name FROM campuses')
    q(page, 'btnRun').click()
    ok('Run shows rows', q(page, 'result').is_visible() and '4 rows' in q(page, 'result').inner_text())
    ok('Run does not grade', rec(page, '1.1') is None)
    q(page, 'btnCheck').click()
    v = q(page, 'verdict').inner_text()
    ok('failed check gives a reason and the expected shape', 'Not yet' in v and 'Expected 4 columns' in v and '4 columns and 4 rows' in v, v.replace('\n', ' | '))
    ok('one try recorded', rec(page, '1.1')['attempts'] == 1)
    ok('Show answer locked before three tries', q(page, 'btnAnswer').is_disabled())

    q(page, 'btnHint').click()
    ok('hint revealed', q(page, 'hintNote').is_visible() and 'star' in q(page, 'hintNote').inner_text())

    solve(page, '1.1', 'SELECT city FROM campuses'); solve(page, '1.1', 'SELECT 1')
    ok('Show answer unlocks at three tries', q(page, 'btnAnswer').is_enabled())
    q(page, 'btnAnswer').click()
    ok('answer shown', 'SELECT * FROM campuses' in q(page, 'answerBox').inner_text())
    page.screenshot(path=SHOT + '02-fail.png', full_page=True)

    solve(page, '1.1', 'SELECT campus_id, name, city, opened_year FROM campuses')
    v = q(page, 'verdict').inner_text()
    ok('a second correct route passes with the concept line', 'Correct' in v and 'SELECT chooses columns' in v)
    ok('solved after four tries', rec(page, '1.1')['status'] == 'solved' and rec(page, '1.1')['attempts'] == 4)
    page.screenshot(path=SHOT + '03-pass.png', full_page=True)
    page.locator('#clinic [data-qc-act="next"]').click()
    ok('Next exercise opens 1.2', '1.2' in q(page, 'exTitle').inner_text())

    # a tried exercise offers its last SQL after a reload
    solve(page, '1.2', 'SELECT last_name, first_name, email FROM students')
    ok('1.2 tried', rec(page, '1.2')['status'] == 'tried')
    page.wait_for_function("QueryClinic.app.state.p && !QueryClinic.app.state.p.isDirty()", timeout=10000)
    page.wait_for_timeout(400)
    page.reload(); booted(page)
    ok('progress survives a reload', rec(page, '1.1')['status'] == 'solved' and rec(page, '1.2')['attempts'] == 1)
    ok('meter shows 1 of 40', '1 of 40 solved' in q(page, 'meterText').inner_text())
    page.locator('#clinic [data-qc-unit="1"]').click()
    page.locator('#clinic [data-qc-ex="1.2"]').click()
    ok('Last SQL button offered', q(page, 'btnLast').is_visible())
    q(page, 'btnLast').click()
    ok('Last SQL refills the editor', q(page, 'editor').input_value() == 'SELECT last_name, first_name, email FROM students')
    page.locator('#clinic [data-qc-ex]').count()
    q(page, 'btnBack').click()
    page.locator('#clinic [data-qc-ex="1.1"]').click()
    ok('a solved exercise reopens with its answer', 'campus_id' in q(page, 'editor').input_value())

    # writes are refused and the data stays intact
    q(page, 'editor').fill('DROP TABLE students')
    q(page, 'btnRun').click()
    ok('DROP TABLE refused on Run', 'Only reading' in q(page, 'verdict').inner_text())
    q(page, 'btnCheck').click()
    ok('DROP TABLE refused on Check', 'Only reading' in q(page, 'verdict').inner_text())
    ok('students still has 400 rows', page.evaluate("QueryClinic.app.project().scalar('SELECT count(*) FROM students')") == 400)
    ok('integrity still holds', page.evaluate("QueryClinic.app.verify().then(r => r.ok)"))
    ok('1.1 still solved after the refused write', rec(page, '1.1')['status'] == 'solved')

    # SQL Server notes
    page.evaluate("QueryClinic.app.open('2.1')")
    ok('no tsql note by default', not q(page, 'tsqlNote').is_visible())
    q(page, 'btnGear').click()
    page.locator('#clinic .switch:has([data-qc="setTsql"])').click()
    page.locator('#clinic [data-qc-close="setScrim"]').click()
    ok('tsql note shown with the setting on', q(page, 'tsqlNote').is_visible() and 'TOP' in q(page, 'tsqlNote').inner_text())
    page.evaluate("QueryClinic.app.open('1.3')")
    ok('no tsql note where the exercise has none', not q(page, 'tsqlNote').is_visible())
    page.screenshot(path=SHOT + '04-tsql.png', full_page=True)

    # schema drawer
    q(page, 'btnSchema').click()
    ok('schema drawer lists ten tables', page.locator('#clinic details.tbl').count() == 10)
    page.locator('#clinic details.tbl[data-table="students"] summary').click()
    ok('a table shows columns and three sample rows', page.locator('#clinic details.tbl[data-table="students"] tbody tr').count() == 3 and 'home_campus_id' in page.locator('#clinic details.tbl[data-table="students"]').inner_text())
    page.screenshot(path=SHOT + '05-tables.png')
    page.locator('#clinic [data-qc-close="schemaScrim"]').click()

    # damaged practice data is found and rebuilt with progress kept
    before = page.evaluate("QueryClinic.app.project().objects('SELECT * FROM _qd_clinic ORDER BY exercise_id')")
    page.evaluate("QueryClinic.app.project().execute(\"UPDATE students SET first_name = 'Zed' WHERE student_id = 7\")")
    page.evaluate("QueryClinic.app.verify()")
    page.wait_for_function("!QueryClinic.app.state.integrity.ok", timeout=5000)
    ok('changed data raises the banner', q(page, 'banner').is_visible() and 'students' in q(page, 'banner').inner_text())
    page.locator('#clinic [data-qc-act="rebuild"]').click()
    page.wait_for_function("QueryClinic.app.state.integrity.ok", timeout=10000)
    ok('rebuild restores the data', page.evaluate("QueryClinic.app.project().scalar('SELECT first_name FROM students WHERE student_id = 7')") != 'Zed' and not q(page, 'banner').is_visible())
    after = page.evaluate("QueryClinic.app.project().objects('SELECT * FROM _qd_clinic ORDER BY exercise_id')")
    ok('rebuild keeps every progress record exactly', before == after and len(after) == 2, after)

    # download, reset, restore
    q(page, 'btnGear').click()
    with page.expect_download() as dl:
        q(page, 'btnDownload').click()
    path = SHOT + 'progress.sqlite'; dl.value.save_as(path)
    ok('progress downloads as a sqlite file', open(path, 'rb').read(16) == b'SQLite format 3\x00')
    q(page, 'btnReset').click()
    ok('reset asks for a second tap', 'Tap again' in q(page, 'btnReset').inner_text() and rec(page, '1.1') is not None)
    q(page, 'btnReset').click()
    ok('reset clears progress', page.evaluate("QDClinic.progress(QueryClinic.app.project()).solved") == 0 and rec(page, '1.1') is None)
    q(page, 'fileIn').set_input_files(path)
    page.wait_for_function("QDClinic.progress(QueryClinic.app.project()).solved === 1", timeout=10000)
    ok('restore brings progress back', page.evaluate("QueryClinic.app.project().objects('SELECT * FROM _qd_clinic ORDER BY exercise_id')") == before)

    # finish screen
    page.evaluate("""() => { const p = QueryClinic.app.project();
      QDClinic.EXERCISES.forEach(e => { if (e.id !== '10.2') QDClinic.check(p, e.id, e.solution); }); QueryClinic.app.open('10.2'); }""")
    ex = page.evaluate("QDClinic.exercise('10.2').solution")
    solve(page, '10.2', ex)
    page.locator('#clinic [data-qc-act="next"]').click()
    fin = q(page, 'viewFinish')
    ok('finish screen after the last exercise', fin.is_visible() and 'Course complete' in fin.inner_text() and '40' in fin.inner_text())
    ok('no sideways scroll on the finish screen', sideways(page))
    page.screenshot(path=SHOT + '06-finish.png', full_page=True)

    # mount into a second root with a host project, as Day 200 will
    host = page.evaluate("""() => { const d = document.createElement('div'); d.id = 'host2'; document.body.appendChild(d);
      const p = QDClinic.createProject(); const a = QueryClinic.mount(d, { project: p, autosave: false });
      return a.ready.then(() => ({ units: d.querySelectorAll('.unit').length, same: a.project() === p, meter: d.querySelector('[data-qc=meterText]').textContent })); }""")
    ok('mount with a host project', host['units'] == 10 and host['same'] and '0 of 40' in host['meter'], host)

    ok('no console errors', not errors, errors)
    b.close()

failed = [n for n, c in results if not c]
print('\n%d passed, %d failed' % (len(results) - len(failed), len(failed)))
raise SystemExit(1 if failed else 0)
