#!/usr/bin/env python3
import subprocess
import re
import sys
import os
import requests

# Global conversation history for maintaining context (similar to the OpenAI Chat API format)
conversation_history = []

def log(message):
    print("[LOG]", message)

def request_sudo_password():
    """
    Requests the root password via 'sudo -v' to cache superuser privileges.
    """
    try:
        subprocess.run("sudo -v", shell=True, check=True)
    except subprocess.CalledProcessError:
        print("Error: Failed to obtain superuser privileges. Exiting.")
        sys.exit(1)

def initialize_conversation():
    """
    Initializes the conversation with a system message containing detailed instructions for the model.
    The model must strictly use the following tags in its responses:
      - {Thought}: for internal reasoning (not executed)
      - {Command}: for self-contained bash commands to be executed
      - {Console}: for the real console output (stdout, stderr, return code)
    Instructions:
      1. Output only bash commands (one per line or as a single multi-line block) with no extra text.
      2. If the task requires verification (e.g., creating a directory), include a command to check the result (e.g., using ls).
      3. After each command is executed, the script will capture its real console output prefixed with {Console}:.
      4. Continue generating {Thought}: and {Command}: lines until the task is fully solved.
      5. When the task is solved, output a final line exactly as RETURN_CONTROL (with no extra characters) to indicate control should be returned.
      6. Always use environment variables (e.g., "$HOME") instead of hard-coded paths.
    """
    system_message = (
        "You are operating in a macOS console environment. Your goal is to solve tasks by generating valid, self-contained bash commands. "
        "Your responses must follow these rules exactly:\n"
        "1. Every response must consist solely of lines beginning with either {Thought}: or {Command}:.\n"
        "   - {Thought}: lines are for your internal reasoning and analysis (do not execute these).\n"
        "   - {Command}: lines contain a single self-contained bash command that will work correctly when executed independently. "
        "     If the task requires a state change (e.g., creating a directory), include a verification step (e.g., using ls to confirm creation).\n"
        "2. Do not output any extra text or tags besides {Thought}: and {Command}:. \n"
        "3. After each command is executed, the script will capture its real console output (stdout, stderr, and return code) "
        "prefixed with {Console}:. Incorporate that output into your subsequent reasoning.\n"
        "4. Continue generating {Thought}: and {Command}: lines iteratively until the task is fully solved. Do not return control until the task is complete.\n"
        "5. When the task is solved, output a final line exactly as RETURN_CONTROL (with no extra characters) to indicate that control should be returned.\n"
        "Note: Always use environment variables (e.g., \"$HOME\") instead of hard-coded paths."
    )
    conversation_history.clear()
    conversation_history.append({"role": "system", "content": system_message})
    # Debug: Print the HOME variable value
    log(f"HOME is set to: {os.environ.get('HOME', 'Not set')}")

def send_to_model():
    """
    Sends the entire conversation history to the Ollama server via the /v1/chat/completions endpoint
    and returns the model's response.
    """
    payload = {
        "model": "phi4:14b-q8_0",
        "messages": conversation_history
    }
    try:
        response = requests.post("http://localhost:11434/v1/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        assistant_reply = data["choices"][0]["message"]["content"].strip()
        conversation_history.append({"role": "assistant", "content": assistant_reply})
        return assistant_reply
    except requests.RequestException as e:
        log(f"Error contacting the Ollama server: {e}")
        return None

def extract_commands(response_text):
    """
    Extracts commands from the model's response.
    It looks for code blocks marked as ```bash ... ``` and returns each block as one command.
    If no such blocks are found, it splits the response by lines (ignoring empty lines and the RETURN_CONTROL marker).
    """
    blocks = re.findall(r"```(?:bash)?\s*(.*?)\s*```", response_text, re.DOTALL)
    if blocks:
        commands = []
        for block in blocks:
            lines = block.strip().splitlines()
            cleaned = [line for line in lines if line.strip() != "RETURN_CONTROL"]
            command_block = "\n".join(cleaned).strip()
            if command_block:
                commands.append(command_block)
        return commands
    else:
        commands = []
        for line in response_text.splitlines():
            line = line.strip()
            if line and line != "RETURN_CONTROL":
                commands.append(line)
        return commands

def run_command_realtime(bash_command):
    """
    Executes the given bash command and prints stdout and stderr in real time.
    Returns the collected stdout and stderr as strings.
    """
    process = subprocess.Popen(
        bash_command, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout_lines = []
    stderr_lines = []
    while True:
        out_line = process.stdout.readline()
        if out_line:
            print(out_line, end='')  # Print immediately
            stdout_lines.append(out_line)
        if out_line == '' and process.poll() is not None:
            break
    # Read any remaining stderr output
    err_output = process.stderr.read()
    if err_output:
        print(err_output, end='', file=sys.stderr)
        stderr_lines.append(err_output)
    output = "".join(stdout_lines)
    errors = "".join(stderr_lines)
    log(f"Command finished. STDOUT: {output!r} | STDERR: {errors!r}")
    return output, errors

def capture_console_output(bash_command):
    """
    Expands environment variables in the command:
      - First expands "~" using os.path.expanduser,
      - Then expands variables using os.path.expandvars.
    Then executes the command.
    If the command starts with 'ssh ', it is run interactively (without capturing output),
    otherwise it is run in real time.
    """
    bash_command = os.path.expanduser(bash_command)
    expanded_cmd = os.path.expandvars(bash_command)
    log(f"Executing command with expanded variables: {expanded_cmd}")
    if expanded_cmd.lstrip().startswith("ssh "):
        subprocess.run(expanded_cmd, shell=True)
        return "", ""
    else:
        return run_command_realtime(expanded_cmd)

def append_console_output(console_output, console_errors):
    """
    Forms a message with the {Console}: tag containing the command output and errors,
    and appends it to the conversation history.
    """
    content = "{Console}: " + console_output
    if console_errors:
        content += "\n{Console}: " + console_errors
    conversation_history.append({"role": "user", "content": content})
    log("Console output appended to conversation history.")

def handle_ai_errors(console_output, console_errors):
    """
    Returns a final message: if there are errors, returns them; otherwise returns the command output.
    """
    if console_errors:
        return f"Errors encountered: {console_errors}\nPlease review the output and adjust the commands if necessary."
    else:
        return console_output

def main():
    print("Welcome to the AI Agent for system management (Ollama Server on port 11434)!")
    print("Type 'exit' to quit.")
    
    request_sudo_password()
    initialize_conversation()
    
    while True:
        user_input = input("\nEnter task description: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting program.")
            break

        # Append the user task to the conversation history
        conversation_history.append({"role": "user", "content": f"Task description: {user_input}"})
        
        # Iteratively request model commands until a line exactly equal to "RETURN_CONTROL" is detected
        while True:
            print("\n[Step] Sending request to model with context...")
            model_reply = send_to_model()
            if model_reply is None:
                print("Failed to get a response from the model. Please try again.")
                break
            
            print("\n[Model Response]:")
            print(model_reply)
            
            # Check if any line in the response is exactly "RETURN_CONTROL" (ignoring whitespace)
            lines = [line.strip() for line in model_reply.splitlines()]
            if any(line == "RETURN_CONTROL" for line in lines):
                print("\nTask solved. Control returned to the user.")
                break
            
            cmds = extract_commands(model_reply)
            if not cmds:
                print("No commands were extracted from the model's response. Check the response format.")
                break
            
            for i, cmd in enumerate(cmds, start=1):
                print(f"\n[Step 3.{i}] Executing command:")
                print(cmd)
                out, err = capture_console_output(cmd)
                print("\n[Step 4] Command output:")
                result_message = handle_ai_errors(out, err)
                print(result_message)
                append_console_output(out, err)
        print("\n[Step 5] Waiting for the next task...")

if __name__ == '__main__':
    main()
