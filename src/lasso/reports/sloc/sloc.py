"""CLI tool to analyze and visualize source lines of code (SLOC) across all repositories in a GitHub organization.

Results are saved in both a current report and a historical CSV log, with optional visualization capabilities.
"""
import argparse
import csv
import json
import logging
import os
import subprocess
from collections import defaultdict
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

HEADERS = {}
HISTORICAL_LOG_DIR = "data/history"
OUTPUT_DIR = "output"
HISTORICAL_LOG_FILE = os.path.join(HISTORICAL_LOG_DIR, "sloc_history.csv")
SLOC_REPORT_FILE = os.path.join(OUTPUT_DIR, "sloc_report.csv")
PLOT_TRENDS_FILE = os.path.join(OUTPUT_DIR, "sloc_trends.png")
PLOT_LEGENDS_FILE = os.path.join(OUTPUT_DIR, "sloc_trends_legend.png")
PLOT_TOTAL_FILE = os.path.join(OUTPUT_DIR, "total_sloc.png")
PLOT_LANGUAGE_FILE = os.path.join(OUTPUT_DIR, "language_trends.png")
PLOT_REPO_FILE = os.path.join(OUTPUT_DIR, "repo_comparison.png")
PLOT_ACTIVE_FILE = os.path.join(OUTPUT_DIR, "active_repos.png")

IGNORE_REPOS = [
    "naif-pds4-bundler",
    "pds4-npm-utils",
    "atlas",
    "archive-viewer",
    "drupal-temp",
    "portal-wp-smd",
    "radiosci-pds4",
    "ppi-reviews",
    "pytrk234",
    "pds-opencsv",
    "kdp",
    "ffmpeg",
    "ffmpeg-web",
    "openh264",
    "mediainfo",
    "product_relationships",
    "pds.nasa.gov-search-prototype",
    "ffmpeg-fateserver",
    "pds4-migrate-tools",
    "pds4-product-registry",
    "portal-legacy",
    "validate-test",
    "registry-ref-data",
    "pds4-ccb",
    "portal-wp",
    "edwg",
]


def ensure_directories():
    """Ensure that all required directories exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(HISTORICAL_LOG_DIR, exist_ok=True)


def get_org_repos(org):
    """Fetch all repositories for a GitHub organization."""
    repos = []
    url = f"https://api.github.com/orgs/{org}/repos"
    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        repos.extend(response.json())
        url = response.links.get("next", {}).get("url")
    return repos


def clone_repo(repo_url, repo_name):
    """Clone a repository using Git."""
    repo_dir = f"./repos/{repo_name}"
    subprocess.run(["git", "clone", "--depth", "1", repo_url, repo_dir], check=True)
    return repo_dir


def count_sloc(repo_dir):
    """Count source lines of code (SLOC) in a repository using cloc."""
    try:
        result = subprocess.run(["cloc", repo_dir, "--json"], capture_output=True, text=True, check=True)
        cloc_data = json.loads(result.stdout)
        language_sloc = {
            lang: stats.get("code", 0) for lang, stats in cloc_data.items() if lang not in ["header", "SUM"]
        }
        total_sloc = cloc_data.get("SUM", {}).get("code", 0)
        return total_sloc, language_sloc
    except subprocess.CalledProcessError as e:
        print(f"Error running cloc: {e.stderr}")
        return None, {}


def write_historical_log(timestamp, repo_name, total_sloc, language_sloc):
    """Write SLOC data for a repository to the historical CSV log."""
    ensure_directories()
    file_exists = os.path.isfile(HISTORICAL_LOG_FILE)
    with open(HISTORICAL_LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Repository Name", "Total SLOC", "Language Breakdown"])
        writer.writerow([timestamp, repo_name, total_sloc, json.dumps(language_sloc)])


def load_data(historical=False):
    """Load and parse the SLOC data.

    Args:
        historical (bool): If True, load historical data from HISTORICAL_LOG_FILE,
                         otherwise load current snapshot from sloc_report.csv
    """
    if historical:
        df = pd.read_csv(HISTORICAL_LOG_FILE)
        # Parse language breakdown from JSON string
        df["Language Breakdown"] = df["Language Breakdown"].apply(json.loads)
        # Explode language data into columns
        languages_df = pd.json_normalize(df["Language Breakdown"].tolist())
        df = pd.concat([df.drop("Language Breakdown", axis=1), languages_df], axis=1)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        return df
    else:
        df = pd.read_csv(SLOC_REPORT_FILE)
        # Convert language columns to numeric
        for col in df.columns:
            if col not in ["Repository Name", "Total SLOC"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df


def plot_total_sloc(df):
    """Plot total SLOC by repository."""
    plt.figure(figsize=(20, 12))
    repos = df[df["Repository Name"] != "Total"]  # Exclude the total row
    top_repos = repos.nlargest(20, "Total SLOC")

    # Create bar plot with consistent styling
    bars = plt.bar(top_repos["Repository Name"], top_repos["Total SLOC"], color=plt.cm.tab20.colors)

    # Add value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, height, f"{int(height):,}", ha="center", va="bottom", fontsize=10)

    plt.title("Top 20 Repositories by SLOC", fontsize=14, pad=20)
    plt.xlabel("Repository", fontsize=12)
    plt.ylabel("Total SLOC (Ks)", fontsize=12)
    plt.xticks(rotation=45, ha="right")

    # Format y-axis in thousands
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x / 1000):,}k"))

    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(PLOT_TOTAL_FILE, bbox_inches="tight")
    plt.close()


def plot_language_trends(df):
    """Plot language distribution across repositories."""
    plt.figure(figsize=(20, 12))
    languages = [col for col in df.columns if col not in ["Repository Name", "Total SLOC"]]
    # Get top 10 languages by total SLOC
    top_languages = df[languages].sum().nlargest(10)

    # Create bar plot with consistent styling
    bars = plt.bar(top_languages.index, top_languages.values, color=plt.cm.tab10.colors)

    # Add value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, height, f"{int(height):,}", ha="center", va="bottom", fontsize=10)

    plt.title("Top 10 Languages by SLOC", fontsize=14, pad=20)
    plt.xlabel("Language", fontsize=12)
    plt.ylabel("Total SLOC (thousands)", fontsize=12)

    # Format y-axis in thousands
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x / 1000):,}k"))

    plt.xticks(rotation=45, ha="right")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(PLOT_LANGUAGE_FILE, bbox_inches="tight")
    plt.close()


def get_historical_sloc(repo_url, repo_name, target_date):
    """Get SLOC count for a repository at a specific point in time.

    Args:
        repo_url (str): URL of the repository
        repo_name (str): Name of the repository
        target_date (str): Target date in YYYY-MM-DD format

    Returns:
        tuple: (total_sloc, language_sloc) or (0, {}) if no commits before target_date
    """
    repo_dir = f"./repos/{repo_name}"
    try:
        # Clone the repository with full history
        logger.info(f"Cloning {repo_name}...")
        subprocess.run(["git", "clone", repo_url, repo_dir], check=True)

        # Get the last commit on or before the target date
        logger.info(f"Finding nearest commit before or at {target_date} for {repo_name}...")

        # First check if repo existed at target date by getting the first commit
        result = subprocess.run(
            ["git", "-C", repo_dir, "rev-list", "--max-parents=0", "HEAD"], capture_output=True, text=True, check=True
        )
        first_commit = result.stdout.strip()
        logger.debug(f"First commit hash: {first_commit}")

        # Get first commit date
        result = subprocess.run(
            ["git", "-C", repo_dir, "show", "-s", "--format=%ai", first_commit],
            capture_output=True,
            text=True,
            check=True,
        )
        first_commit_date = result.stdout.strip().split()[0]  # Get just the date part
        logger.debug(f"First commit date: {first_commit_date}")

        if first_commit_date > target_date:
            logger.info(f"Repository {repo_name} was created after {target_date} (created on {first_commit_date})")
            return 0, {}

        # Get the commit hash closest to target_date
        result = subprocess.run(
            ["git", "-C", repo_dir, "rev-list", "-1", "--before", f"{target_date} 23:59:59", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        commit_hash = result.stdout.strip()
        logger.debug(f"Found commit hash: {commit_hash}")

        if not commit_hash:
            logger.info(f"No commits found before {target_date} for {repo_name}")
            return 0, {}

        # Get the actual date of the commit we'll use
        result = subprocess.run(
            ["git", "-C", repo_dir, "show", "-s", "--format=%ai", commit_hash],
            capture_output=True,
            text=True,
            check=True,
        )
        actual_date = result.stdout.strip().split()[0]  # Get just the date part
        logger.info(f"Using commit from {actual_date} for {repo_name}")

        # Checkout the repository at that commit
        subprocess.run(["git", "-C", repo_dir, "checkout", commit_hash], check=True)

        # Count SLOC at that point in time
        logger.info(f"Counting SLOC for {repo_name} at {actual_date}...")
        total_sloc, language_sloc = count_sloc(repo_dir)
        logger.info(f"Found {total_sloc} total SLOC and {len(language_sloc)} languages")
        return total_sloc, language_sloc
    except subprocess.CalledProcessError as e:
        logger.error(f"Error processing repository {repo_name} at {target_date}: {e}")
        logger.error(f"Command output: {e.output}")
        return 0, {}
    finally:
        # Cleanup
        subprocess.run(["rm", "-rf", repo_dir], check=True)


def get_repo_info(org, repo_name=None):
    """Get repository information.

    Args:
        org (str): GitHub organization name
        repo_name (str, optional): Specific repository name to analyze

    Returns:
        list: List of repository information dictionaries
    """
    if repo_name:
        url = f"https://api.github.com/repos/{org}/{repo_name}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return [response.json()]
    else:
        return get_org_repos(org)


def initialize_history(org, target_date, repo_name=None):
    """Initialize historical SLOC data for repositories at a specific date.

    Args:
        org (str): GitHub organization name
        target_date (str): Target date in YYYY-MM-DD format
        repo_name (str, optional): Specific repository name to analyze
    """
    repos = get_repo_info(org, repo_name)
    timestamp = f"{target_date} 00:00:00"

    # Ensure directories exist
    ensure_directories()

    logger.info(f"Initializing historical data for {len(repos)} repositories at {target_date}")
    for repo in repos:
        repo_name = repo["name"]
        if repo_name.lower() in IGNORE_REPOS:
            logger.info(f"Skipping ignored repository: {repo_name}")
            continue

        logger.info(f"\nProcessing {repo_name}...")
        repo_url = repo["clone_url"]
        try:
            total_sloc, language_sloc = get_historical_sloc(repo_url, repo_name, target_date)
            logger.info(f"Repository {repo_name}: {total_sloc} total SLOC, {len(language_sloc)} languages")

            # Write to historical log
            write_historical_log(timestamp, repo_name, total_sloc, language_sloc)
        except Exception as e:
            logger.error(f"Error processing repository {repo_name}: {str(e)}")
            logger.info("Continuing with next repository...")
            continue

    logger.info(f"\nHistorical data initialization complete for {target_date}")


def plot_total_sloc_trends(df):
    """Plot total SLOC trends over time for the organization and individual repositories."""
    plt.figure(figsize=(20, 12))

    # Calculate total SLOC for each timestamp
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    total_sloc_by_date = df.groupby("Timestamp")["Total SLOC"].sum()

    # Plot total SLOC trend with thicker line and distinct color
    plt.plot(
        total_sloc_by_date.index,
        total_sloc_by_date.values,
        label="Total Organization SLOC",
        linewidth=4,
        color="black",
        marker="o",
    )

    # Add value labels for total SLOC
    for x, y in zip(total_sloc_by_date.index, total_sloc_by_date.values):
        plt.text(
            x,
            y,
            f"{int(y):,}",
            ha="center",
            va="bottom",
            fontsize=8,
            color="black",
            bbox=dict(facecolor="white", alpha=0.7, edgecolor="none", pad=1),
        )

    # Plot top 20 repositories by most recent SLOC
    latest_date = df["Timestamp"].max()
    latest_data = df[df["Timestamp"] == latest_date]
    top_repos = latest_data.nlargest(20, "Total SLOC")["Repository Name"]

    # Create a colormap for the repositories
    colors = plt.cm.tab20(np.linspace(0, 1, 20))

    for idx, repo in enumerate(top_repos):
        repo_data = df[df["Repository Name"] == repo]
        plt.plot(
            repo_data["Timestamp"],
            repo_data["Total SLOC"],
            label=repo,
            linestyle="--",
            marker="o",
            color=colors[idx],
        )

        # Add value labels for each repository's data points
        for x, y in zip(repo_data["Timestamp"], repo_data["Total SLOC"]):
            plt.text(
                x,
                y,
                f"{int(y):,}",
                ha="center",
                va="bottom",
                fontsize=8,
                color=colors[idx],
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="none", pad=1),
            )

    plt.title("SLOC Trends Over Time", fontsize=14, pad=20)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Total SLOC (thousands)", fontsize=12)

    # Format y-axis in thousands
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x / 1000):,}k"))

    # Add grid
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.xticks(rotation=45)

    # Create a legend with two columns
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=10, ncol=2, title="Repositories", title_fontsize=12)

    # Adjust layout to make room for the legend
    plt.tight_layout()

    # Save the plot with the legend included
    plt.savefig(PLOT_TRENDS_FILE, bbox_inches="tight", dpi=300)
    plt.close()


def calculate_repo_activity(df):
    """Calculate repository activity based on SLOC changes in the last year.

    Args:
        df (pd.DataFrame): DataFrame containing historical SLOC data.

    Returns:
        pd.DataFrame: DataFrame with activity metrics for each repository.
    """
    # Convert timestamp to datetime if not already
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    # Check if we have multiple timestamps
    unique_timestamps = df["Timestamp"].unique()
    if len(unique_timestamps) < 2:
        msg = (
            f"Need at least 2 different timestamps to calculate activity. "
            f"Found {len(unique_timestamps)} timestamp(s): {unique_timestamps[0]}"
        )
        logger.warning(msg)
        return pd.DataFrame()

    # Calculate activity metrics for each repository
    activity_data = []
    for repo in df["Repository Name"].unique():
        repo_data = df[df["Repository Name"] == repo].sort_values("Timestamp")

        if len(repo_data) < 2:  # Need at least 2 data points to calculate change
            continue

        # Get the first and last data points
        initial_data = repo_data.iloc[0]
        final_data = repo_data.iloc[-1]

        # Calculate total change in SLOC
        initial_sloc = initial_data["Total SLOC"]
        final_sloc = final_data["Total SLOC"]
        total_change = final_sloc - initial_sloc

        # Calculate time difference in months
        months = (final_data["Timestamp"] - initial_data["Timestamp"]).days / 30.44
        avg_monthly_change = total_change / months if months > 0 else 0

        # Calculate percentage change
        percent_change = (total_change / initial_sloc * 100) if initial_sloc > 0 else 0

        activity_data.append(
            {
                "Repository Name": repo,
                "Total Change": total_change,
                "Average Monthly Change": avg_monthly_change,
                "Percent Change": percent_change,
                "Current SLOC": final_sloc,
                "Initial Date": initial_data["Timestamp"],
                "Final Date": final_data["Timestamp"],
            }
        )

    return pd.DataFrame(activity_data)


def plot_active_repos(df):
    """Plot the most active repositories based on SLOC changes in the last year."""
    plt.figure(figsize=(20, 12))

    # Calculate activity metrics
    activity_df = calculate_repo_activity(df)

    if activity_df.empty:
        logger.warning("No activity data available. Make sure you have historical data with multiple timestamps.")
        plt.close()
        return

    # Sort by absolute total change and get top 20
    activity_df["Abs Change"] = activity_df["Total Change"].abs()
    top_active = activity_df.nlargest(20, "Abs Change")

    # Create bar plot with consistent styling
    bars = plt.bar(top_active["Repository Name"], top_active["Total Change"], color=plt.cm.tab20.colors)

    # Add value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{int(height):,}",
            ha="center",
            va="bottom" if height >= 0 else "top",
            fontsize=10,
        )

    plt.title("Top 20 Most Active Repositories by SLOC Change", fontsize=14, pad=20)
    plt.xlabel("Repository", fontsize=12)
    plt.ylabel("Total SLOC Change (thousands)", fontsize=12)
    plt.xticks(rotation=45, ha="right")

    # Format y-axis in thousands
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x / 1000):,}k"))

    # Add a horizontal line at y=0
    plt.axhline(y=0, color="black", linestyle="-", alpha=0.3)

    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(PLOT_ACTIVE_FILE, bbox_inches="tight")
    plt.close()

    # Log the activity metrics for the top repositories
    logger.info("\nTop 20 Most Active Repositories:")
    for _, row in top_active.iterrows():
        logger.info(f"{row['Repository Name']}:")
        logger.info(f"  Total Change: {int(row['Total Change']):,} SLOC")
        logger.info(f"  Average Monthly Change: {int(row['Average Monthly Change']):,} SLOC")
        logger.info(f"  Percent Change: {row['Percent Change']:.1f}%")
        logger.info(f"  Current SLOC: {int(row['Current SLOC']):,}")
        logger.info(f"  Period: {row['Initial Date'].strftime('%Y-%m-%d')} to {row['Final Date'].strftime('%Y-%m-%d')}")


def main():
    """Entry point for the CLI tool."""
    parser = argparse.ArgumentParser(description="Analyze and visualize SLOC for a GitHub organization.")
    parser.add_argument("--org", default="NASA-PDS", help="GitHub organization name (default: NASA-PDS)")
    parser.add_argument("--repo", help="Specific repository name to analyze (optional)")
    parser.add_argument(
        "--token",
        default=os.getenv("GITHUB_TOKEN"),
        help="GitHub personal access token (default: GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--output", default=SLOC_REPORT_FILE, help=f"Output CSV report file (default: {SLOC_REPORT_FILE})"
    )
    parser.add_argument("--visualize", action="store_true", help="Generate visualizations from existing data")
    parser.add_argument("--update", action="store_true", help="Update SLOC data by fetching from repositories")
    parser.add_argument("--init-history", help="Initialize historical data from a specific date (format: YYYY-MM-DD)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Set logging level based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)

    global HEADERS
    if args.update or args.init_history:
        if not args.token:
            raise ValueError("GitHub token must be provided via --token or GITHUB_TOKEN env var")
        HEADERS = {"Authorization": f"token {args.token}"}

    if args.init_history:
        initialize_history(args.org, args.init_history, args.repo)
        return

    if args.update:
        os.makedirs("repos", exist_ok=True)

        # Ensure output directory exists for custom output paths
        output_dir = os.path.dirname(args.output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(args.output, mode="w", newline="") as file:
            writer = csv.writer(file)
            repos = get_repo_info(args.org, args.repo)

            all_languages = set()
            repo_language_data = []
            total_sloc_org = 0
            total_language_sloc_org = defaultdict(int)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for repo in repos:
                repo_name = repo["name"]
                if repo_name.lower() in IGNORE_REPOS:
                    continue
                repo_url = repo["clone_url"]
                logger.info(f"Cloning repository: {repo_name}")
                try:
                    repo_dir = clone_repo(repo_url, repo_name)
                    logger.info(f"Counting SLOC for repository: {repo_name}")
                    repo_sloc, language_sloc = count_sloc(repo_dir)

                    if repo_sloc is not None:
                        total_sloc_org += repo_sloc
                        for lang, sloc in language_sloc.items():
                            total_language_sloc_org[lang] += sloc
                            all_languages.add(lang)
                        repo_language_data.append((repo_name, repo_sloc, language_sloc))
                        write_historical_log(timestamp, repo_name, repo_sloc, language_sloc)
                    else:
                        repo_language_data.append((repo_name, "Error", {}))
                except Exception as e:
                    logger.error(f"Error processing repository {repo_name}: {e}")
                    repo_language_data.append((repo_name, "Error", {}))
                finally:
                    subprocess.run(["rm", "-rf", repo_dir], check=True)

            language_columns = sorted(all_languages)
            writer.writerow(["Repository Name", "Total SLOC"] + language_columns)

            for repo_name, total_sloc, language_sloc in repo_language_data:
                row = [repo_name, total_sloc] + [language_sloc.get(lang, 0) for lang in language_columns]
                writer.writerow(row)

            if not args.repo:  # Only add total row for org-wide analysis
                total_row = ["Total", total_sloc_org] + [
                    total_language_sloc_org.get(lang, 0) for lang in language_columns
                ]
                writer.writerow(total_row)

        msg = (
            f"Total SLOC for {'repository' if args.repo else 'organization'} "
            f"{args.org}/{args.repo if args.repo else ''}: {total_sloc_org}"
        )
        logger.info(msg)
        logger.info(f"Report saved to {args.output}")

    if args.visualize:
        msg = (
            f"Generating visualizations {PLOT_TOTAL_FILE}, {PLOT_LANGUAGE_FILE}, "
            f"{PLOT_TRENDS_FILE}, {PLOT_ACTIVE_FILE}..."
        )
        logger.info(msg)
        try:
            df = load_data()
            plot_total_sloc(df)
            plot_language_trends(df)

            # Try to load historical data for trends and active repos
            try:
                df_history = load_data(historical=True)
                if "Timestamp" in df_history.columns:
                    logger.info(f"Generating historical trends {PLOT_TRENDS_FILE}...")
                    plot_total_sloc_trends(df_history)
                    logger.info(f"Generating active repositories {PLOT_ACTIVE_FILE}...")
                    plot_active_repos(df_history)
                else:
                    msg = (
                        "No historical data available for trends. Run with --init-history to generate historical data."
                    )
                    logger.info(msg)
            except (FileNotFoundError, pd.errors.EmptyDataError):
                msg = "No historical data available for trends. Run with --init-history to generate historical data."
                logger.info(msg)
        except FileNotFoundError:
            logger.error(f"Error: Could not find {args.output}. Run with --update to generate the data first.")
            return
        except pd.errors.EmptyDataError:
            logger.error(f"Error: {args.output} is empty. Run with --update to generate the data first.")
            return


if __name__ == "__main__":
    main()
