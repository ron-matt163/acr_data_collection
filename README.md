# Automated Code Reviewer
This repository contains code to collect additional commit-related and function-related context for code review data from PRs.

## Strategy followed for adding commit-related context:
### 1. Initialize Authentication

- Use a GitHub access token to authenticate the application, ensuring access to the required data.
- Store the authenticated session globally to reuse across API calls.

### 2. Define Project Scope

- For each repository listed in `/data/Projects.xlsx`, filter for **approved pull requests** (PRs). Approved PRs are more likely to contain valuable review comments for analysis.

### 3. Load or Fetch Approved Pull Requests

- For each repository:
  - Attempt to load previously saved data on approved PRs from a local file.
  - If no saved data is found, query the GitHub API to retrieve all **closed PRs**.
  - For each PR, check the review status. If a PR has any review with an **"APPROVED"** state, add it to the list of approved PRs.
  - Persist the list of approved PRs to a file for future retrieval, reducing redundant API calls.

### 4. Process Each Approved Pull Request

- For each approved PR, retrieve relevant details:
  - **Title**
  - **Commits**
  - **Review Comments**
  - **Modified Files**
- This data is essential for linking code changes with reviewer feedback.

### 5. Map Review Comments to Commits

- Use each review comment's `commit_id` to associate it with a specific commit.
- Store these associations in a dictionary (`commit_to_review_comment`) for easier retrieval during processing.

### 6. Extract and Process Code Changes for Relevant Files

- For each commit in the PR:
  - Identify modified files and check if each file type matches `ALLOWED_FILE_EXTENSIONS`.
  - For each relevant file, retrieve its **patch** (diff) and break it into sections representing specific code changes.
  - Analyze each code section individually to facilitate targeted analysis.

### 7. Determine Comment Associations for Each Code Change

- For each code section:
  - Calculate its starting and ending line numbers.
  - Check if any review comments associated with the commit reference this section.
  - If a review comment refers to a line within the section, add it to the code section’s metadata.

### 8. Add Commit Messages to Code Changes

- For each code section, store the **commit message** from the associated commit. 
- This provides context, linking specific changes to the rationale behind them.

### 9. Store and Return the Collected Data

- Compile all processed information, including code changes, comments, commit messages, and metadata, into a structured format.
- This data is now ready for further analysis or reporting.

### 10. Rate Limit Monitoring

- Check the GitHub API rate limit status before each API call.
  - If the rate limit is low, pause until it resets to avoid API errors.
- This step ensures continuous data collection without interruption.

## How to run the data collection script?
1. Create a ".env" file that stores your GitHub Access token:
```
GITHUB_ACCESS_TOKEN=<your token>
```
2. Install dependencies by running `pip install -r requirements.txt`. *Run this inside a virtual environment (venv) to avoid breaking dependencies in your local system.*
3. Go inside the src/ directory and run main.py (`cd src && python3 main.py`)

The list of repositories from which the data is going to be collected was obtained from https://github.com/aiopsplus/Carllm