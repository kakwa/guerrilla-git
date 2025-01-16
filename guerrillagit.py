#!/usr/bin/env python3

from bdflib import reader
import sys
import os
import shutil
import subprocess
import datetime
import shlex
import argparse

FONT = "tkw-font-7-n.bdf"

def parse_bdf_font(bdf_path):
    with open(bdf_path, 'rb') as f:
        font = reader.read_bdf(f)
    return font

def render_text(text, font):
    ret = []
    for char_index, char in enumerate(text):
        if ord(char) == 32:
            continue
        glyph = font[ord(char)]
        char_x_offset = char_index * glyph.bbW  # Deriving offset from bounding box width
        
        for y, row in enumerate(glyph.iter_pixels()):
            line_output = [[x + char_x_offset, y] if pixel else None for x, pixel in enumerate(row)]
            ret += line_output
    return ret

def get_commit_date(week, day):
    timestamp = first_sunday_timestamp + (week * 7 + day) * 86400
    return datetime.datetime.fromtimestamp(timestamp).isoformat()

# Argument parsing
parser = argparse.ArgumentParser(description="Generate Git commits in a pattern")
parser.add_argument("--name", required=True, help="Git author name")
parser.add_argument("--email", required=True, help="Git author email")
parser.add_argument("--year", type=int, help="Year for the commits (default: auto-detect)")
parser.add_argument("--message", required=True, help="Message to encode in commits")
parser.add_argument("--repository", required=True, help="Git repository URL")
args = parser.parse_args()

# Set environment variables
env = os.environ.copy()
env["GIT_AUTHOR_NAME"] = args.name
env["GIT_AUTHOR_EMAIL"] = args.email
env["GIT_COMMITTER_NAME"] = args.name
env["GIT_COMMITTER_EMAIL"] = args.email

MESSAGE = args.message
REPO = args.repository



# Determine the first Sunday in the past 365-357 days
if args.year:
    YEAR = args.year
    first_sunday_date = datetime.date(YEAR, 1, 7)
    while first_sunday_date.weekday() != 6:
        first_sunday_date += datetime.timedelta(days=1)
else:
    today = datetime.date.today()
    first_sunday_date = None
    for days_ago in range(365, 356, -1):
        candidate_date = today - datetime.timedelta(days=days_ago)
        if candidate_date.weekday() == 6:
            first_sunday_date = candidate_date
            break
    YEAR = first_sunday_date.year

first_sunday_timestamp = int(first_sunday_date.strftime("%s"))

# Navigate to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Initialize new Git repository
shutil.rmtree(".git", ignore_errors=True)
subprocess.run("git init", shell=True)
subprocess.run("git checkout -b main", shell=True)

# Create initial file
with open("file.txt", "w") as f:
    f.write("First file\n")
subprocess.run("git add file.txt", shell=True)

# Generate commit coordinates
font = parse_bdf_font(FONT)
commit_days = render_text(MESSAGE, font)
print(commit_days)

# Create commits
for key in commit_days:
    if key is None:
        continue
    week = key[0]
    day = key[1]
    for _ in range(100):
        commit_date = get_commit_date(week, day)
        with open("file.txt", "a") as f:
            f.write(f"Commit at week {week}, day {day}\n")
        subprocess.run("git add file.txt", shell=True)
        env["GIT_AUTHOR_DATE"] = commit_date
        env["GIT_COMMITTER_DATE"] = commit_date
        subprocess.run(shlex.split(f"git commit -m 'Commit for letter'"), env=env)

print("Repository with pattern created!")

# Final commit and push
subprocess.run("git add *", shell=True, env=env)
subprocess.run("git commit -m 'adding resources'", shell=True, env=env)
subprocess.run(shlex.split(f"git remote add origin {REPO}"), env=env)
subprocess.run("git push origin main -f", shell=True, env=env)
