"""A curated dictionary of technical and professional skills.

Each skill has a canonical name (what we show the user) and a list of
aliases (how it might be written in a resume or job posting).

Aliases are matched case-insensitively unless they start with "cs:", which
means "match this exact capitalization". That keeps everyday words from
counting as skills: "cs:React" matches the library but not "react quickly",
and "cs:Led" matches "Led a team" but not an LED on a circuit board.

Some names are too ambiguous to match on their own ("Go", "C", "Spring"),
so only their unambiguous spellings are listed ("golang", "C/C++",
"Spring Boot").
"""

from __future__ import annotations

SKILLS: dict[str, dict[str, list[str]]] = {
    "Languages": {
        "Python": ["python", "python3"],
        "Java": ["java"],
        "JavaScript": ["javascript", "js", "es6", "ecmascript"],
        "TypeScript": ["typescript"],
        "C": ["cs:C/C++", "cs:C, C++", "cs:C and C++", "cs:C or C++", "embedded c", "c programming", "c99"],
        "C++": ["c++", "cpp"],
        "C#": ["c#", "csharp"],
        "Go": ["golang"],
        "Rust": ["rust"],
        "Kotlin": ["kotlin"],
        "Swift": ["swift"],
        "Ruby": ["ruby"],
        "PHP": ["php"],
        "SQL": ["sql"],
        "Bash": ["bash", "shell scripting", "shell scripts"],
        "MATLAB": ["matlab"],
        "HTML": ["html", "html5"],
        "CSS": ["css", "css3", "sass", "scss"],
    },
    "Frameworks & Libraries": {
        "React": ["cs:React", "react.js", "reactjs"],
        "Angular": ["cs:Angular", "angularjs", "angular.js"],
        "Vue": ["vue", "vue.js", "vuejs"],
        "Next.js": ["next.js", "nextjs"],
        "Node.js": ["cs:Node", "node.js", "nodejs"],
        "Express": ["cs:Express", "express.js", "expressjs"],
        "Django": ["django"],
        "Flask": ["flask"],
        "FastAPI": ["fastapi"],
        "Spring Boot": ["spring boot", "spring framework", "spring mvc"],
        ".NET": [".net", "dotnet", "asp.net"],
        "ROS": ["ros", "ros2", "ros 2"],
        "OpenCV": ["opencv"],
        "NumPy": ["numpy"],
        "pandas": ["pandas"],
        "PyTorch": ["pytorch"],
        "TensorFlow": ["tensorflow"],
        "scikit-learn": ["scikit-learn", "sklearn"],
    },
    "Data & Databases": {
        "PostgreSQL": ["postgresql", "postgres"],
        "MySQL": ["mysql"],
        "MongoDB": ["mongodb", "mongo"],
        "Redis": ["redis"],
        "SQLite": ["sqlite"],
        "GraphQL": ["graphql"],
        "REST APIs": ["cs:REST", "restful", "rest api", "rest apis"],
        "Machine Learning": ["machine learning", "ml"],
        "Data Structures & Algorithms": ["data structures and algorithms", "data structures", "algorithms"],
    },
    "Cloud & DevOps": {
        "AWS": ["aws", "amazon web services"],
        "Azure": ["azure"],
        "Google Cloud": ["gcp", "google cloud"],
        "Docker": ["docker", "containers", "containerization"],
        "Kubernetes": ["kubernetes", "k8s"],
        "CI/CD": [
            "ci/cd",
            "ci pipeline",
            "ci pipelines",
            "continuous integration",
            "continuous delivery",
            "continuous deployment",
            "github actions",
            "jenkins",
        ],
        "Linux": ["linux", "unix"],
        "Terraform": ["terraform"],
    },
    "Tools & Practices": {
        "Git": ["git", "github", "gitlab", "version control"],
        "Testing": [
            "testing",
            "unit tests",
            "automated tests",
            "test-driven",
            "tdd",
            "pytest",
            "junit",
            "jest",
        ],
        "Agile": ["agile", "scrum", "kanban"],
        "Object-Oriented Programming": ["object-oriented", "object oriented", "oop"],
        "Debugging": ["debugging", "debug", "troubleshooting"],
        "Embedded Systems": ["embedded", "firmware", "microcontroller", "microcontrollers"],
        "Code Review": ["code review", "code reviews"],
    },
    "Soft Skills": {
        "Communication": ["communication", "communicate", "communicator"],
        "Teamwork": [
            "teamwork",
            "team player",
            "collaboration",
            "collaborate",
            "collaborated",
            "collaborating",
            "cross-functional",
        ],
        "Leadership": ["leadership", "cs:Led", "cs:led", "mentor", "mentored", "mentoring"],
        "Problem Solving": ["problem solving", "problem-solving", "problem solver"],
    },
}


def iter_skills():
    """Yield (category, canonical_name, aliases) for every known skill."""
    for category, skills in SKILLS.items():
        for name, aliases in skills.items():
            yield category, name, aliases
