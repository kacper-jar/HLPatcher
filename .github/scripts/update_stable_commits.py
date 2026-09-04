import json
import subprocess
import sys


def get_latest_commit(url, branch):
    if not branch:
        ref = "HEAD"
    else:
        ref = f"refs/heads/{branch}"

    cmd = ["git", "ls-remote", url, ref]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to run git ls-remote for {url} {ref}")
        sys.exit(1)

    output = result.stdout.strip()
    if not output:
        print(f"No output from git ls-remote for {url} {ref}")
        sys.exit(1)

    lines = output.split('\n')
    first_line = lines[0]
    hash_full = first_line.split()[0]
    return hash_full[:7]


def main():
    components_file = "data/components.json"
    with open(components_file, "r") as f:
        data = json.load(f)

    changes_made = False

    for component in data:
        component_name = component.get("name")
        component_updated = False

        for step in component.get("steps", []):
            if step.get("type") in ["git-fetcher", "goldsrc-engine-fetcher"]:
                url = step.get("url")
                branch = step.get("branch")
                current_stable = step.get("stable_commit")

                if not current_stable:
                    continue

                latest_commit = get_latest_commit(url, branch)
                if latest_commit and latest_commit != current_stable:
                    print(f"Updating {component_name}: {current_stable} -> {latest_commit}")
                    step["stable_commit"] = latest_commit
                    component_updated = True
                    changes_made = True

        if component_updated:
            with open(components_file, "w") as f:
                json.dump(data, f, indent=2)
                f.write('\n')

            subprocess.run(["git", "add", components_file])
            commit_msg = f"fix: update stable commit hash for {component_name}"
            subprocess.run(["git", "commit", "-m", commit_msg])

    if not changes_made:
        print("All components are up-to-date.")


if __name__ == "__main__":
    main()
