from github import Github, GithubException, BadCredentialsException, PullRequest
# Authentication is defined via github.Auth
from github import Auth
from helper import extract_hunks, get_hunk_start_line
import constants
import os
from dotenv import load_dotenv
from typing import List

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

    pulls = repo.get_pulls(state='closed')  # Only closed PRs can be approved
    approved_prs = []
    print("No. of closed PRs in the repo: ", pulls.totalCount)

    for pr in pulls:
        reviews = pr.get_reviews()
        if reviews.totalCount > 0:
            for review in reviews:
                if review.state == "APPROVED":
                    approved_prs.append(pr)
                    print("Approved PR found: ", len(approved_prs))
                    break
            
    return approved_prs


def collect_diffs_comments_and_commits(approved_prs: List[PullRequest.PullRequest]):
    diffs_and_comments = []
    
    for pr in approved_prs:
        pr_title = pr.title
        print(f"\n\nProcessing PR: {pr_title}")

        review_comments = pr.get_review_comments()
        if review_comments.totalCount == 0:
            continue
        commits = pr.get_commits()
        files = pr.get_files()

        for file in files:
            if any(file.filename.endswith(ext) for ext in constants.ALLOWED_FILE_EXTENSIONS):
                patch = file.patch
                hunks = extract_hunks(patch)

                for header, content in hunks:
                    hunk_start_line = get_hunk_start_line(header)

                    # Skip empty content
                    if not content.strip():
                        continue
                    
                    hunk_info = {
                        "pr_title": pr_title,
                        "file_name": file.filename,
                        "hunk": f"{header}\n{content}",  # Include both header and content
                        "comments": [],
                        "commit_messages": []
                    }

                    if hunk_start_line:
                        # Calculate the ending line number based on the content
                        hunk_lines_length = len(content.split('\n'))
                        hunk_end_line = hunk_start_line + hunk_lines_length - 1

                        for comment in review_comments:
                            if (comment.path == file.filename and
                                hunk_start_line <= comment.position <= hunk_end_line):
                                # we could remove comment.position later after verifying that no errors are occurring
                                hunk_info["comments"].append({
                                    "comment": comment.body,
                                    "position": comment.position
                                })

                    for commit in commits:
                        commit_files = commit.files
                        for commit_file in commit_files:
                            if commit_file.filename == file.filename:
                                # More robust presence check can be implemented here, i.e, adding the commit message only it the code diff was made in its corresponding commit
                                if content.strip() in commit_file.patch:
                                    hunk_info["commit_messages"].append(commit.commit.message)

                    diffs_and_comments.append(hunk_info)
    
    return diffs_and_comments