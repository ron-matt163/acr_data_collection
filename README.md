# Automated Code Reviewer
This repository contains code to collect additional commit-related and function-related context for code review data from PRs.

## Strategy followed for adding commit-related context:
1. For each repository in the list given in /data/Projects.xlsx, maintain a list of PRs that are approved (since these are more likely to have review comments in them).
2. Initialize Data Storage: Create a structure to hold information about code changes, comments, and commit messages.
3. Process Each Approved Pull Request: For each approved pull request, retrieve its title and prepare to gather relevant information.
4. Fetch Associated Data: Obtain the list of commits and review comments associated with the pull request. Identify the files that have been modified in the pull request.
5. Filter Relevant Files: For each modified file, check if it is of a type that is relevant to the analysis.
6. Extract Code Changes: Break down the file's changes into sections (hunks) that represent specific code modifications.
7. Analyze Each Code Change Section: For each section of code changes: Determine where the changes begin in the new version of the file. If the section is not empty, prepare to collect information about it.
8. Determine Comment Associations: Check each review comment to see if it refers to the specific section of code changes. If so, associate the comment with that section.
9. Identify Related Commit Messages: For each commit related to the pull request, check if the specific code changes are included in that commit. If they are, link the commit message to the section of code changes.
10. Store the Collected Information: Compile all gathered information (including code changes, comments, and commit messages) into a structured format for each section.
11. Return the Collected Data: After processing all approved pull requests, return the compiled information for further analysis or reporting.

## How to run the data collection script?
1. Create a ".env" file that stores your GitHub Access token:
```
GITHUB_ACCESS_TOKEN=<your token>
```
2. Install dependencies by running `pip install -r requirements.txt`. *Run this inside a virtual environment (venv) to avoid breaking dependencies in your local system.*
3. Go inside the src/ directory and run main.py (`cd src && python3 main.py`)

The list of repositories from which the data is going to be collected was obtained from https://github.com/aiopsplus/Carllm