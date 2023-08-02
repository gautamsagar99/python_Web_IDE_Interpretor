from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import code
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse

app = FastAPI()

# CORS settings
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Command(BaseModel):
    command: str

session_namespaces = {}


# Mount the static files directory to serve the HTML file
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    # Serve the index.html file
    with open("static/index.html", "r") as f:
        content = f.read()
    return HTMLResponse(content)

@app.post("/execute/{session_id}")
def execute_command(session_id: str, command: Command):
    # Get or create the session's namespace
    namespace = session_namespaces.get(session_id)
    if namespace is None:
        namespace = {}
        session_namespaces[session_id] = namespace

    # Create a custom Python interpreter with the session's namespace
    interpreter = code.InteractiveInterpreter(namespace)

    # Execute the command in the session's namespace
    result = ""
    error = ""
    try:
        # Capture the output of the command
        from io import StringIO
        import sys
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()

        interpreter.runsource(command.command)

        # Get the captured output
        sys.stdout = old_stdout
        result = redirected_output.getvalue()
    except Exception as e:
        error = str(e)

    return {"result": result, "error": error}

@app.post("/execute/file/{session_id}")
async def execute_file(session_id: str, file: UploadFile = File(...)):
    # Get or create the session's namespace
    namespace = session_namespaces.get(session_id)
    if namespace is None:
        namespace = {}
        session_namespaces[session_id] = namespace

    # Read the file content
    file_content = await file.read()

    # Execute the Python code
    result = ""
    error = ""
    try:
        # Capture the output of the code
        from io import StringIO
        import sys
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()

        exec(file_content, namespace)

        # Get the captured output
        sys.stdout = old_stdout
        result = redirected_output.getvalue()
    except Exception as e:
        error = str(e)

    return {"result": result, "error": error}

