import os
import sys
import time
import random
import subprocess
from datetime import date, timedelta

# --- CONFIGURATION ---
START_DATE = date(2023, 5, 12)    # Start date for the simulated activity
END_DATE = date(2023, 8, 9)       # End date for the simulated activity
MIN_COMMITS_PER_DAY = 0           # Minimum number of commits per day
MAX_COMMITS_PER_DAY = 5           # Maximum number of commits per day (inclusive)
# --- END OF CONFIGURATION ---

def commit(commit_date, msg):
    """
    Executes a git commit command with a specified historical date using subprocess.
    """
    # Format the date into the required Git format, including a random time
    # Time is randomized between 9 AM and 5 PM for a more natural look
    time_str = f"{random.randint(9, 17):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
    t = f"{commit_date} {time_str}"
    
    # 1. Write the commit message and random content to a temporary file (.tmpfile)
    # This ensures the file content is always changed, which is necessary for Git to create a new commit
    try:
        with open(".tmpfile", "w") as f:
            f.write(msg + "\n" + os.urandom(8).hex() + "\n")
    except Exception as e:
        print(f"Error writing to .tmpfile: {e}")
        return

    # 2. Set environment variables to spoof the commit date
    env = os.environ.copy()
    # GIT_COMMITTER_DATE sets the date when the commit was created (crucial for GitHub stats)
    env["GIT_COMMITTER_DATE"] = t
    # GIT_AUTHOR_DATE sets the date when the changes were originally authored
    env["GIT_AUTHOR_DATE"] = t
    
    # 3. Execute Git commands using subprocess for better reliability and error handling
    try:
        # Git Add: Stage the temporary file
        subprocess.run(["git", "add", ".tmpfile"], 
                       check=True, 
                       stdout=subprocess.DEVNULL, # Suppress standard output
                       stderr=subprocess.DEVNULL) # Suppress standard error
        
        # Git Commit: Create the commit
        subprocess.run(["git", "commit", "-m", msg], 
                       check=True, 
                       env=env, 
                       stdout=subprocess.DEVNULL, 
                       stderr=subprocess.DEVNULL)
        
        # Small sleep to mitigate 'index.lock' errors caused by rapid commits
        time.sleep(0.01) 
        
    except subprocess.CalledProcessError as e:
        # Catches Git command failures (e.g., index.lock errors, if not suppressed)
        print(f"Git command failed for date {commit_date}: {e}")
        
        # Attempt to clean up the lock file to proceed with the next commit
        lock_path = os.path.join(".git", "index.lock")
        if os.path.exists(lock_path):
            os.remove(lock_path)
            print("Removed .git/index.lock. Attempting to proceed...")
            
    except FileNotFoundError:
        # Catches the critical error if the 'git' executable cannot be found
        print("CRITICAL ERROR: 'git' executable not found. Ensure Git is installed and in your PATH.")
        sys.exit(1) # Exit the script upon critical failure

def generate_commits(start_date, end_date):
    """
    Generates a random number of commits for each day in the specified date range.
    """
    current_date = start_date
    delta = timedelta(days=1)
    
    print(f"Starting commit generation from {start_date} to {end_date}...")

    while current_date <= end_date:
        # Determine a random number of commits for the day
        num_commits = random.randint(MIN_COMMITS_PER_DAY, MAX_COMMITS_PER_DAY)
        
        if num_commits > 0:
            print(f"--> {current_date}: Generating {num_commits} commits...")
        
        for i in range(num_commits):
            # Create a unique message for each commit
            msg = f"Simulated activity commit {i+1}/{num_commits} on {current_date}"
            commit(current_date, msg)
        
        # Move to the next day
        current_date += delta
        
    print("Generation complete. Don't forget to push your changes to the remote repository!")

if __name__ == "__main__":
    # Check if a Git repository has been initialized
    if not os.path.exists(".git"):
        print("WARNING: Current folder is not a Git repository. Initializing...")
        try:
            # Initialize the repository if it doesn't exist
            subprocess.run(["git", "init"], check=True, stdout=subprocess.DEVNULL)
            print("Git repository successfully initialized.")
        except subprocess.CalledProcessError:
            print("CRITICAL ERROR: Failed to initialize Git repository.")
            sys.exit(1)
        except FileNotFoundError:
            print("CRITICAL ERROR: 'git' executable not found during initialization. Ensure Git is in your PATH.")
            sys.exit(1)

    generate_commits(START_DATE, END_DATE)