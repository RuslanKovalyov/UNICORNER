#!/usr/bin/env python3
import subprocess
import shlex
import re
import sys

def log(message):
    print("[LOG]", message)

def request_sudo_password():
    """
    Requests the root password using 'sudo -v' to cache superuser privileges.
    """
    try:
        subprocess.run("sudo -v", shell=True, check=True)
    except subprocess.CalledProcessError:
        print("Error: Failed to obtain superuser privileges. Exiting.")
        sys.exit(1)

def run_ollama(prompt):
    """
    Sends the formatted prompt to the ollama model (phi4:14b-Q8_0)
    and returns its response.
    """
    safe_prompt = shlex.quote(prompt)
    command = f"echo {safe_prompt} | ollama run phi4:14b-Q8_0"
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout.strip()
        if result.stderr:
            log("Error (stderr): " + result.stderr.strip())
        return output
    except subprocess.CalledProcessError as e:
        log("An error occurred while executing the command:")
        log(e.stderr.strip())
        return None

def format_task_for_ai(user_input):
    """
    Formats the user's input so that the model outputs exactly one valid bash command.
    """
    formatted_prompt = (
        f"Task description: {user_input}\n"
        "Instruction: Output exactly one valid bash command that will execute the task described above. "
        "Do not output any additional text, explanation, or markdown formatting. "
        "The output should be a single line containing only the command."
    )
    return formatted_prompt

def generate_bash_command(ai_response):
    """
    Extracts the command from the model's response by removing markdown formatting if present.
    """
    if "```" in ai_response:
        matches = re.findall(r"```(?:bash)?\s*(.*?)\s*```", ai_response, re.DOTALL)
        if matches:
            return matches[0].strip()
        else:
            return ai_response.replace("```", "").strip()
    return ai_response.strip()

def capture_console_output(bash_command):
    """
    Executes the given bash command and captures its output and errors.
    """
    try:
        result = subprocess.run(
            bash_command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout.strip()
        errors = result.stderr.strip()
        return output, errors
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip()

def handle_ai_errors(console_output, console_errors):
    """
    Returns an error message if errors are detected; otherwise, returns the command output.
    """
    if console_errors:
        return f"Errors encountered: {console_errors}\nPlease check the task or the generated command."
    else:
        return console_output

def main():
    print("Welcome to the AI Agent for system management (ollama run phi4:14b-Q8_0)!")
    print("Type 'exit' to quit.")
    
    # Request root password at startup
    request_sudo_password()

    while True:
        # Step A: Get task description from the user
        user_input = input("\nEnter task description: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting program.")
            break

        # Step B: Format the prompt for the model
        formatted_prompt = format_task_for_ai(user_input)
        print("\n[Step 1] Formatted prompt for AI:")
        print(formatted_prompt)
        
        # Step C: Send the prompt to the model and get its response (expecting one command)
        print("\n[Step 2] Sending request to the ollama model...")
        ai_response = run_ollama(formatted_prompt)
        if ai_response is None:
            print("Failed to get a response from the model. Please try again.")
            continue

        print("\n[Step 3] Model response (bash command):")
        print(ai_response)

        # Extract the command from the model's response
        bash_command = generate_bash_command(ai_response)
        print("\n[Step 3.1] Extracted bash command for execution:")
        print(bash_command)

        # Step D: Execute the command and capture its output
        print("\n[Step 4] Executing the generated bash command...")
        console_output, console_errors = capture_console_output(bash_command)
        print("\nConsole output:")
        print(console_output)
        if console_errors:
            print("\nConsole errors:")
            print(console_errors)

        # Step E: Process errors and display final feedback
        final_output = handle_ai_errors(console_output, console_errors)
        print("\n[Step 5] Final result / AI feedback:")
        print(final_output)

        # Step F: Wait for next task
        print("\nWaiting for the next task...")

if __name__ == '__main__':
    main()
