from github import Github, GithubException, BadCredentialsException, PullRequest, File, PaginatedList, PullRequestComment, Commit
# Authentication is defined via github.Auth
from github import Auth
from helper import extract_code_diffs, get_code_diff_start_line
import constants
import os
from dotenv import load_dotenv
import pickle
from typing import List
from logger import logger
import time

auth = None
user = None

def authenticate_github():
    global user, auth
    try:
        # Load environment variables from .env file
        load_dotenv()
        access_token = os.getenv("GITHUB_ACCESS_TOKEN")
        if not access_token:
            raise ValueError("GitHub access token not found. Please set GITHUB_ACCESS_TOKEN in the environment.")

        # Authenticate using the access token
        auth = Github(access_token)
        user = auth.get_user()  # Test if the token is valid
        print(f"Authenticated as: {user.login}")
        
    except ValueError as ve:
        print(f"Error: {ve}")
    except BadCredentialsException:
        print("Error: Invalid GitHub access token. Please check the token and try again.")
    except GithubException as ge:
        print(f"GitHub API error: {ge.data['message']}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")


def fetch_approved_PRs_from_repo(repo_name: str):
    if auth:
        repo = auth.get_repo(repo_name)
    else:
        print("auth is None")
        return None
    
    try:
        with open(f"../saved_objs/{repo_name}/approved_prs.pkl", 'rb') as f:
            approved_prs = pickle.load(f)
            print("Loaded approved PRs from file.")
            return approved_prs
    except FileNotFoundError as fe:
        print("Approved PRs pickle not found: ", str(fe))
        approved_prs = []

    pulls = repo.get_pulls(state='closed')  # Only closed PRs can be approved
    approved_prs = []
    print("No. of closed PRs in the repo: ", pulls.totalCount)

    for pr in pulls:
        monitor_rate_limit()
        reviews = pr.get_reviews()
        if reviews.totalCount > 0:
            for review in reviews:
                if review.state == "APPROVED":
                    approved_prs.append(pr)
                    print("Approved PR found: ", len(approved_prs))
                    break

    os.makedirs(f"../saved_objs/{repo_name}", exist_ok=True)
    with open(f"../saved_objs/{repo_name}/approved_prs.pkl", 'wb') as f:
        pickle.dump(approved_prs, f)
        print("Saved approved PRs to file.")            

    return approved_prs


def is_comment_in_code_diff(code_diff_start_line, comment_position, code_diff_end_line):
    if None in (code_diff_start_line, comment_position, code_diff_end_line):
        print("None found in is_comment_in_code_diff", code_diff_start_line, comment_position, code_diff_end_line)
        if comment_position is not None:
            return True
        return False

    return code_diff_start_line <= comment_position <= code_diff_end_line


def collect_diffs_comments_and_commits(approved_prs: List[PullRequest.PullRequest]):
    diffs_and_comments = []
    i, approved_prs_count = 0, len(approved_prs)

    for pr in approved_prs:
        monitor_rate_limit()
        i += 1
        pr_title = pr.title
        pr_number = pr.number
        print(f"\n\nProcessing PR ({i}/{approved_prs_count}): {pr_title}")

        # Skip if there are no review comments
        review_comments = pr.get_review_comments()
        if not review_comments.totalCount:
            continue

        commits = pr.get_commits()
        files = pr.get_files()

        for file in files:
            if any(file.filename.endswith(ext) for ext in constants.ALLOWED_FILE_EXTENSIONS):
                diffs_and_comments.extend(process_file_in_pr(file, pr_title, pr_number, review_comments, commits))
    
    return diffs_and_comments


def process_file_in_pr(file: File.File, pr_title: str, pr_number: int, review_comments: PaginatedList.PaginatedList[PullRequestComment.PullRequestComment], commits: PaginatedList.PaginatedList[Commit.Commit]):
    """
    Process a single file in the PR: extract code diffs, handle comments, and match commit messages.
    """
    diffs_and_comments = []
    patch = file.patch
    if not patch:
        print("PATCH IS NONE")
        return []

    code_diffs = extract_code_diffs(patch)
    for header, content in code_diffs:
        # Skip empty diffs
        if not content.strip():
            continue
        
        code_diff_info = create_code_diff_info(header, content, pr_title, pr_number, file.filename)

        # Handle review comments
        code_diff_start_line = get_code_diff_start_line(header)
        if code_diff_start_line:
            code_diff_end_line = code_diff_start_line + len(content.strip().split('\n')) - 1
            add_comments_to_code_diff(review_comments, code_diff_start_line, code_diff_end_line, code_diff_info, file.filename)

        # Handle commits
        last_commit_sha = add_commits_to_code_diff(commits, content, file.filename, code_diff_info)
        code_diff_info["last_commit_sha"] = last_commit_sha

        diffs_and_comments.append(code_diff_info)
        print("\n\nAdded code diff:\n", code_diff_info)

    return diffs_and_comments


def create_code_diff_info(header: str, content: str, pr_title: str, pr_number: int, file_name: str):
    """
    Create a dictionary to store code diff information.
    """
    return {
        "pr_title": pr_title,
        "pr_number": pr_number,
        "file_name": file_name,
        "code_diff": f"{header}\n{content}",
        "comments": [],
        "commit_messages": [],
    }


def add_comments_to_code_diff(review_comments: PaginatedList.PaginatedList[PullRequestComment.PullRequestComment], code_diff_start_line: int, code_diff_end_line: int, code_diff_info: dict, file_name: str):
    """
    Add comments to a code diff if the comment's position matches the diff's lines.
    """
    for comment in review_comments:
        if (comment.path == file_name and is_comment_in_code_diff(code_diff_start_line, comment.position, code_diff_end_line)):
            print("\n\n\nREVIEW COMMENT FOUND!!!")
            code_diff_info["comments"].append({
                "comment": comment.body,
                "position": comment.position
            })

def monitor_rate_limit():
    global auth
    # Get the current rate limit status for core API requests
    rate_limit = auth.get_rate_limit().core
    
    if rate_limit.remaining < 100:
        # If rate limit is exceeded, calculate time until reset
        reset_time = rate_limit.reset.timestamp() - time.time()
        print(f"Rate limit exceeded. Sleeping for {reset_time} seconds.")
        
        # Sleep until the rate limit is reset
        if reset_time >= 0:
            time.sleep(reset_time)
        else:
            while reset_time < 0:
                print("Negative reset time. Waiting for the rate limit to get reset.")
                time.sleep(10)
                rate_limit = auth.get_rate_limit().core
                reset_time = rate_limit.reset.timestamp() - time.time()

    else:
        print(f"Rate limit OK. Remaining requests: {rate_limit.remaining}")


def add_commits_to_code_diff(commits: PaginatedList.PaginatedList[Commit.Commit], content: str, file_name: str, code_diff_info: dict):
    """
    Add commit messages to a code diff if the commit affects the diff.
    """
    last_commit_sha = None
    for commit in commits:
        last_commit_sha = commit.sha
        commit_files = commit.files
        for commit_file in commit_files:
            if commit_file.filename == file_name:
                if commit_file.patch and (commit_file.patch in content.strip() or content.strip() in commit_file.patch):
                    print("\n\nMatch between content and commit patch IS found")
                    code_diff_info["commit_messages"].append(commit.commit.message)
                else:
                    print("\n\nMatch between content and commit patch NOT found")
                    logger.debug(f"\nCommit file patch: {commit_file.patch}\ncontent.strip: {content.strip()}")
    return last_commit_sha