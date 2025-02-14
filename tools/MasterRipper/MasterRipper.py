import subprocess
import sys
import os
import time

# Color constants for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# ASCII Art Introduction
INTRO_ART = f"""
{Colors.OKBLUE}
___  ___          _           ______ _                       
|  \/  |         | |          | ___ (_)                      
| .  . | __ _ ___| |_ ___ _ __| |_/ /_ _ __  _ __   ___ _ __ 
| |\/| |/ _` / __| __/ _ \ '__|    /| | '_ \| '_ \ / _ \ '__|
| |  | | (_| \__ \ ||  __/ |  | |\ \| | |_) | |_) |  __/ |   
\_|  |_/\__,_|___/\__\___|_|  \_| \_|_| .__/| .__/ \___|_|   
                                      | |   | |              
                                      |_|   |_|                  
{Colors.ENDC}
"""

APP_NAME = f"{Colors.BOLD}{Colors.OKGREEN}MasterRipper.py{Colors.ENDC}"
DEVELOPER_NAME = f"{Colors.BOLD}{Colors.OKCYAN}Developed by Z3r0 S3c{Colors.ENDC}"

# Define the scripts to run in order
SCRIPTS = [
    "SQLRipper.py",
    "XSSRipper.py",
    "RCERipper.py",
    "RTRipper.py",
    "APIRipper.py"
]

# Function to execute each script
def execute_script(script_name):
    try:
        if not os.path.exists(script_name):
            print(f"{Colors.WARNING}Warning: {script_name} not found. Skipping...{Colors.ENDC}")
            return False

        print(f"{Colors.OKCYAN}Starting {script_name}...{Colors.ENDC}")
        start_time = time.time()
        
        # Run the script
        result = subprocess.run(
            [sys.executable, script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        elapsed_time = time.time() - start_time
        print(f"{Colors.OKBLUE}Execution Time for {script_name}: {elapsed_time:.2f} seconds{Colors.ENDC}")
        
        # Output logs
        if result.stdout:
            print(f"{Colors.OKGREEN}Output of {script_name}:\n{result.stdout}{Colors.ENDC}")
        if result.stderr:
            print(f"{Colors.FAIL}Errors in {script_name}:\n{result.stderr}{Colors.ENDC}")

        # Check exit status
        if result.returncode == 0:
            print(f"{Colors.OKGREEN}{script_name} completed successfully.{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.FAIL}{script_name} failed with exit code {result.returncode}.{Colors.ENDC}")
            return False
    except Exception as e:
        print(f"{Colors.FAIL}Exception occurred while running {script_name}: {e}{Colors.ENDC}")
        return False

# Main function
def main():
    print(INTRO_ART)
    print(f"{APP_NAME} - {DEVELOPER_NAME}\n")
    print(f"{Colors.BOLD}{Colors.OKCYAN}Initializing Master Ripper Suite...{Colors.ENDC}\n")

    for script in SCRIPTS:
        success = execute_script(script)
        if not success:
            print(f"{Colors.FAIL}Execution halted due to failure in {script}.{Colors.ENDC}")
            break
        else:
            print(f"{Colors.OKBLUE}Proceeding to next script...{Colors.ENDC}\n")
            time.sleep(1)  # Add a slight delay for smooth transitions

    print(f"{Colors.BOLD}{Colors.OKGREEN}All operations completed. Thank you for using MasterRipper!{Colors.ENDC}")

if __name__ == "__main__":
    main()
