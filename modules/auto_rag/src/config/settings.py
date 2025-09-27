import yaml
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field

# Define models for capabilities loaded from YAML
class LLMConfig(BaseModel):
    model_name: str
    provider: str
    max_tokens: int

class EmbeddingConfig(BaseModel):
    model_name: str
    provider: str
    dimensions: int
    class_path: str

class ChunkerConfig(BaseModel):
    name: str
    class_path: str

class VectorStoreConfig(BaseModel):
    class_path: str

class Capabilities(BaseModel):
    available_llms: dict[str, dict[str, LLMConfig]]
    available_embedders: dict[str, dict[str, EmbeddingConfig]]
    available_vector_stores: dict[str, VectorStoreConfig]
    available_chunkers: dict[str, ChunkerConfig]

# Function to load YAML capabilities
def load_capabilities() -> Capabilities:
    config_dir = Path(__file__).parent / "yml"
    
    llm_data = yaml.safe_load((config_dir / "llm.yml").read_text())
    embed_data = yaml.safe_load((config_dir / "embedding.yml").read_text())
    vs_data = yaml.safe_load((config_dir / "vector_store.yml").read_text())
    chunker_data = yaml.safe_load((config_dir / "chunker.yml").read_text())

    return Capabilities(
        available_llms=llm_data.get("available_llms", {}),
        available_embedders=embed_data.get("available_embedders", {}),
        available_vector_stores=vs_data.get("available_vector_stores", {}),
        available_chunkers=chunker_data.get("available_chunkers", {})
    )

# Main Application Settings
class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # Core Settings
    APP_NAME: str = "AutoRAG Platform"
    ENVIRONMENT: str = "development"
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./autorag_data.db"
    
    # API Keys (loaded from .env)
    OPENAI_API_KEY: str = Field(default="", validation_alias="OPENAI_API_KEY")
    GOOGLE_API_KEY: str = Field(default="", validation_alias="GOOGLE_API_KEY")
    GROQ_API_KEY: str = Field(default="", validation_alias="GROQ_API_KEY")
    
    # Capabilities (Loaded dynamically)
    CAPABILITIES: Capabilities = Field(default_factory=load_capabilities)

# Instantiate settings object
settings = AppSettings()