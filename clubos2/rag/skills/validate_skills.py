from __future__ import annotations

import os
import re
import sys

# Required level 2 headings in each skill file
REQUIRED_HEADINGS = [
    r"^##\s+Purpose\s*$",
    r"^##\s+Metrics\s+on\s+this\s+screen\s*$",
    r"^##\s+Valid\s+queries\s*$",
    r"^##\s+Invalid\s+queries\s*$",
    r"^##\s+Known\s+gotchas\s*$",
    r"^##\s+Stakeholder\s+language\s*$",
    r"^##\s+What\s+the\s+Scout\s+should\s+NEVER\s+do\s+with\s+this\s+screen\s*$",
    r"^##\s+References\s*$",
]


def validate_file(file_path: str) -> tuple[bool, bool, list[str]]:
    """Validates a single skill markdown file.

    Returns:
        (has_valid_headers, has_todo, missing_headers)
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Check for TODO markers
    has_todo = bool(re.search(r"TODO", content, re.IGNORECASE))

    # Split lines to check headers
    lines = content.splitlines()
    found_headers = set()

    for line in lines:
        for pattern in REQUIRED_HEADINGS:
            if re.match(pattern, line):
                found_headers.add(pattern)

    missing = []
    for pattern in REQUIRED_HEADINGS:
        if pattern not in found_headers:
            # Simplify pattern for readable output
            readable = pattern.replace(r"^##\s+", "").replace(r"\s*", "").replace(r"\s+", " ")
            missing.append(readable)

    return len(missing) == 0, has_todo, missing


def main() -> None:
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # List all markdown files in this directory
    files = [f for f in os.listdir(current_dir) if f.endswith(".md") and f != "README.md"]
    files.sort()

    errors_found = False
    print("=" * 60)
    print("ClubOS 2.0 Screen Skill Files Validation Report")
    print("=" * 60)

    for filename in files:
        file_path = os.path.join(current_dir, filename)
        has_valid_headers, has_todo, missing = validate_file(file_path)

        status_str = "OK"
        detail_str = ""

        # Special constraint: priority_board and signal_engine must NOT have TODOs
        is_hero_file = filename in ("priority_board.md", "signal_engine.md")

        if not has_valid_headers:
            status_str = "INVALID HEADINGS"
            detail_str = f"Missing sections: {', '.join(missing)}"
            errors_found = True
        elif is_hero_file and has_todo:
            status_str = "TODO FOUND"
            detail_str = "Hero skill file must be fully completed and contain no TODOs."
            errors_found = True
        elif has_todo:
            status_str = "INCOMPLETE (TODO)"
            detail_str = "Skeleton matches structure; needs future human completion."
        else:
            status_str = "FULLY COMPLETED"

        print(f"{filename:<25} | Status: {status_str:<20} | {detail_str}")

    print("=" * 60)
    if errors_found:
        print("Validation FAILED: Correct heading structures or hero file TODO markers.")
        sys.exit(1)
    else:
        print("Validation PASSED successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
