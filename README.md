# Resume Matcher

[![tests](https://github.com/eajala08/resume-matcher/actions/workflows/tests.yml/badge.svg)](https://github.com/eajala08/resume-matcher/actions/workflows/tests.yml)

A command-line tool that compares your resume to a job posting and tells you
which skills the posting asks for that your resume never mentions.

Many companies filter resumes by keyword before a person reads them. This
tool shows you the gaps first, so you can add the experience you already
have but forgot to write down.

```
$ python3 -m resume_matcher examples/resume.txt examples/job_posting.txt

  RESUME MATCH
  █████████████████████░░░░░░░░░  71%  Good match, a few gaps

  Missing — required
    Cloud & DevOps: AWS, CI/CD
    Soft Skills: Communication

  Missing — nice to have
    Cloud & DevOps: Kubernetes
    Data & Databases: PostgreSQL
    Languages: TypeScript

  Already on your resume
    Data & Databases: Data Structures & Algorithms, REST APIs
    Cloud & DevOps: Linux, Docker
    Frameworks & Libraries: ROS, React
    Languages: C++, Python
    Tools & Practices: Debugging, Git, Testing

  Other words the posting repeats
    fleet, robotics, robots

  Tip: if you have experience with AWS, CI/CD or Communication, say so in a bullet point.
```

## Run it

You need Python 3.9 or newer. There is nothing else to install.

```bash
git clone https://github.com/eajala08/resume-matcher.git
cd resume-matcher
python3 -m resume_matcher examples/resume.txt examples/job_posting.txt
```

To use your own files, save your resume and the job posting as plain text
(`.txt` or `.md`) and pass their paths in that order.

| Option | What it does |
| --- | --- |
| `--json` | Print the result as JSON so another program can read it |
| `--top N` | List up to N extra repeated keywords (default 10) |
| `--min-score PCT` | Exit with code 1 if the score is below PCT, useful in scripts |
| `--no-color` | Turn off colored output |

## How the score works

1. **Split the posting into required and nice-to-have.** Lines under a
   heading like "Nice to have" or "Preferred" are optional. So is any single
   line that says so itself, such as "Kubernetes is a plus".
2. **Find the skills.** About 70 skills are matched from a dictionary in
   [`skills.py`](resume_matcher/skills.py). Each skill lists the ways people
   write it, so `Postgres`, `PostgreSQL`, `k8s` and `Kubernetes` all land on
   the right name.
3. **Weigh them.** A required skill counts 1 point and an optional one counts
   half. A skill the posting repeats counts up to twice as much.
4. **Score.** The score is the points your resume covers divided by the
   points the posting asks for.

### Matching is stricter than a text search

A plain search for `java` also finds `javascript`, and a search for `rest`
finds "the rest of the team". The matcher avoids both:

- Symbols are part of a term, so `C++`, `C#`, `.NET` and `Node.js` match as
  whole words, and `js` is not found inside `Node.js`.
- Skills that are also everyday words must be capitalized the way the skill
  is. `React` matches the library but "react quickly" does not. `Led a team`
  counts as leadership but an `LED` on a circuit board does not.
- If two spellings overlap in the text, such as `REST` inside `REST API`, the
  mention is counted once.

## Limitations

- It reads plain text only. Copy the text out of a PDF or Word file first.
- It only knows the skills in its dictionary. Anything else can still show up
  under "Other words the posting repeats".
- A few names are too ambiguous to match alone. `Go`, `C` and `Spring` are
  only matched as `golang`, `C/C++` and `Spring Boot`.
- It checks whether a word appears on your resume. It cannot judge how well
  you know it.

## Project layout

```
resume_matcher/
  skills.py    the skill dictionary
  text.py      cleaning text, splitting it into words, matching whole terms
  matcher.py   required vs. optional sections, weights, the score
  report.py    the terminal report
  cli.py       command-line options
tests/         34 tests, run on every push by GitHub Actions
examples/      a sample resume and job posting
```

## Tests

```bash
python3 -m unittest discover -s tests
```

## How it was built

I planned the features and behavior and built the tool with Claude Code as a
pair programmer. It leans on ideas from my data structures course: hash maps
for the skill dictionary and word counts, sets for fast lookups, sorting with
a custom key, and unit tests for every rule.

## License

MIT
