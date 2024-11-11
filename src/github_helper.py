from github import Github, GithubException, BadCredentialsException, PullRequest, PaginatedList, PullRequestComment, Commit, PullRequestComment, Repository
# Authentication is defined via github.Auth
from github import Auth
from helper import extract_code_diffs, get_code_diff_start_line, has_allowed_extensions, extract_function_from_full_content, detect_lang_from_extension
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


def is_comment_in_code_diff(code_diff_file, comment_file, code_diff_start_line, comment_position, code_diff_end_line):
    if code_diff_file != comment_file:
        return False
    if None in (code_diff_start_line, comment_position, code_diff_end_line):
        print("None found in is_comment_in_code_diff", code_diff_start_line, comment_position, code_diff_end_line)
        if comment_position is None:
            return True
        return False

    return code_diff_start_line <= comment_position <= code_diff_end_line


def get_commits_by_ids(commits: PaginatedList.PaginatedList[Commit.Commit], commit_ids: List[str]) -> List[Commit.Commit]:
    filtered_commits = []
    for commit in commits:
        if commit.sha in commit_ids:
            filtered_commits.append(commit)

    return filtered_commits


def collect_diffs_comments_and_commits(approved_prs: List[PullRequest.PullRequest]):
    diffs_and_comments = []
    i, approved_prs_count = 0, len(approved_prs)

    for pr in approved_prs:
        monitor_rate_limit()
        i += 1
        repo = pr.base.repo
        pr_title = pr.title
        pr_number = pr.number
        # A dictionary that maps commits to the review comments made at that point.
        commit_to_review_comment = {}
        print(f"\n\nProcessing PR ({i}/{approved_prs_count}): {pr_title}")

        # Skip if there are no review comments
        review_comments = pr.get_review_comments()
        if not review_comments.totalCount:
            continue

        for review_comment in review_comments:
            commit_to_review_comment[review_comment.commit_id] = commit_to_review_comment.get(review_comment.commit_id, []) + [{"body": review_comment.body, "position": review_comment.position, "file_name": review_comment.path}]

        commits = pr.get_commits()
        diffs_and_comments.extend(process_commits_in_pr(repo, commit_to_review_comment, pr_title, pr_number, review_comments, commits))
   
    return diffs_and_comments

def process_commits_in_pr(repo: Repository.Repository, commit_to_review_comment: dict, pr_title: str, pr_number: int, review_comments: PaginatedList.PaginatedList[PullRequestComment.PullRequestComment], commits: PaginatedList.PaginatedList[Commit.Commit]):
    commits_with_review_comments = get_commits_by_ids(commits, list(commit_to_review_comment.keys()))
    diffs_and_comments = []

    for commit in commits_with_review_comments:
        for file in commit.files:
            if not has_allowed_extensions(file.filename, constants.ALLOWED_FILE_EXTENSIONS):
                continue

            patch = file.patch
            if not file.patch:
                print("PATCH IS NONE")
                return []
            
            code_diffs = extract_code_diffs(patch)
            for header, content in code_diffs:
                # Skip empty diffs
                if not content.strip():
                    continue                
        
                code_diff_info = create_code_diff_info(header, content, pr_title, pr_number, file.filename, commit.sha, commit.commit.message)
                code_diff_start_line = get_code_diff_start_line(header)
                if code_diff_start_line:
                    code_diff_end_line = code_diff_start_line + len(content.strip().split('\n')) - 1
                    code_diff_info = add_comments_to_code_diff(commit.sha, code_diff_start_line, code_diff_end_line, commit_to_review_comment, code_diff_info)
                    code_diff_info = add_function_context_to_code_diff(code_diff_info, code_diff_start_line, code_diff_end_line, repo, file.filename, detect_lang_from_extension(file.filename))
                    diffs_and_comments.append(code_diff_info)

                    print("Adding entry: ", code_diff_info)   

    return diffs_and_comments


def create_code_diff_info(header: str, content: str, pr_title: str, pr_number: int, file_name: str, commit_id: str, commit_msg: str):
    """
    Create a dictionary to store code diff information.
    """
    return {
        "pr_title": pr_title,
        "pr_number": pr_number,
        "file_name": file_name,
        "code_diff": f"{header}\n{content}",
        "comments": [],
        "commit_message": commit_msg,
        "commit_id": commit_id
    }


def add_comments_to_code_diff(commit_id: str, code_diff_start_line: int, code_diff_end_line: int, commit_to_review_comment: dict, code_diff_info: dict):
    """
    Add comments to a code diff if the comment's position matches the diff's lines.
    """
    comments_in_commit = commit_to_review_comment.get(commit_id)

    for comment in comments_in_commit:
        if is_comment_in_code_diff(code_diff_info["file_name"], comment["file_name"], code_diff_start_line, comment["position"], code_diff_end_line):
            print("Found a review comment")
            code_diff_info["comments"].append({"comment": comment["body"], "position": comment["position"]})

    return code_diff_info


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

# Fetches file content of a particular file at any given commit. The commit ID of the required 
# should be passed to the `ref` parameter
def get_file_content(repo: Repository.Repository, file_path: str, ref='main') -> str:
    """Fetch the full content of a file from the repository."""
    file_content = repo.get_contents(file_path, ref=ref)
    return file_content.decoded_content.decode('utf-8')


def add_function_context_to_code_diff(code_diff: dict, code_diff_start_line: int, code_diff_end_line: int, repo: Repository.Repository, file_path: str, language: str):
    code_diff["fn_context"] = extract_function_code(repo, file_path, code_diff["commit_id"], code_diff_start_line, code_diff_end_line, language)

    return code_diff

def extract_function_code(repo: Repository.Repository, file_path: str, commit_sha: str, code_diff_start_line: int, code_diff_end_line: int, language: str) -> List[str]:
    """
    Extract entire function code for each code diff header.

    Parameters:
    - repo: The GitHub repository object.
    - file_patch: The patch content for the modified file.
    - file_path: The path of the file in the repository.
    - code_diff_headers: A list of code diff headers indicating the start of each diff.
    - language: The programming language of the file.

    Returns:
    - A list of function codes as strings.
    """
    full_content = get_file_content(repo, file_path, commit_sha)
    function_code = ""
    
    if code_diff_start_line and code_diff_end_line:
        function_code = extract_function_from_full_content(full_content, code_diff_start_line, code_diff_end_line, language)
    
    return function_code