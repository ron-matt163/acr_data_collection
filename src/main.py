import helper
import github_helper
import constants
from logger import init_logger


def create_dataset_for_repo(repo_name: str):
    print(f"Repo for which PRs are going to be pulled: {repo_name}\n\n")
    approved_prs = github_helper.fetch_approved_PRs_from_repo(repo_name)
    diffs_comments_and_commits = github_helper.collect_diffs_comments_and_commits(approved_prs)
    helper.write_json_to_file(diffs_comments_and_commits, "../data/diffs_per_repo/" + repo_name + ".json")


if __name__ == "__main__":
    init_logger()
    repo_names = helper.get_repo_names_from_file(constants.REPO_LIST_FILENAME)
    github_helper.authenticate_github()

    create_dataset_for_repo(repo_names[20])
    create_dataset_for_repo(repo_names[94])
    # for repo_name in repo_names:
    #     create_dataset_for_repo(repo_name)