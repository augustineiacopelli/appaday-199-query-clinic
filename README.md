# Query Clinic | AppADay 199

Query Clinic is a hands on SQL course in your browser. Forty graded exercises on a built in college database take you from SELECT to window functions. Every answer is checked by its results, not its wording, each mistake gets a specific reason, and notes show where SQL Server differs.

Live at https://augustineiacopelli.github.io/appaday-199-query-clinic/ and part of the [AppADay portfolio](https://augustineiacopelli.github.io/appaday/). Day 199 is the last of six daily builds that assemble into the Query Desk milestone on Day 200.

## Using it

The first visit builds Prairie Ridge College, a fictional school with ten tables (campuses, departments, instructors, courses, terms, rooms, sections, students, enrollments and work orders), from a fixed seed, so the data is the same on every device and nothing is downloaded.

The home screen lists the ten units with a progress bar for each. Tap a unit to see its exercises, each marked New, with its number of tries, or Solved. **Continue** opens the first exercise you have not solved.

On an exercise, write a query and tap **Run** to see its rows without grading, or **Check** (also Ctrl or Cmd plus Enter) to grade it. Grading runs the reference query and yours on the same data and compares the rows, so any correct route passes. A miss shows the specific reason, such as a wrong column count or a missing row, along with how many columns and rows the expected answer has. A pass shows the idea the exercise teaches and a button to the next one. **Hint** reveals a nudge. **Show answer** unlocks after three tries and can put the reference query in the editor. **Last SQL** refills the editor with your last checked attempt. Exercises where row order counts are tagged.

**Tables** opens a drawer with every practice table, its columns with key columns outlined, its row count and three sample rows.

Settings holds the **I am learning SQL Server** switch, which shows a T-SQL note on the nine exercises where SQL Server is written differently, plus **Download progress**, **Restore from a file**, **Check the practice data**, **Rebuild the practice data** and **Reset progress** (two taps). Solving all forty opens the finish screen with totals per unit, checks made and first try solves. **Totals** shows the same screen at any time.

Queries are read only. A DROP, DELETE or UPDATE is refused before it runs, and the engine itself is switched to read only while your query runs, so the practice data cannot be broken from here.

## Progress and the practice data

Progress is stored in its own project named Query Clinic through `QD.store`, the shared IndexedDB store of the Query Desk apps, with autosave tagged 199. Each attempt is a row in the reserved `_qd_clinic` table (status, attempts, last SQL, solved time), so a downloaded progress file is an ordinary SQLite database that also opens in Query Bench.

On every open, the ten practice tables are fingerprinted with SHA-256 and compared with the pinned value in `test/clinic.fingerprint.json` of the 194 workspace (where Web Crypto is missing, they are compared with a freshly generated copy). If anything was changed, for example by opening the project in Query Bench with changes on, a banner names the table and offers **Rebuild and keep progress**, which generates fresh data and carries every `_qd_clinic` row across. A restored file whose data was changed is rebuilt the same way.

## How it is built

One `index.html`, vendored from the Query Desk workspace in [appaday-194-csv-intake](https://github.com/augustineiacopelli/appaday-194-csv-intake). The inline script holds `QD:CORE` 1.2.0 and `QD:CLINIC` 1.0.0, written by `tools/vendor.js` and never edited here, then the interface. There is no chart module and no Chart.js. The engine loads from the portal at `../appaday/vendor/sql.js-1.16.0/`.

The interface is a component: `QueryClinic.mount(root, { project })` builds everything inside `root` and finds every element under it, so Day 200 can mount it in its Learn tab. With no project it opens or creates the stored Query Clinic project. Other options are `autosave: false`, `onProject(project, why)` and `onView(view, exerciseId)`. The returned object has `ready`, `project()`, `open(id)`, `units()`, `finish()`, `verify()`, `rebuild()` and `unmount()`.

Not included by design: new exercises and free practice on your own data.

## Checks

`test/e2e_query_clinic.py` drives the app in Chromium at 375 px with an iPhone user agent, 45 checks: the pinned fingerprint passes, all ten units open an exercise, Run does not grade, a failed check gives its reason and shape, the hint shows, Show answer unlocks at three tries, a second correct route passes, progress and Last SQL survive a reload, DROP TABLE is refused on Run and Check with the data intact, the T-SQL note follows the setting, the drawer shows ten tables with three sample rows, a changed row raises the banner and the rebuild keeps every progress record, download, reset and restore round trip, the finish screen appears, a second mount with a host project works, nothing scrolls sideways, and there are no console errors. Serve the folder that holds this repo and a clone of the portal side by side, then run it:

```
python3 -m http.server 8199
python3 appaday-199-query-clinic/test/e2e_query_clinic.py
```

`node tools/vendor.js --check` in the 194 workspace verifies the vendored modules match `core/`, and `npm test` there passes 116 of 116.
