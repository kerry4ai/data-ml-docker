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

    # Pattern 1: Dockerfile syntax error (e.g., from concatenated RUN commands)
    syntax_error_match = re.search(r"syntax error near unexpected token `\('", log_content)
    if syntax_error_match:
        print("Detected Dockerfile syntax error related to unexpected token '('. Attempting to fix concatenated RUN instructions.", file=sys.stderr)
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()

        problematic_block = '''RUN R -e "install.packages(c('tidyverse', 'caret', 'randomForest', 'xgboost', 'ggplot2', 'dplyr'), repos='https://cloud.r-project.org/')"\n\n# Install Julia (latest stable version dynamically)
ENV JULIA_MAJOR_MINOR=1.12
RUN JULIA_URL_BASE="https://julialang-s3.julialang.org/bin/linux/x64/${JULIA_MAJOR_MINOR}" \\
    && JULIA_VERSION=$(curl -s "${JULIA_URL_BASE}/" | grep -oP 'julia-\\K\\d+\\.\\d+\\.\\d+(?=-linux-x86_64\.tar\.gz)' | sort -V | tail -n 1) \\
    && echo "Installing Julia ${JULIA_VERSION}" \\
    && wget -q "${JULIA_URL_BASE}/julia-${JULIA_VERSION}-linux-x86_64.tar.gz" -O /tmp/julia.tar.gz \\
    && tar -xzf /tmp/julia.tar.gz -C /usr/local --strip-components=1 \\
    && rm /tmp/julia.tar.gz'''

        fixed_block = '''RUN R -e "install.packages(c('tidyverse', 'caret', 'randomForest', 'xgboost', 'ggplot2', 'dplyr'), repos='https://cloud.r-project.org/')"

# Install Julia (latest stable version dynamically)
ENV JULIA_MAJOR_MINOR=1.12
RUN JULIA_URL_BASE="https://julialang-s3.julialang.org/bin/linux/x64/${JULIA_MAJOR_MINOR}" \\
    && JULIA_VERSION=$(curl -s "${JULIA_URL_BASE}/" | grep -oP 'julia-\\K\\d+\\.\\d+\\.\\d+(?=-linux-x86_64\.tar\.gz)' | sort -V | tail -n 1) \\
    && echo "Installing Julia ${JULIA_VERSION}" \\
    && wget -q "${JULIA_URL_BASE}/julia-${JULIA_VERSION}-linux-x86_64.tar.gz" -O /tmp/julia.tar.gz \\
    && tar -xzf /tmp/julia.tar.gz -C /usr/local --strip-components=1 \\
    && rm /tmp/julia.tar.gz'''

        if problematic_block in dockerfile_content:
            new_dockerfile_content = dockerfile_content.replace(problematic_block, fixed_block)
            with open(dockerfile_path, 'w') as f:
                f.write(new_dockerfile_content)
            print(f"Dockerfile updated to split R and Julia RUN instructions.", file=sys.stderr)
            return True, "Dockerfile R/Julia RUN instructions split"
        else:
            print(f"Dockerfile syntax error detected, but specific R/Julia concatenation pattern not found in {dockerfile_path}. Manual intervention may be needed.", file=sys.stderr)
            return False, "Specific R/Julia concatenation fix not applicable"

    # Pattern 2: Missing systemfonts/freetype2 dependencies for R packages
    systemfonts_error_match = re.search(r"ERROR: configuration failed for package ‘systemfonts’", log_content)
    fontconfig_header_error = re.search(r"fatal error: fontconfig/fontconfig.h: No such file or directory", log_content)

    if systemfonts_error_match or fontconfig_header_error:
        print("Detected missing systemfonts/freetype2 dependencies. Attempting to add apt-get install commands to Dockerfile.", file=sys.stderr)
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()

        # Define the dependencies to add and the insertion point
        dependencies_to_add = "    libfontconfig1-dev \\\n    libfreetype6-dev \\\n    libharfbuzz-dev \\\n    libfribidi-dev \\\n"
        insertion_point_pattern = re.compile(r'(RUN apt-get update && apt-get install -y --no-install-recommends \\\n(?:    [^\\]+\\\n)*?    openssh-server \\\n)')

        match = insertion_point_pattern.search(dockerfile_content)
        if match:
            # Insert dependencies right after openssh-server (or similar last package)
            # and before the '&& mkdir -p /var/run/sshd' part
            # The pattern is tricky because of the trailing '\\' and newline.
            # We are inserting these dependencies at the END of the first major apt-get install block.

            # Find the line containing "openssh-server \\"
            lines = dockerfile_content.splitlines()
            new_lines = []
            fixed = False
            for line in lines:
                new_lines.append(line)
                if 'openssh-server \\' in line and not fixed:
                    # Check if the next line is "    && mkdir -p /var/run/sshd \\"
                    # If it is, insert BEFORE it. If it's another package, insert after.
                    # Given the structure, inserting directly after openssh-server is safest.
                    # Ensure it's not already there
                    if "libfontconfig1-dev" not in dockerfile_content: # Simple check to avoid double insertion
                         new_lines.append(dependencies_to_add.strip()) # Add without trailing newline for safe re-insertion
                         fixed = True
            if fixed:
                new_dockerfile_content = "\n".join(new_lines)
                with open(dockerfile_path, 'w') as f:
                    f.write(new_dockerfile_content)
                print(f"Dockerfile updated with systemfonts/freetype2 dependencies.", file=sys.stderr)
                return True, "Dockerfile updated with systemfonts/freetype2 dependencies"
            else:
                print("Could not find appropriate insertion point for systemfonts/freetype2 dependencies in Dockerfile.", file=sys.stderr)
                return False, "Could not find insertion point for systemfonts/freetype2 dependencies"
        else:
            print("Dockerfile missing expected 'RUN apt-get install' block for systemfonts/freetype2 fix.", file=sys.stderr)
            return False, "Dockerfile structure not compatible for systemfonts/freetype2 fix"


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
            subprocess.run(['git', 'add', os.path.join(workspace_dir, 'dataml', 'Dockerfile')], check=True, cwd=os.path.join(workspace_dir, 'dataml'))
            subprocess.run(['git', 'commit', '-m', f"Auto-fix: {message}"], check=True, cwd=os.path.join(workspace_dir, 'dataml'))
            # Use 'git push --set-upstream origin master' for the first push if needed
            subprocess.run(['git', 'push', '-u', 'origin', 'master'], check=True, cwd=os.path.join(workspace_dir, 'dataml'))
            print("Auto-fix committed and pushed successfully.", file=sys.stderr)
            print(json.dumps({"status": "fixed", "message": message})) # Output for shell script
        except subprocess.CalledProcessError as e:
            print(f"Git command failed during auto-fix: {e}", file=sys.stderr)
            print(json.dumps({"status": "error", "message": f"Git command failed: {e.stderr.decode()}"}))
    else:
        print(json.dumps({"status": "no_fix", "message": message}))