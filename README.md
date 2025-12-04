# Guerrilla-Git

## Description

Write a small message (up to 10 characters) in your github contributions.

![Example](https://cdn.rawgit.com/kakwa/guerrilla-git/master/sc.png)

## Requirements

* `Python3`
* `bdflib`
* `git`

Github personal Token:

https://github.com/settings/personal-access-tokens/new

* `Repository access` -> `All repositories`
* `Administration` -> `Access: Read and write`

## Usage

Checkout this tool
```sh
git clone https://github.com/kakwa/guerrilla-git
cd guerrilla-git
```

In Github, create a bare repository (no template).

Then run:
```sh
# Run
./guerrillagit.py --name "kakwa" \
  --email "kakwa@example.com"
  --message "Hello" \
  --repository "git@github.com:kakwa/bonjour.git"
```

**Disclaimer**: run on dedicated repositories, this script deletes all the repository history, both local and remote.

## Help
```sh
./guerrillagit.py --help

usage: guerrillagit.py [-h] --name NAME --email EMAIL [--year YEAR] --message MESSAGE --repository REPOSITORY --github-token "<GH_TOKEN>"

Generate Git commits in a pattern

options:
  -h, --help            show this help message and exit
  --name NAME           Git author name
  --email EMAIL         Git author email
  --year YEAR           Year for the commits (default: auto-detect)
  --message MESSAGE     Message to encode in commits
  --repository REPOSITORY
                        Git repository URL
```
