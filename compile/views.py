from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect, render
from django.contrib import messages
from .models import CodeSubmission 
from django.conf import settings
import os
import uuid
import subprocess
from pathlib import Path
from django.contrib.auth.decorators import login_required
# from django.views.decorators.clickjacking import xframe_options_exempt

@login_required
def submit_compile(request):
    if request.method == "POST":
        # Manually fetch form data
        form = CodeSubmission(request.POST)
        language = request.POST.get("language")
        code = request.POST.get("code")
        input_data = request.POST.get("input_data")

        

        # Simple validation (can add more)
        if not language or not code:
            messages.info(request, "Language and code are required fields.")
            return redirect("/compile/")  # Or wherever your form page is

        # Save submission to DB
        submission = CodeSubmission(
            language=language,
            code=code,
            input_data=input_data,
        )
        submission.save()

        # Run the code and save output
        output = run_code(language, code, input_data)
        submission.output_data = output
        submission.save()

        return render(request, "result.html", {"submission": submission})
    selected_language = request.GET.get('lang', 'py') 
    # If GET request
    form = CodeSubmission()
    
    return render(request, "index.html", {"form": form,"selected_language": selected_language}) 



def run_code(language, code, input_data):
    project_path = Path(settings.BASE_DIR)
    directories = ["codes", "inputs", "outputs"]

    # Make sure the necessary directories exist
    for directory in directories:
        dir_path = project_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)

    codes_dir = project_path / "codes"
    inputs_dir = project_path / "inputs"
    outputs_dir = project_path / "outputs"

    unique = str(uuid.uuid4())

    code_file_name = f"{unique}.{language}"
    input_file_name = f"{unique}.txt"
    output_file_name = f"{unique}.txt"

    code_file_path = codes_dir / code_file_name
    input_file_path = inputs_dir / input_file_name
    output_file_path = outputs_dir / output_file_name

    # Save the code to file
    with open(code_file_path, "w") as code_file:
        code_file.write(code)

    # Normalize input line endings
    input_data = (input_data or "").replace("\r\n", "\n")

    with open(input_file_path, "w") as input_file:
        input_file.write(input_data)

    # Debug input content
    with open(input_file_path, "r") as f:
        print("DEBUG: Input file content -->", repr(f.read()))

    with open(output_file_path, "w") as output_file:
        pass  # Create an empty output file

    output_data = ""
    error_data = ""

    if language == "cpp":
        executable_path = codes_dir / unique
        # Compile
        compile_result = subprocess.run(
            ["g++", str(code_file_path), "-o", str(executable_path)],
            capture_output=True, text=True
        )
        if compile_result.returncode != 0:
            # Compilation failed — return compiler error
            error_data = compile_result.stderr
        else:
            # Run the program
            run_result = subprocess.run(
                [str(executable_path)],
                stdin=open(input_file_path, "r"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            output_data = run_result.stdout
            error_data = run_result.stderr

    elif language == "py":
        run_result = subprocess.run(
            ["python", str(code_file_path)],
            stdin=open(input_file_path, "r"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        output_data = run_result.stdout
        error_data = run_result.stderr

    # Combine output and error
    final_output = output_data
    if error_data:
        final_output += "\nErrors:\n" + error_data

    print("DEBUG: Final Output -->", final_output)
    return final_output
