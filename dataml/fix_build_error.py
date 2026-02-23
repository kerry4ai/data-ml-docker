import os
import sys
import re
import subprocess
import json

def analyze_and_fix_dockerfile_error(log_dir, github_token, repo_owner, repo_name, workspace_dir):
    log_file_path = os.path.join(log_dir, 'build', '6_Build and push image.txt')
    dockerfile_path = os.path.join(workspace_dir, 'dataml', 'Dockerfile')

    if not os.path.exists(log_file_path):
        print(f"Error: Log file not found at {log_file_path}", file=sys.stderr)
        return False, "Log file not found"

    with open(log_file_path, 'r') as f:
        log_content = f.read()

    # Pattern: Missing systemfonts/freetype2 dependencies for R packages
    systemfonts_error_match = re.search(r"ERROR: configuration failed for package ‘systemfonts’", log_content)
    fontconfig_header_error = re.search(r"fatal error: fontconfig/fontconfig.h: No such file or directory", log_content)

    if systemfonts_error_match or fontconfig_header_error:
        print("Detected missing systemfonts/freetype2 dependencies. Attempting to add apt-get install commands to Dockerfile.", file=sys.stderr)
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()

        # Define the dependencies to add and the insertion point
        dependencies_to_add = "    libfontconfig1-dev \\\n    libfreetype6-dev \\\n    libharfbuzz-dev \\\n    libfribidi-dev \\\n"
        # Adjusted pattern to correctly find the insertion point after the main 'openssh-server'
        # and ensure it's not already present.
        # This regex looks for the 'RUN apt-get install' block and specifically after 'openssh-server'.
        insertion_point_pattern = r"(RUN apt-get update && apt-get install -y --no-install-recommends \\\n(?:    [^\\]+\\\n)*?    openssh-server \\\n)"

        # Check if dependencies are already in the file to prevent duplicates
        if "libfontconfig1-dev" in dockerfile_content and \
           "libfreetype6-dev" in dockerfile_content and \
           "libharfbuzz-dev" in dockerfile_content and \
           "libfribidi-dev" in dockerfile_content:
            print("Systemfonts dependencies already present in Dockerfile. No change needed.", file=sys.stderr)
            return False, "Systemfonts dependencies already present, no fix needed"

        new_dockerfile_content = re.sub(
            insertion_point_pattern,
            lambda m: m.group(1) + dependencies_to_add,
            dockerfile_content,
            count=1 # Only replace the first occurrence
        )

        if new_dockerfile_content != dockerfile_content:
            with open(dockerfile_path, 'w') as f:
                f.write(new_dockerfile_content)
            print(f"Dockerfile updated with systemfonts/freetype2 dependencies.", file=sys.stderr)
            return True, "Dockerfile updated with systemfonts/freetype2 dependencies"
        else:
            print("Could not find appropriate insertion point for systemfonts/freetype2 dependencies in Dockerfile.", file=sys.stderr)
            return False, "Could not find insertion point for systemfonts/freetype2 dependencies"

    # Pattern: Julia version download path not found (NoSuchKey error)
    julia_download_error_match = re.search(r"NoSuchKey</Code><Message>The specified key does not exist.</Message><Key>bin/linux/x64/1.12/", log_content)

    if julia_download_error_match:
        print("Detected Julia 1.12 download path error (NoSuchKey). Attempting to fix Julia version in Dockerfile.", file=sys.stderr)
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()

        # New Julia installation block with fixed version
        new_julia_block = '''# Install Julia (fixed stable version)
ENV JULIA_MAJOR_MINOR=1.12
ENV JULIA_VERSION=1.12.5
RUN JULIA_URL_BASE="https://julialang-s3.julialang.org/bin/linux/x64/${JULIA_MAJOR_MINOR}" \\
    && echo "Installing Julia ${JULIA_VERSION}" \\
    && wget -q "${JULIA_URL_BASE}/julia-${JULIA_VERSION}-linux-x86_64.tar.gz" -O /tmp/julia.tar.gz \\
    && tar -xzf /tmp/julia.tar.gz -C /usr/local --strip-components=1 \\
    && rm /tmp/julia.tar.gz'''

        # Original problematic Julia block (dynamic version fetching)
        old_julia_block_pattern = re.compile(r'''# Install Julia \(latest stable version dynamically\)\nENV JULIA_MAJOR_MINOR=1.12\nRUN JULIA_URL_BASE="https://julialang-s3.julialang.org/bin/linux/x64/\$\{JULIA_MAJOR_MINOR\}" \\\n    && JULIA_VERSION=\$\(curl -s "\$\{JULIA_URL_BASE\}/" \| grep -oP 'julia-\\\\K\\d+\.\\d+\.\\d+\(\?=-linux-x86_64\\\\.tar\\\\.gz\)' \| sort -V \| tail -n 1\) \\\n    && echo "Installing Julia \$\{JULIA_VERSION\}" \\\n    && wget -q "\$\{JULIA_URL_BASE\}/julia-\$\{JULIA_VERSION\}-linux-x86_64.tar.gz" -O /tmp/julia.tar.gz \\\n    && tar -xzf /tmp/julia.tar.gz -C /usr/local --strip-components=1 \\\n    && rm /tmp/julia.tar.gz''')

        new_dockerfile_content = old_julia_block_pattern.sub(new_julia_block, dockerfile_content, count=1)

        if new_dockerfile_content != dockerfile_content:
            with open(dockerfile_path, 'w') as f:
                f.write(new_dockerfile_content)
            print(f"Dockerfile updated with fixed Julia version.", file=sys.stderr)
            return True, "Dockerfile updated with fixed Julia version 1.12.5"
        else:
            print("Could not find dynamic Julia installation block in Dockerfile to fix.", file=sys.stderr)
            return False, "Could not find dynamic Julia installation block"

    print("No specific auto-fixable error pattern detected in logs for Dockerfile.", file=sys.stderr)
    return False, "No auto-fixable error detected"

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python fix_build_error.py <log_dir> <github_token> <repo_owner> <repo_name> <workspace_dir>", file=sys.stderr)
        sys.exit(1)

    log_dir = sys.argv[1]
    github_token = sys.argv[2]
    repo_owner = sys.argv[3]
    repo_name = sys.argv[4]
    workspace_dir = sys.argv[5]

    fixed, message = analyze_and_fix_dockerfile_error(log_dir, github_token, repo_owner, repo_name, workspace_dir)

    if fixed:
        # Perform Git operations
        try:
            print("Performing git operations...", file=sys.stderr)
            # Ensure we are in the correct directory for git commands
            subprocess.run(['git', 'add', os.path.join(workspace_dir, 'dataml', 'Dockerfile')], check=True, cwd=os.path.join(workspace_dir, 'dataml'))
            subprocess.run(['git', 'add', os.path.join(workspace_dir, 'dataml', 'fix_build_error.py')], check=True, cwd=os.path.join(workspace_dir, 'dataml'))
            subprocess.run(['git', 'commit', '-m', f"Auto-fix: {message}"], check=True, cwd=os.path.join(workspace_dir, 'dataml'))
            subprocess.run(['git', 'push', 'origin', 'master'], check=True, cwd=os.path.join(workspace_dir, 'dataml'))
            print("Auto-fix committed and pushed successfully.", file=sys.stderr)
            print(json.dumps({"status": "fixed", "message": message})) # Output for shell script
        except subprocess.CalledProcessError as e:
            print(f"Git command failed during auto-fix: {e}", file=sys.stderr)
            print(json.dumps({"status": "error", "message": f"Git command failed: {e.stderr.decode()}"}))
    else:
        print(json.dumps({"status": "no_fix", "message": message}))