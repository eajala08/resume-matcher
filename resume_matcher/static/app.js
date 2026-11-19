"use strict";

const MAX_CHARS = 50000;
const $ = (id) => document.getElementById(id);

const form = $("form");
const resumeBox = $("resume");
const jobBox = $("job");
const submitBtn = $("submit");
const formError = $("form-error");
const results = $("results");

// Everything that comes from user text goes in with textContent, never innerHTML.
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function showError(message) {
  formError.textContent = message;
  formError.hidden = !message;
}

// {category: [names]} in first-seen order.
function groupByCategory(hits) {
  const groups = new Map();
  for (const hit of hits) {
    if (!groups.has(hit.category)) groups.set(hit.category, []);
    groups.get(hit.category).push(hit.skill);
  }
  return groups;
}

function skillGroup(title, hits, chipClass) {
  if (hits.length === 0) return null;
  const section = el("div", "group");
  section.appendChild(el("h3", "", title));
  for (const [category, names] of groupByCategory(hits)) {
    const row = el("p", "category");
    row.appendChild(el("span", "category-name", category));
    for (const name of names) row.appendChild(el("span", `chip ${chipClass}`, name));
    section.appendChild(row);
  }
  return section;
}

function listWords(names) {
  if (names.length <= 1) return names.join("");
  return `${names.slice(0, -1).join(", ")} or ${names[names.length - 1]}`;
}

function render(report) {
  const details = $("details");
  details.replaceChildren();

  const score = $("score");
  const verdict = $("verdict");
  const fill = $("fill");
  const card = score.closest(".score-card");
  card.className = `score-card tone-${report.tone}`;

  if (report.skills_in_posting === 0) {
    score.textContent = "–";
    verdict.textContent = "Nothing to score";
    fill.style.width = "0";
    const empty = el(
      "p",
      "empty",
      "No recognizable skills were found in the job posting. Check that the second box holds the job posting and that it is plain text."
    );
    details.appendChild(empty);
  } else {
    score.textContent = `${report.score}%`;
    verdict.textContent = report.verdict;
    fill.style.width = `${report.score}%`;

    const missingRequired = report.missing.filter((s) => !s.preferred);
    const missingNice = report.missing.filter((s) => s.preferred);
    const sections = [
      skillGroup("Missing: required", missingRequired, "missing"),
      skillGroup("Missing: nice to have", missingNice, "nice"),
      skillGroup("Already on your resume", report.matched, "have"),
    ];
    for (const section of sections) if (section) details.appendChild(section);

    if (report.missing_keywords.length) {
      const section = el("div", "group");
      section.appendChild(el("h3", "", "Other words the posting repeats"));
      const row = el("p", "category");
      for (const word of report.missing_keywords) row.appendChild(el("span", "chip other", word));
      section.appendChild(row);
      details.appendChild(section);
    }

    if (missingRequired.length) {
      const names = missingRequired.slice(0, 3).map((s) => s.skill);
      details.appendChild(
        el("p", "tip", `If you have experience with ${listWords(names)}, say so in a bullet point.`)
      );
    }
  }

  results.hidden = false;
  $("results-heading").focus({ preventScroll: true });
  results.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
}

async function check() {
  showError("");
  if (!resumeBox.value.trim() || !jobBox.value.trim()) {
    showError("Paste both your resume and the job posting first.");
    (resumeBox.value.trim() ? jobBox : resumeBox).focus();
    return;
  }
  submitBtn.disabled = true;
  submitBtn.textContent = "Checking…";
  try {
    const response = await fetch("/api/match", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume: resumeBox.value, job: jobBox.value }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      showError(data.error || "Something went wrong. Try again.");
      return;
    }
    render(data);
  } catch {
    showError("Could not reach the server. Check your connection and try again.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Check my match";
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  check();
});

for (const box of [resumeBox, jobBox]) {
  box.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      check();
    }
  });
}

$("example").addEventListener("click", async () => {
  showError("");
  try {
    const [resume, job] = await Promise.all(
      ["/example/resume", "/example/job"].map((url) => fetch(url).then((r) => r.text()))
    );
    resumeBox.value = resume;
    jobBox.value = job;
    check();
  } catch {
    showError("Could not load the example. Check your connection and try again.");
  }
});

$("clear").addEventListener("click", () => {
  resumeBox.value = "";
  jobBox.value = "";
  results.hidden = true;
  showError("");
  resumeBox.focus();
});

for (const input of document.querySelectorAll("input[type=file]")) {
  input.addEventListener("change", async () => {
    const file = input.files[0];
    input.value = ""; // lets the same file be chosen again
    if (!file) return;
    if (/\.(pdf|docx?)$/i.test(file.name)) {
      showError(`${file.name} is not plain text. Copy the text out of it and paste it into the box.`);
      return;
    }
    if (file.size > MAX_CHARS * 4) {
      showError(`${file.name} is too large. Resumes and job postings are a few KB of text.`);
      return;
    }
    showError("");
    const text = await file.text();
    $(input.dataset.target).value = text.slice(0, MAX_CHARS);
  });
}
