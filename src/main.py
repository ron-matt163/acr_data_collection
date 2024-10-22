import helper
import github_helper
import constants

if __name__ == "__main__":
    repo_names = helper.get_repo_names_from_file(constants.REPO_LIST_FILENAME)
    github_helper.authenticate_github()
    print(f"Repo for which PRs are going to be pulled: {repo_names[20]}\n\n")
    approved_prs = github_helper.fetch_approved_PRs_from_repo(repo_names[20])
    diffs_comments_and_commits = github_helper.collect_diffs_comments_and_commits(approved_prs)
    helper.write_json_to_file(diffs_comments_and_commits, "../data/diffs_per_repo/test.json")