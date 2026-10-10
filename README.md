# Xreading Progress Meter

A small, privacy-first tool for teachers who use [Xreading](https://xreading.com) for extensive reading.
It turns an Xreading class export into a student-facing web page with two parts:

- **A personal grade calculator.** A student types in their total words read and sees their current reading points, the next level, and how many words per week they need to reach each level by the end of term.
- **"How the class is climbing".** An aggregate ladder showing how many students in each class have reached each level, and how many haven't started yet.

The page is a single static HTML file, so it can be hosted on GitHub Pages and embedded in a class blog or LMS with an iframe.

**No student data ever leaves the teacher's computer.** The Xreading CSV (which contains names, IDs and usernames) is read locally. The published page holds only class-level counts.

## Files

| File | Purpose |
|---|---|
| `reading-progress.html` | The student page (calculator + class ladder). Ships with demo data. |
| `admin.html` | Browser tool: drop in an Xreading CSV and the page, set term dates and levels, download the updated page. Everything runs locally; nothing is uploaded. |
| `update-reading-progress.py` | Command-line equivalent of `admin.html` (Python 3, standard library only). |
| `examples/sample-xreading-export.csv` | Synthetic export (fake students) for trying the tools. |

## Quick start

1. Try it with the sample data:
   ```bash
   python3 update-reading-progress.py examples/sample-xreading-export.csv
   ```
   then open `reading-progress.html` in a browser.
2. Set your own grading scheme and term dates, either in `admin.html` or in the `CFG:START … CFG:END` block of the page.
3. Export your class data from Xreading as CSV and run the script (or use `admin.html`) whenever you want to refresh the numbers.
4. Publish `reading-progress.html` however you like, e.g. GitHub Pages from a repository of your own.

The tools only need three CSV columns: `Classes`, `Words Read` and `Read Speed (Word/Min)`. Rows whose class contains `Demo Class` (teacher/test accounts) are dropped.

## Privacy

- Never commit or upload the raw Xreading CSV. `.gitignore` excludes `*.csv` (except the synthetic example).
- The published page contains only per-class totals: number of students, number at each level, number at zero, and the cohort's average reading speed.
- Very small groups can make an individual's progress guessable. If that matters in your setting, merge small classes before publishing.

## Background

Built for first-year English courses at Asahikawa City University (Japan), where extensive reading counts towards the course grade. Shared so other Xreading teachers can adapt it.

## Citation

If you use or adapt this tool, please cite it (see `CITATION.cff`, or the "Cite this repository" button on GitHub).

## Licence

MIT. See [LICENSE](LICENSE).
