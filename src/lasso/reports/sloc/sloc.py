"""SLOC Counter script."""
import csv
import json
import os
import subprocess
from collections import defaultdict

import requests

# GitHub organization and personal access token
GITHUB_ORG = "NASA-PDS"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# Headers for GitHub API requests
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

IGNORE_REPOS = [
    "archive-viewer",
    "atlas",
    "pds4-npm-utils",
    "naif-pds4-bundler",
    "pds4-product-registry",
    "pds-opencsv",
    "FFmpeg-fateserver",
    "FFmpeg",
    "openh264",
]


def get_org_repos(org):
    """Get repos.

    Fetch all repositories for a GitHub organization.
    """
    repos = []
    url = f"https://api.github.com/orgs/{org}/repos"
    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        repos.extend(response.json())
        # Get the next page of results if it exists
        url = response.links.get("next", {}).get("url")
    return repos


def clone_repo(repo_url, repo_name):
    """Clone repo.

    Clone a repository using git.
    """
    repo_dir = f"./repos/{repo_name}"
    subprocess.run(["git", "clone", "--depth", "1", repo_url, repo_dir], check=True)
    return repo_dir


def count_sloc(repo_dir):
    """Count SLOC.

    Count the source lines of code in a directory using cloc 2.04.
    """
    try:
        result = subprocess.run(["cloc", repo_dir, "--json"], capture_output=True, text=True, check=True)
        # Parse JSON output
        cloc_data = json.loads(result.stdout)

        # Extract total SLOC and breakdown by language
        language_sloc = {}
        for language, stats in cloc_data.items():
            if language not in ["header", "SUM"]:
                language_sloc[language] = stats.get("code", 0)

        total_sloc = cloc_data.get("SUM", {}).get("code", 0)
        return total_sloc, language_sloc
    except subprocess.CalledProcessError as e:
        print(f"Error running cloc: {e.stderr}")
        return None, {}


def main():
    """main."""
    # Create a directory to store cloned repositories
    os.makedirs("repos", exist_ok=True)

    # Prepare CSV file to store results
    csv_file = "sloc_report.csv"
    with open(csv_file, mode="w", newline="") as file:
        writer = csv.writer(file)

        # Get all repositories in the organization
        repos = get_org_repos(GITHUB_ORG)

        # Determine all languages used across the organization
        all_languages = set()
        repo_language_data = []
        total_sloc_org = 0
        total_language_sloc_org = defaultdict(int)

        for repo in repos:
            repo_name = repo["name"]
            repo_url = repo["clone_url"]

            if repo["name"] in IGNORE_REPOS:
                continue

            print(f"Cloning repository: {repo_name}")
            try:
                repo_dir = clone_repo(repo_url, repo_name)

                print(f"Counting SLOC for repository: {repo_name}")
                repo_sloc, language_sloc = count_sloc(repo_dir)

                if repo_sloc is not None:
                    total_sloc_org += repo_sloc
                    for lang, sloc in language_sloc.items():
                        total_language_sloc_org[lang] += sloc
                        all_languages.add(lang)
                    repo_language_data.append((repo_name, repo_sloc, language_sloc))
                else:
                    repo_language_data.append((repo_name, "Error", {}))
            except Exception as e:
                print(f"Error processing repository {repo_name}: {e}")
                repo_language_data.append((repo_name, "Error", {}))
            finally:
                # Clean up the cloned repository
                subprocess.run(["rm", "-rf", repo_dir], check=True)

        # Write CSV header dynamically based on all languages
        language_columns = sorted(all_languages)
        header = ["Repository Name", "Total SLOC"] + language_columns
        writer.writerow(header)

        # Write repository data
        for repo_name, total_sloc, language_sloc in repo_language_data:
            row = [repo_name, total_sloc]
            for lang in language_columns:
                row.append(language_sloc.get(lang, 0))
            writer.writerow(row)

        # Write total organization SLOC row
        total_row = ["Total", total_sloc_org]
        for lang in language_columns:
            total_row.append(total_language_sloc_org.get(lang, 0))
        writer.writerow(total_row)

    print(f"Total SLOC for organization {GITHUB_ORG}: {total_sloc_org}")
    print(f"Language Breakdown for organization: {dict(total_language_sloc_org)}")
    print(f"Report saved to {csv_file}")


if __name__ == "__main__":
    main()
