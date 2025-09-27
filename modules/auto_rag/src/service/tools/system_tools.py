import subprocess
import shlex
from pathlib import Path
from langchain_core.tools import BaseTool
from pydantic import Field, BaseModel
from typing import Type, Any
import json

from src.utils.logger import get_logger

logger = get_logger(__name__)

# --- CORRECTED ORDER: Define Input Schemas FIRST ---

class DockerfileWriterInput(BaseModel):
    content: str = Field(description="The complete, valid content of the Dockerfile.")

class DockerBuildInput(BaseModel):
    image_tag: str = Field(description="The tag for the new Docker image, e.g., 'my-rag:latest'.")

# --- NOW Define the Tools that use the schemas ---

class DockerfileWriterTool(BaseTool):
    name: str = "dockerfile_writer"
    description: str = "Writes the provided content to a Dockerfile in the designated build directory."
    # The args_schema is now more flexible
    args_schema: Type[BaseModel] = DockerfileWriterInput
    
    build_path: Path

    def _run(self, content: Any) -> str:
        """
        This method is now robust and can handle multiple input formats from the LLM.
        """
        dockerfile_content = ""
        
        # --- THIS IS THE FIX ---
        # Check if the LLM sent a dictionary {'content': '...'}
        if isinstance(content, dict) and 'content' in content:
            dockerfile_content = content['content']
        # Check if the LLM sent a JSON string '{"content": "..."}'
        elif isinstance(content, str):
            try:
                data = json.loads(content)
                if 'content' in data:
                    dockerfile_content = data['content']
                else:
                    # Assume the string itself is the content
                    dockerfile_content = content
            except json.JSONDecodeError:
                # The string is not JSON, so it must be the raw content
                dockerfile_content = content
        
        if not dockerfile_content:
            return "Error: The 'content' for the Dockerfile was empty or in an invalid format."

        try:
            if not self.build_path.exists() or not self.build_path.is_dir():
                return f"Error: Build path '{self.build_path}' is not a valid directory."
            
            # Clean the content of any escape characters the LLM might have added
            cleaned_content = dockerfile_content.encode().decode('unicode_escape')
            
            (self.build_path / "Dockerfile").write_text(cleaned_content)
            logger.info(f"Dockerfile successfully written to {self.build_path / 'Dockerfile'}")
            return f"Success: Dockerfile written to {self.build_path / 'Dockerfile'}."
        except Exception as e:
            logger.error(f"Failed to write Dockerfile: {e}")
            return f"Error: Failed to write Dockerfile. Reason: {e}"

class DockerBuildTool(BaseTool):
    name: str = "docker_image_builder"
    description: str = "Builds a Docker image from the Dockerfile in the designated build context."
    args_schema: Type[BaseModel] = DockerBuildInput

    build_path: Path

    def _run(self, image_tag: str) -> str:
        absolute_build_path = self.build_path.resolve()
        project_root = Path.cwd().resolve()

        if not absolute_build_path.is_relative_to(project_root):
             logger.error(f"Security Error: Attempted build outside of project root. Path: {absolute_build_path}")
             return f"Error: Build path must be within the project directory. Access denied for path: {self.build_path}"

        safe_build_path = shlex.quote(str(self.build_path))
        safe_image_tag = shlex.quote(image_tag)

        command = f"docker build -t {safe_image_tag} {safe_build_path}"
        logger.info(f"Executing sanitized Docker build command: {command}")

        try:
            process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            logger.info(f"Docker build successful for tag {image_tag}.")
            return f"Success: Docker image '{image_tag}' was built successfully. You can now run it using 'docker run'."
        except subprocess.CalledProcessError as e:
            logger.error(f"Docker build failed for tag {image_tag}. Error: {e.stderr}")
            return f"Error: Docker build failed. Docker error log:\n{e.stderr}"