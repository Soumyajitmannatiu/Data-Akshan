from docker import errors
import docker
import os
import io
import tarfile
import time
import uuid

# --- Configuration ---
# NOW USING OUR CUSTOM BUILT IMAGE
DOCKER_IMAGE = "data-analyzer-sandbox:latest"
CODE_EXEC_TIMEOUT_SECONDS = 60
HOST_DATA_DIR = "./data"       # Directory on host where datasets are stored
HOST_OUTPUT_DIR = "./output"   # Directory on host where plots/cleaned data will be saved
CONTAINER_WORKSPACE = "/workspace" # Inside the container

# Ensure host directories exist
os.makedirs(HOST_DATA_DIR, exist_ok=True)
os.makedirs(HOST_OUTPUT_DIR, exist_ok=True)

# Initialize Docker client
client = docker.from_env()
def _normalize_container_path(path: str) -> str:
    """Ensures paths for Docker operations use forward slashes."""
    return path.replace('\\', '/')

MAX_LOG_LENGTH = 4000 

def execute_sandboxed_code(code_string: str, input_files: list | None = None, output_files_expected: list | None = None):
    """
    Executes Python code in an isolated Docker container and manages file I/O.

    Args:
        code_string (str): The Python script to run.
        input_files (list): Filenames to inject from host (default: []).
        output_files_expected (list): Filenames to retrieve from container (default: []).

    Returns:
        dict: Execution results with keys:
            - 'status_code' (int): 0 for success, non-zero for error.
            - 'stdout' (str): Standard output log (truncated).
            - 'stderr' (str): Standard error log (truncated).
            - 'files_generated' (list): Filenames successfully created inside container.
            - 'host_file_paths' (list): Absolute paths to retrieved files on host.
    """    
    if input_files is None: input_files = []
    if output_files_expected is None: output_files_expected = []

    client = docker.from_env()
    
    container_id = f"adk-sandbox-{uuid.uuid4().hex[:8]}"
    host_output_temp_dir = os.path.join(HOST_OUTPUT_DIR, container_id)
    os.makedirs(host_output_temp_dir, exist_ok=True)

    container = None
    stdout = ""
    stderr = ""
    execution_time = 0.0
    status_code = 1 
    retrieved_output_paths = []
    # NEW: A simplified list for the agent to know what worked
    verified_files = [] 

    try:
        # --- 1. PREPARATION ---
        # (Same script packaging logic as before)
        script_filename = "script.py"
        full_code = f"""
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
plt.switch_backend('Agg')
pd.set_option('display.max_rows', 50) # Prevent massive prints
pd.set_option('display.max_columns', 20)

{code_string}
"""
        script_tar_stream = io.BytesIO()
        with tarfile.open(fileobj=script_tar_stream, mode='w') as tar:
            script_data = full_code.encode('utf-8')
            tarinfo = tarfile.TarInfo(name=script_filename)
            tarinfo.size = len(script_data)
            tarinfo.mode = 0o755 
            tar.addfile(tarinfo, io.BytesIO(script_data))
        script_tar_stream.seek(0)

        # --- 2. CONTAINER STARTUP ---
        container = client.containers.run(
            DOCKER_IMAGE,
            detach=True,
            tty=False, 
            name=container_id,
            working_dir=_normalize_container_path(CONTAINER_WORKSPACE),
            command="tail -f /dev/null"
        )
        
        # Copy script
        container.put_archive(_normalize_container_path(CONTAINER_WORKSPACE), script_tar_stream.read())

        # Copy inputs
        for filename in input_files:
            host_path = os.path.join(HOST_DATA_DIR, filename)
            if os.path.exists(host_path):
                with io.BytesIO() as tar_stream:
                    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                        tar.add(host_path, arcname=filename)
                    tar_stream.seek(0)
                    container.put_archive(_normalize_container_path(CONTAINER_WORKSPACE), tar_stream.read())

        # --- 3. EXECUTION ---
        start_time = time.time()
        exec_result = container.exec_run(
            cmd=f"python {script_filename}",
            user="root",
            environment={"PYTHONUNBUFFERED": "1"},
            demux=True # Request separate streams (Tuple)
        )
        
        execution_time = round(time.time() - start_time, 2)
        status_code = exec_result.exit_code
        
        # UNPACKING LOGIC FOR DEMUX=TRUE
        # exec_result.output is now a tuple: (stdout_bytes, stderr_bytes)
        stdout_bytes, stderr_bytes = exec_result.output
        
        stdout = stdout_bytes.decode('utf-8', errors='replace') if stdout_bytes else ""
        stderr = stderr_bytes.decode('utf-8', errors='replace') if stderr_bytes else ""
        # --- 4. ARTIFACT RETRIEVAL ---
        for filename in output_files_expected:
            container_file_path = f"{CONTAINER_WORKSPACE}/{filename}" # Linux path
            host_save_path = os.path.join(host_output_temp_dir, filename)
            
            try:
                strm, stat = container.get_archive(container_file_path)
                file_obj = io.BytesIO()
                for chunk in strm: file_obj.write(chunk)
                file_obj.seek(0)

                with tarfile.open(fileobj=file_obj, mode='r') as tar:
                    members = tar.getmembers()
                    if members:
                        extracted_f = tar.extractfile(members[0])
                        if extracted_f:
                            with open(host_save_path, 'wb') as f_out:
                                f_out.write(extracted_f.read())
                            retrieved_output_paths.append(host_save_path)
                            verified_files.append(filename) # Agent friendly name
            except Exception:
                pass # File was expected but not created by the script

    except Exception as e:
        stderr = str(e)
        status_code = 1
        
    finally:
        if container:
            try:
                container.stop(timeout=2)
                container.remove()
            except: pass

    # --- 5. RESULT FORMATTING (CRITICAL FOR AGENT) ---
    
    # TRUNCATION: Protect the Context Window
    if len(stdout) > MAX_LOG_LENGTH:
        stdout = stdout[:MAX_LOG_LENGTH] + "\n...[OUTPUT TRUNCATED]..."
    if len(stderr) > MAX_LOG_LENGTH:
        stderr = stderr[:MAX_LOG_LENGTH] + "\n...[ERRORS TRUNCATED]..."

    return {
        "status_code": status_code,
        "stdout": stdout,
        "stderr": stderr,
        "execution_time": execution_time,
        # The agent uses this to know if its file generation worked:
        "files_generated": verified_files, 
        # The system uses this for the next step (path management):
        "host_file_paths": retrieved_output_paths 
    }


# --- Example Usage (for testing the tool) ---
if __name__ == "__main__":
    # 1. Create some dummy data and ensure directories exist
    if not os.path.exists(HOST_DATA_DIR): os.makedirs(HOST_DATA_DIR)
    if not os.path.exists(HOST_OUTPUT_DIR): os.makedirs(HOST_OUTPUT_DIR)

    # with open(os.path.join(HOST_DATA_DIR, "sales.csv"), "w") as f:
    #     f.write("Product,Sales\n")
    #     f.write("A,100\n")
    #     f.write("B,150\n")
    #     f.write("C,200\n")

    print("\n--- Test Case 1: Simple code execution with input/output files ---")
    code_to_run_1 = """
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

df = pd.read_csv('sales.csv')
total_sales_per_product = df.groupby('Product')['Sales'].sum().reset_index()

print("Total Sales per Product:")
print(total_sales_per_product)

# Create a simple plot
sns.barplot(x='Product', y='Sale', data=df)
plt.savefig('sales_plot_sns.png')
print("Plot saved as sales_plot_sns.png")

# Create a cleaned/processed CSV
total_sales_per_product.to_csv('total_sales.csv', index=False)
print("Processed data saved as total_sales.csv")
"""
    result_1 = execute_sandboxed_code(
        code_to_run_1,
        input_files=["sales.csv"],
        output_files_expected=["sales_plot_sns.png", "total_sales.csv"]
    )
    print("\n--- Result 1 ---")
    print(result_1)
    if result_1:
        if result_1['host_file_paths'] and result_1["stdout"]:
            print(f"Generated files for Test 1 in: {os.path.dirname(result_1['host_file_paths'][0])}")

    