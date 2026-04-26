import subprocess
import sys

def run_lint():
    print("Running flake8...")
    # Make sure flake8 is installed
    subprocess.run([sys.executable, "-m", "pip", "install", "flake8", "pytest"], capture_output=True)
    
    result = subprocess.run(
        [sys.executable, "-m", "flake8", ".", "--select=E9,F63,F7,F82", "--show-source"],
        capture_output=True,
        text=True
    )
    print("=== FLAKE8 STDOUT ===")
    print(result.stdout)
    print("=== FLAKE8 STDERR ===")
    print(result.stderr)

if __name__ == "__main__":
    run_lint()
