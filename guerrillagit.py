#!/usr/bin/env python3

from bdflib import reader
import sys
import os
import re
import shutil
import subprocess
import datetime
import shlex
import argparse
import requests

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
parser.add_argument("--github-token", required=False, help="Github Token (create+delete repository)")
args = parser.parse_args()

# Set environment variables
env = os.environ.copy()
env["GIT_AUTHOR_NAME"] = args.name
env["GIT_AUTHOR_EMAIL"] = args.email
env["GIT_COMMITTER_NAME"] = args.name
env["GIT_COMMITTER_EMAIL"] = args.email

MESSAGE = args.message
REPO = args.repository

def parse_github_url(url: str):
    """
    Extracts the owner and repo name from a GitHub URL.
    Supports:
    - https://github.com/user/repo
    - https://github.com/user/repo.git
    - git@github.com:user/repo.git
    """
    patterns = [
        r'^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$',
        r'^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$'
    ]
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            return match.group("owner"), match.group("repo")
    raise ValueError(f"Invalid GitHub repo URL: {url}")

def recreate_github_repo(token: str, username: str, repo_name: str, private: bool = False, org: str = None):
    """
    Delete (if exists) and create a GitHub repository.

    :param token: GitHub Personal Access Token
    :param username: Your GitHub username
    :param repo_name: The name of the repository
    :param private: Whether the new repo should be private
    :param org: (Optional) Name of the GitHub organization (for org-owned repo)
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    repo_owner = org if org else username
    delete_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    create_url = f"https://api.github.com/{'orgs/' + org if org else 'user'}/repos"

    # Delete repo if exists
    delete_response = requests.delete(delete_url, headers=headers)
    if delete_response.status_code == 204:
        print(f"✅ Deleted existing repo: {repo_owner}/{repo_name}")
    elif delete_response.status_code == 404:
        print(f"ℹ️ Repo {repo_owner}/{repo_name} does not exist.")
    else:
        print(f"⚠️ Error deleting repo ({delete_response.status_code}): {delete_response.text}")
        return

    # Create repo
    payload = {
        "name": repo_name,
        "description": "Recreated repository",
        "private": private
    }

    create_response = requests.post(create_url, headers=headers, json=payload)
    if create_response.status_code == 201:
        repo_url = create_response.json().get("html_url", "")
        print(f"✅ Created repo: {repo_owner}/{repo_name}")
        print(f"🔗 {repo_url}")
    else:
        print(f"❌ Failed to create repo ({create_response.status_code}): {create_response.json()}")

# Determine the first Sunday in the past 365-357 days

if args.year:
    YEAR = args.year
    first_sunday_date = datetime.date(YEAR, 1, 7)
    while first_sunday_date.weekday() != 6:  # Sunday = 6
        first_sunday_date += datetime.timedelta(days=1)
else:
    today = datetime.date.today()

    # Go back either 365 or 366 days depending on whether the previous year is a leap year
    last_year = today.year - 1
    days_back = 366 if last_year % 4 == 0 else 365

    first_sunday_date = None
    for delta_days in range(days_back, days_back - 8, -1):  # max 1 week span
        candidate_date = today - datetime.timedelta(days=delta_days)
        if candidate_date.weekday() == 6:
            first_sunday_date = candidate_date
            break

    YEAR = first_sunday_date.year

first_sunday_timestamp = int(first_sunday_date.strftime("%s"))

# Navigate to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

if args.github_token:
    # Extract owner and repo name from URL
    # e.g. https://github.com/user/repo.git => user, repo
    try:
        owner, repo_name = parse_github_url(args.repository)
        recreate_github_repo(
            token=args.github_token,
            username=owner,
            repo_name=repo_name,
            private=False
        )
    except Exception as e:
        print(f"❌ Could not parse repository URL: {e}")

# Initialize new Git repository
shutil.rmtree(".git", ignore_errors=True)
subprocess.run("git init", shell=True)
subprocess.run("git checkout -b main", shell=True)

# Generate commit coordinates
font = parse_bdf_font(FONT)
commit_days = render_text(MESSAGE, font)

for key in commit_days:
    if key is None:
        continue
    week = key[0]
    day = key[1]
    for i in range(400):
        commit_date = get_commit_date(week, day)
        env["GIT_AUTHOR_DATE"] = commit_date
        env["GIT_COMMITTER_DATE"] = commit_date
        subprocess.run(
            shlex.split(f"git commit --allow-empty -m 'Commit[{i}] at week {week}, day {day}'"),
            env=env
        )

print("Repository with pattern created!")

# Final commit and push
subprocess.run("git add *", shell=True, env=env)
subprocess.run("git commit -m 'adding resources'", shell=True, env=env)
subprocess.run(shlex.split(f"git remote add origin {REPO}"), env=env)
subprocess.run("git push origin main -f", shell=True, env=env)
