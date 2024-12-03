import helper
import github_helper
import constants
from logger import init_logger
from function_analyzer import analyze_diff_and_functions

def create_dataset_for_repo(repo_name: str):
    repo_path = "../repositories"
    helper.empty_directory(repo_path)
    helper.remove_file("user_defined_functions.txt")
    github_helper.clone_repo_to_path(repo_name, repo_path)

    print(f"Repo for which PRs are going to be pulled: {repo_name}\n\n")
    approved_prs = github_helper.fetch_approved_PRs_from_repo(repo_name)
    diffs_comments_and_commits = github_helper.collect_diffs_comments_and_commits(approved_prs)

    helper.write_json_to_file(diffs_comments_and_commits, "../data/diffs_per_repo/" + repo_name + ".json")

        # Analyze function calls for each diff
    for item in diffs_comments_and_commits:
        function_analysis = analyze_diff_and_functions(item, repo_path)
        item['function_analysis'] = function_analysis

    helper.write_json_to_file(diffs_comments_and_commits, "../data/diffs_per_repo/" + repo_name + ".json")


if __name__ == "__main__":
    init_logger()
    repo_names = helper.get_repo_names_from_file(constants.REPO_LIST_FILENAME)
    github_helper.authenticate_github()

    create_dataset_for_repo(repo_names[210])
    create_dataset_for_repo(repo_names[211])
    create_dataset_for_repo(repo_names[237])
    create_dataset_for_repo(repo_names[240])
    create_dataset_for_repo(repo_names[244])
    create_dataset_for_repo(repo_names[251])
    create_dataset_for_repo(repo_names[255])
    create_dataset_for_repo(repo_names[258])
    create_dataset_for_repo(repo_names[267])
    create_dataset_for_repo(repo_names[271])
    create_dataset_for_repo(repo_names[719])
    create_dataset_for_repo(repo_names[720])

    # for repo_name in repo_names:
    #     create_dataset_for_repo(repo_name)