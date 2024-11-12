import helper
import github_helper
import constants
from logger import init_logger
from function_analyzer import analyze_diff_and_functions

def create_dataset_for_repo(repo_name: str):
    print(f"Repo for which PRs are going to be pulled: {repo_name}\n\n")
    approved_prs = github_helper.fetch_approved_PRs_from_repo(repo_name)
    diffs_comments_and_commits = github_helper.collect_diffs_comments_and_commits(approved_prs)

    repo_path = "/Users/salonishah/Documents/Sem 3 - Fall 2024/GenAI/Project/Airtest-master"

        # Analyze function calls for each diff
    for item in diffs_comments_and_commits:
        function_analysis = analyze_diff_and_functions(item, repo_path)
        item['function_analysis'] = function_analysis

    helper.write_json_to_file(diffs_comments_and_commits, "../data/diffs_per_repo/" + repo_name + ".json")


if __name__ == "__main__":
    init_logger()
    repo_names = helper.get_repo_names_from_file(constants.REPO_LIST_FILENAME)
    github_helper.authenticate_github()

    create_dataset_for_repo(repo_names[10])
    # for repo_name in repo_names:
    #     create_dataset_for_repo(repo_name)