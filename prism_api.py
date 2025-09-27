# agent.py

import os
import logging
import uuid
import io
import sys
import json
import zipfile
import shutil
import subprocess
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from typing import List, Dict, Union, TypedDict, Any, Optional

import sqlite3


# --- Third-party Imports ---
from fastapi import FastAPI, HTTPException, Body, UploadFile, File, Form
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

import openai
from tavily import TavilyClient
import pandas as pd
from openpyxl import load_workbook
from xl2md import ConverterOptions, ExcelToMarkdownConverter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import sqlalchemy
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

# ==============================================================================
# 1. CONFIGURATION AND SETUP
# ==============================================================================
load_dotenv()

class Settings(BaseSettings):
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    TAVILY_API_KEY: str = Field(..., env="TAVILY_API_KEY")
    DATA_DIR: Path = Path("./data")
    PROCESSED_DIR: Path = DATA_DIR / "processed"
    PLOTS_DIR: Path = DATA_DIR / "plots"
    ARTIFACTS_DIR: Path = DATA_DIR / "artifacts"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    OPENAI_MODEL_NAME: str = "gpt-4-turbo"
    OPENAI_FAST_MODEL_NAME: str = "gpt-4o-mini"
    OPENAI_ADV_MODEL_NAME: str = "gpt-4o"
    MAX_CORRECTION_ATTEMPTS: int = 2

    class Config:
        case_sensitive = True
        env_file = ".env"

try:
    settings = Settings()
except Exception as e:
    print(f"FATAL: Could not load settings. Ensure .env file is configured. Error: {e}")
    sys.exit(1)

logging.basicConfig(level=settings.LOG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_directories():
    settings.DATA_DIR.mkdir(exist_ok=True)
    settings.PROCESSED_DIR.mkdir(exist_ok=True)
    settings.PLOTS_DIR.mkdir(exist_ok=True)
    settings.ARTIFACTS_DIR.mkdir(exist_ok=True)

# ==============================================================================
# 2. PROMPT MANAGEMENT
# ==============================================================================
_prompt_cache: Dict[str, str] = {}
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

def load_prompt(prompt_name: str) -> str:
    if prompt_name in _prompt_cache: return _prompt_cache[prompt_name]
    file_path = PROMPTS_DIR / f"{prompt_name}.txt"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        _prompt_cache[prompt_name] = prompt_content
        return prompt_content
    except Exception as e:
        raise ValueError(f"Could not load prompt '{prompt_name}': {e}")

# ==============================================================================
# 3. CORE SERVICES
# ==============================================================================
class DataAnalysisService:
    def analyze_dataset(self, file_path: Path) -> str:
        try:
            df = pd.read_csv(file_path)
            profile = "--- Dataset Profile ---\n\n"
            profile += "1. Sample Data (first 5 rows):\n"
            profile += df.head().to_string()
            profile += "\n\n"
            profile += "2. Dataframe Info:\n"
            info_buffer = io.StringIO()
            df.info(buf=info_buffer)
            profile += info_buffer.getvalue()
            profile += "\n"
            profile += "3. Summary Statistics:\n"
            profile += df.describe().to_string()
            profile += "\n\n"
            profile += "4. Column Names:\n"
            profile += ", ".join(df.columns.tolist())
            profile += "\n\n--- End of Profile ---"
            return profile
        except Exception as e:
            return f"Error analyzing dataset: {e}"

class ExcelLoaderService:
    def get_sheets(self, file_path: Union[str, Path]) -> List[str]:
        try:
            wb = load_workbook(filename=file_path, read_only=True, data_only=True)
            return [s.title for s in wb.worksheets if s.sheet_state == "visible"]
        except Exception as e:
            raise ValueError(f"Could not process Excel file '{file_path}': {e}")

class MarkdownConverterService:
    def convert(self, file_path: Union[str, Path], sheets: List[str]) -> str:
        source_path = Path(file_path)
        out_dir = settings.PROCESSED_DIR / source_path.stem
        out_dir.mkdir(exist_ok=True, parents=True)
        all_md_content = []
        for sheet_name in sheets:
            try:
                converter = ExcelToMarkdownConverter(str(source_path), ConverterOptions(out_dir=str(out_dir)))
                written_files = converter.convert(sheet_names=[sheet_name])
                if written_files:
                    md_content = Path(written_files[0]).read_text(encoding='utf-8')
                    all_md_content.append(f"--- SHEET: {sheet_name} ---\n{md_content}")
            except Exception:
                logger.exception(f"Failed to convert sheet '{sheet_name}'.")
        return "\n\n".join(all_md_content)

class DBHandlerService:
    def __init__(self, db_config: Dict[str, Any]):
        db_type = db_config.get("type")
        try:
            if db_type == "mysql":
                conn_url = URL.create(drivername="mysql+mysqlconnector", username=db_config['username'], password=db_config['password'], host=db_config['host'], port=db_config['port'], database=db_config['database'])
            elif db_type == "postgresql":
                conn_url = URL.create(drivername="postgresql+psycopg2", username=db_config['username'], password=db_config['password'], host=db_config['host'], port=db_config['port'], database=db_config['database'])
            elif db_type == "sqlite":
                conn_url = f"sqlite:///{db_config['path']}"
            else:
                raise ValueError("Unsupported DB type.")
            self.engine = create_engine(conn_url)
            with self.engine.connect() as connection:
                self.inspector = inspect(self.engine)
        except Exception as e:
            logger.error(f"Database connection failed for {db_type}: {e}")
            raise ConnectionError(f"Failed to connect to {db_type} database. Please check credentials and network. Details: {e}")

    def get_schema_as_str(self) -> str:
        schema_str = ""
        for table_name in self.inspector.get_table_names():
            schema_str += f"Table: {table_name}\nColumns:\n"
            for col in self.inspector.get_columns(table_name):
                schema_str += f"  - {col['name']} ({str(col['type'])})\n"
            schema_str += "\n"
        return schema_str

    def execute_query(self, query: str) -> pd.DataFrame:
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            return pd.DataFrame(result.fetchall(), columns=result.keys())

class CodeExecutorService:
    def run_plot_code(self, code: str) -> Dict[str, Any]:
        stdout_buffer = io.StringIO()
        try:
            with redirect_stdout(stdout_buffer):
                exec(code, {"plt": plt, "pd": pd})
            fig_nums = plt.get_fignums()
            if not fig_nums:
                return {"error": "No plot was generated by the code.", "plot_path": None}
            fig = plt.figure(fig_nums[0])
            plot_path = settings.PLOTS_DIR / f"plot_{uuid.uuid4()}.png"
            fig.savefig(plot_path)
            return {"error": None, "plot_path": str(plot_path)}
        except Exception as e:
            return {"error": str(e), "plot_path": None}
        finally:
            plt.close('all')

    def run_ml_pipeline_code(self, code: str, requirements: str, readme: str, dataset_path: Path, session_id: str) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "artifacts").mkdir()
            
            pipeline_script_path = temp_path / "pipeline.py"
            pipeline_script_path.write_text(code, encoding='utf-8')
            
            requirements_path = temp_path / "requirements.txt"
            requirements_path.write_text(requirements, encoding='utf-8')

            readme_path = temp_path / "README.md"
            readme_path.write_text(readme, encoding='utf-8')

            shutil.copy(dataset_path, temp_path / "dataset.csv")
            
            try:
                pip_command = [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)]
                install_process = subprocess.run(pip_command, cwd=temp_dir, capture_output=True, text=True, timeout=300)
                
                if install_process.returncode != 0:
                    log_output = f"--- DEPENDENCY INSTALLATION FAILED ---\n\n--- STDOUT ---\n{install_process.stdout}\n\n--- STDERR ---\n{install_process.stderr}"
                    return {"success": False, "log": log_output, "artifacts": {}}

                run_command = [sys.executable, str(pipeline_script_path)]
                run_process = subprocess.run(run_command, cwd=temp_dir, capture_output=True, text=True, timeout=600)
                
                log_output = f"--- DEPENDENCY INSTALLATION LOG ---\n{install_process.stdout}\n\n--- PIPELINE EXECUTION LOG ---\n--- STDOUT ---\n{run_process.stdout}\n\n--- STDERR ---\n{run_process.stderr}"
                
                if run_process.returncode != 0:
                    return {"success": False, "log": log_output, "artifacts": {}}

                artifacts = {}
                session_artifact_dir = settings.ARTIFACTS_DIR / session_id
                session_artifact_dir.mkdir(exist_ok=True)
                for item in (temp_path / "artifacts").iterdir():
                    dest_path = session_artifact_dir / item.name
                    shutil.copy(item, dest_path)
                    artifacts[item.name] = str(dest_path)
                return {"success": True, "log": log_output, "artifacts": artifacts}
            except Exception as e:
                return {"success": False, "log": f"An unexpected error occurred during execution: {e}", "artifacts": {}}

# ==============================================================================
# 4. AGENT DEFINITIONS
# ==============================================================================
class BaseAgent:
    def __init__(self, agent_name: str, client: openai.OpenAI, tavily_client: Optional[TavilyClient] = None):
        self.agent_name = agent_name
        self.client = client
        self.tavily_client = tavily_client
        self.system_prompt = load_prompt(agent_name)
        self.model_map = {"fast": settings.OPENAI_FAST_MODEL_NAME, "adv": settings.OPENAI_ADV_MODEL_NAME, "reasoning": settings.OPENAI_MODEL_NAME}

    def invoke(self, user_prompt: str, llm_type: str = "fast", **kwargs: Any) -> str:
        model_name = self.model_map[llm_type]
        messages = [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": user_prompt}]
        response = self.client.chat.completions.create(model=model_name, messages=messages, **kwargs)
        return response.choices[0].message.content or ""

class SummarizerAgent(BaseAgent):
    def summarize(self, context: str) -> str: return self.invoke(context, llm_type="fast")

class RouterAgent(BaseAgent):
    def route(self, question: str, context: str, history: str, source_type: str) -> Dict[str, Any]:
        prompt = (f"Source Type: '{source_type}'\n\nPrevious Conversation:\n{history}\n\nData Context Summary:\n{context}\n\nCurrent User Question:\n{question}")
        response_str = self.invoke(prompt, llm_type="fast", response_format={"type": "json_object"})
        return json.loads(response_str)

class SQLGeneratorAgent(BaseAgent):
    def generate(self, question: str, schema: str, dialect: str) -> str:
        prompt = f"User Question: {question}\nSQL Dialect: {dialect}\nSchema:\n{schema}"
        return self.invoke(prompt, llm_type="adv")

class CodeGenAgent(BaseAgent):
    def generate(self, question: str, context: str) -> str:
        prompt = f"Context:\n{context}\n\nQuestion:\n{question}\n"
        code = self.invoke(prompt, llm_type="adv")
        return code.strip().replace("```python", "").replace("```", "")

class InsightsAgent(BaseAgent):
    def generate(self, question: str, context: str, plot_info: str = "") -> str:
        prompt = f"User Question: {question}\nData Context:\n{context}\n{plot_info}"
        return self.invoke(prompt, llm_type="reasoning")

class ModelingPlannerAgent(BaseAgent):
    def plan(self, task: str, data_context: str, source_type: str, data_profile: str) -> Dict[str, Any]:
        prompt = (f"User Task: {task}\n\nData Source Type: {source_type}\n\nData Context/Schema:\n{data_context}\n\nData Profile:\n{data_profile}")
        response_str = self.invoke(prompt, llm_type="adv", response_format={"type": "json_object"})
        return json.loads(response_str)

class ModelingCodeGenAgent(BaseAgent):
    def generate(self, plan: str, data_profile: str) -> str:
        prompt = f"ML Development Plan:\n{plan}\n\nData Profile:\n{data_profile}"
        code = self.invoke(prompt, llm_type="adv")
        return code.strip().replace("```python", "").replace("```", "")

class ModelingCorrectorAgent(BaseAgent):
    def correct(self, original_code: str, error_log: str) -> str:
        prompt = f"Original Code:\n```python\n{original_code}\n```\n\nError Log:\n{error_log}"
        code = self.invoke(prompt, llm_type="adv")
        return code.strip().replace("```python", "").replace("```", "")

class DependencyAnalyzerAgent(BaseAgent):
    def analyze(self, code: str) -> str:
        return self.invoke(code, llm_type="fast")

### NEW: Report Generator Agent ###
class ReportGeneratorAgent(BaseAgent):
    def generate(self, source_name: str, chat_history: str) -> str:
        prompt = f"Source Name: {source_name}\n\nChat History:\n{chat_history}"
        return self.invoke(prompt, llm_type="reasoning")

# ==============================================================================
# 5. LANGGRAPH WORKFLOWS
# ==============================================================================
class DataInsightsState(TypedDict):
    session_id: str; question: str; history: str; data_source_config: Dict[str, Any]; data_context: str; summary: str; router_decision: Dict[str, Any]; sql_query: Optional[str]; query_result: Optional[str]; plot_code: Optional[str]; plot_path: Optional[str]; final_insight: str; error: Optional[str]; step_log: List[str]

def route_node(state: DataInsightsState):
    logger.info(f"[{state['session_id']}] Routing question...")
    state['step_log'].append(f"🤔 Routing question: '{state['question']}'")
    source_type = "database" if state['data_source_config']['type'] != 'file' else 'file'
    decision = router_agent.route(state['question'], state['summary'], state['history'], source_type)
    state['step_log'].append(f"🗺️ Router plan: SQL Required=`{decision.get('requires_sql')}`, Plot Required=`{decision.get('requires_plot')}`")
    return {"router_decision": decision, "step_log": state['step_log']}

def sql_generate_node(state: DataInsightsState):
    logger.info(f"[{state['session_id']}] Generating SQL...")
    question = state['router_decision']['contextualized_question']
    state['step_log'].append(f"✍️ Generating SQL for question: '{question}'")
    dialect = state['data_source_config'].get('type', 'sqlite')
    query = sql_generator_agent.generate(question, state['data_context'], dialect)
    return {"sql_query": query, "step_log": state['step_log']}

def sql_execute_node(state: DataInsightsState):
    logger.info(f"[{state['session_id']}] Executing SQL...")
    state['step_log'].append(f"⚙️ Executing SQL query...")
    try:
        db_handler = DBHandlerService(state['data_source_config'])
        df = db_handler.execute_query(state['sql_query'])
        return {"query_result": df.to_markdown(index=False), "step_log": state['step_log']}
    except Exception as e:
        return {"error": f"SQL Execution Failed: {e}", "step_log": state['step_log']}

def code_generate_node(state: DataInsightsState):
    logger.info(f"[{state['session_id']}] Generating plot code...")
    question = state['router_decision']['contextualized_question']
    state['step_log'].append(f"🐍 Generating Python code for visualization...")
    context = state.get('query_result') or state['data_context']
    code = code_gen_agent.generate(question, context)
    return {"plot_code": code, "step_log": state['step_log']}

def code_execute_node(state: DataInsightsState):
    logger.info(f"[{state['session_id']}] Executing plot code...")
    state['step_log'].append("🚀 Executing Python code to generate plot...")
    result = code_executor_service.run_plot_code(state['plot_code'])
    if result['error']:
        return {"error": f"Plotting Failed: {result['error']}", "step_log": state['step_log']}
    return {"plot_path": result['plot_path'], "step_log": state['step_log']}

def insights_node(state: DataInsightsState):
    logger.info(f"[{state['session_id']}] Generating final insight...")
    state['step_log'].append("💡 Generating final insight...")
    question = state['router_decision']['contextualized_question']
    context = state.get('query_result') or state['summary']
    plot_info = f"A plot is available at: {state['plot_path']}" if state.get('plot_path') else ""
    insight = insights_agent.generate(question, context, plot_info)
    return {"final_insight": insight, "step_log": state['step_log']}

def should_proceed(state: DataInsightsState):
    if state.get("error"): return END
    if state['router_decision'].get('requires_sql'): return 'sql_generate'
    if state['router_decision'].get('requires_plot'): return 'code_generate'
    return 'generate_insight'

def after_sql(state: DataInsightsState):
    if state.get("error"): return END
    if state['router_decision'].get('requires_plot'): return 'code_generate'
    return 'generate_insight'

def build_data_insights_graph():
    workflow = StateGraph(DataInsightsState)
    workflow.add_node("route", route_node)
    workflow.add_node("sql_generate", sql_generate_node)
    workflow.add_node("sql_execute", sql_execute_node)
    workflow.add_node("code_generate", code_generate_node)
    workflow.add_node("code_execute", code_execute_node)
    workflow.add_node("generate_insight", insights_node)
    workflow.set_entry_point("route")
    workflow.add_conditional_edges("route", should_proceed, {"sql_generate": "sql_generate", "code_generate": "code_generate", "generate_insight": "generate_insight", END: END})
    workflow.add_edge("sql_generate", "sql_execute")
    workflow.add_conditional_edges("sql_execute", after_sql, {"code_generate": "code_generate", "generate_insight": "generate_insight", END: END})
    workflow.add_edge("code_generate", "code_execute")
    workflow.add_edge("code_execute", "generate_insight")
    workflow.add_edge("generate_insight", END)
    return workflow.compile(checkpointer=SqliteSaver.from_conn_string("checkpoints.db"))

class PredictiveModelingState(TypedDict):
    session_id: str; task_description: str; source_config: Dict[str, Any]; data_context: str; dataset_path: str; data_profile: str; ml_plan: Dict[str, Any]; requirements_txt: str; readme_md: str; generated_code: str; execution_log: str; artifacts: Dict[str, str]; error: Optional[str]; step_log: List[str]; correction_attempts: int

def plan_pipeline_node(state: PredictiveModelingState):
    state['step_log'].append("🧠 Planning ML pipeline with research...")
    source_type = "database" if state['source_config']['type'] != 'file' else 'file'
    plan_data = modeling_planner_agent.plan(state['task_description'], state['data_context'], source_type, state.get('data_profile', ''))
    return {
        "ml_plan": plan_data,
        "requirements_txt": plan_data.get("requirements_txt", ""),
        "readme_md": plan_data.get("readme_md", ""),
        "step_log": state['step_log']
    }

def prepare_data_node(state: PredictiveModelingState):
    state['step_log'].append("📖 Preparing data for modeling pipeline...")
    config = state['source_config']
    if config['type'] != 'file':
        state['step_log'].append("...Source is a database. Executing SQL query from plan...")
        sql_query = state['ml_plan'].get('data_sql_query')
        if not sql_query:
            return {"error": "Planner Agent failed to generate the required SQL query."}
        try:
            db_handler = DBHandlerService(config)
            df = db_handler.execute_query(sql_query)
            dataset_path = settings.PROCESSED_DIR / f"{state['session_id']}_modeling_dataset.csv"
            df.to_csv(dataset_path, index=False)
            state['step_log'].append(f"...Successfully saved query results to CSV: {dataset_path}")
            return {"dataset_path": str(dataset_path), "step_log": state['step_log']}
        except Exception as e:
            return {"error": f"Failed to execute SQL and create dataset: {e}"}
    else:
        state['step_log'].append("...Source is a file. Using it directly.")
        return {"dataset_path": config['path'], "step_log": state['step_log']}

def analyze_dataset_node(state: PredictiveModelingState):
    state['step_log'].append("📊 Analyzing dataset structure and statistics...")
    profile = data_analysis_service.analyze_dataset(Path(state['dataset_path']))
    return {"data_profile": profile, "step_log": state['step_log']}

def generate_code_node(state: PredictiveModelingState):
    state['step_log'].append("✍️ Generating ML pipeline code...")
    code = modeling_code_gen_agent.generate(state['ml_plan']['plan'], state['data_profile'])
    return {"generated_code": code, "step_log": state['step_log']}

def execute_code_node(state: PredictiveModelingState):
    attempt = state.get('correction_attempts', 0)
    state['step_log'].append(f"🚀 Executing pipeline in sandbox (Attempt {attempt + 1})...")
    result = code_executor_service.run_ml_pipeline_code(state['generated_code'], state['requirements_txt'], state['readme_md'], Path(state['dataset_path']), state['session_id'])
    if not result['success']:
        state['step_log'].append(f"Execution failed. Error log captured.")
        return {"error": "ML pipeline execution failed.", "execution_log": result['log'], "step_log": state['step_log']}
    return {"execution_log": result['log'], "artifacts": result['artifacts'], "step_log": state['step_log'], "error": None}

def correct_code_node(state: PredictiveModelingState):
    state['step_log'].append(" reflector agent is correcting the code...")
    corrected_code = modeling_corrector_agent.correct(state['generated_code'], state['execution_log'])
    return {"generated_code": corrected_code, "correction_attempts": state.get('correction_attempts', 0) + 1, "step_log": state['step_log']}

def check_execution_result(state: PredictiveModelingState):
    if not state.get("error"): return "end"
    if state.get('correction_attempts', 0) >= settings.MAX_CORRECTION_ATTEMPTS: return "end_with_error"
    return "correct_code"

# --- CORRECTED: This is the new, robust workflow for the modeling agent ---
def build_predictive_modeling_graph():
    workflow = StateGraph(PredictiveModelingState)
    
    workflow.add_node("plan_pipeline", plan_pipeline_node)
    workflow.add_node("prepare_data", prepare_data_node)
    workflow.add_node("analyze_dataset", analyze_dataset_node)
    workflow.add_node("generate_code", generate_code_node)
    workflow.add_node("execute_code", execute_code_node)
    workflow.add_node("correct_code", correct_code_node)
    
    workflow.set_entry_point("plan_pipeline")
    
    # After planning, decide if we need to prepare data (for DB) or can go straight to analysis (for files)
    workflow.add_conditional_edges(
        "plan_pipeline",
        lambda state: "prepare_data" if state['source_config']['type'] != 'file' else "analyze_dataset",
        {
            "prepare_data": "prepare_data",
            "analyze_dataset": "analyze_dataset"
        }
    )
    
    # The DB path converges with the file path here
    workflow.add_edge("prepare_data", "analyze_dataset")
    
    # Continue the linear flow
    workflow.add_edge("analyze_dataset", "generate_code")
    workflow.add_edge("generate_code", "execute_code")
    
    # The self-correction loop
    workflow.add_conditional_edges("execute_code", check_execution_result, {"correct_code": "correct_code", "end": END, "end_with_error": END})
    workflow.add_edge("correct_code", "execute_code")
    
    return workflow.compile(checkpointer=SqliteSaver.from_conn_string("checkpoints.db"), interrupt_after=["generate_code"])

# ==============================================================================
# 6. FASTAPI APPLICATION
# ==============================================================================
app = FastAPI(title="PRISM Backend", description="Insights and Modeling Agent Backend")

class ProcessSourceRequest(BaseModel): source_config: Dict[str, Any]
class InsightsRequest(BaseModel): session_id: str; question: str; history: str; source_config: Dict[str, Any]; data_context: str; summary: str
class StartModelingRequest(BaseModel): session_id: str; task_description: str; source_config: Dict[str, Any]; data_context: str
class ExecuteModelingRequest(BaseModel): session_id: str
### NEW: Pydantic model for the report request ###
class ExportReportRequest(BaseModel): source_name: str; chat_history: List[Dict[str, Any]]

openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
summarizer_agent = SummarizerAgent("summarizer_agent", openai_client)
router_agent = RouterAgent("router_agent", openai_client)
sql_generator_agent = SQLGeneratorAgent("sql_generator_agent", openai_client)
code_gen_agent = CodeGenAgent("code_gen_agent", openai_client)
insights_agent = InsightsAgent("insights_agent", openai_client)
modeling_planner_agent = ModelingPlannerAgent("modeling_planner_agent", openai_client, tavily_client)
modeling_code_gen_agent = ModelingCodeGenAgent("modeling_code_gen_agent", openai_client)
modeling_corrector_agent = ModelingCorrectorAgent("modeling_corrector_agent", openai_client)
# dependency_analyzer_agent = DependencyAnalyzerAgent("dependency_analyzer_agent", openai_client)
report_generator_agent = ReportGeneratorAgent("report_generator_agent", openai_client) ### NEW ###
excel_loader_service = ExcelLoaderService()
md_converter_service = MarkdownConverterService()
code_executor_service = CodeExecutorService()
data_analysis_service = DataAnalysisService()
data_insights_graph = build_data_insights_graph()
predictive_modeling_graph = build_predictive_modeling_graph()

@app.on_event("startup")
async def startup_event(): setup_directories()

@app.post("/upload_file", tags=["Data Processing"])
async def upload_file_endpoint(session_id: str = Form(...), file: UploadFile = File(...)):
    """Accept a file from the browser and save it under data/incoming/{session_id}_{filename}."""
    try:
        incoming_dir = settings.DATA_DIR / "incoming"
        incoming_dir.mkdir(parents=True, exist_ok=True)
        safe_name = file.filename or "uploaded_file"
        save_path = incoming_dir / f"{session_id}_{safe_name}"
        with open(save_path, "wb") as f:
            f.write(await file.read())
        return {"path": str(save_path)}
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload file")


@app.post("/process_source", tags=["Data Processing"])
async def process_source(request: ProcessSourceRequest = Body(...)):
    try:
        config = request.source_config
        source_type = config.get("type")
        context = ""
        if source_type == "file":
            sheets = excel_loader_service.get_sheets(config["path"])
            context = md_converter_service.convert(config["path"], sheets)
        elif source_type in ["mysql", "postgresql", "sqlite"]:
            db_handler = DBHandlerService(config)
            context = db_handler.get_schema_as_str()
        else:
            raise HTTPException(status_code=400, detail="Invalid source type")
        summary = summarizer_agent.summarize(context)
        return {"summary": summary, "data_context": context}
    except Exception as e:
        logger.error(f"Error processing source: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/invoke_insights", tags=["Data Insights"])
async def invoke_insights_workflow(request: InsightsRequest):
    try:
        thread_config = {"configurable": {"thread_id": request.session_id}}
        initial_state = DataInsightsState(session_id=request.session_id, question=request.question, history=request.history, data_source_config=request.source_config, data_context=request.data_context, summary=request.summary, router_decision={}, sql_query=None, query_result=None, plot_code=None, plot_path=None, final_insight="", error=None, step_log=[])
        final_state = data_insights_graph.invoke(initial_state, thread_config)
        return {"final_insight": final_state.get("final_insight", ""), "plot_path": final_state.get("plot_path"), "error": final_state.get("error"), "step_log": final_state.get("step_log", [])}
    except Exception as e:
        logger.error(f"Error in insights workflow for session {request.session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start_modeling_pipeline", tags=["Predictive Modeling"])
async def start_modeling_pipeline(request: StartModelingRequest):
    try:
        thread_config = {"configurable": {"thread_id": request.session_id}}
        
        # --- CORRECTED: The initial state now only needs the file path for file sources ---
        # The graph will handle creating the dataset path for DB sources later.
        initial_dataset_path = ""
        if request.source_config.get("type") == "file":
            initial_dataset_path = request.source_config.get("path", "")

        initial_state = PredictiveModelingState(
            session_id=request.session_id, 
            task_description=request.task_description, 
            source_config=request.source_config, 
            data_context=request.data_context, 
            step_log=[], 
            dataset_path=initial_dataset_path, # Set initial path for file sources
            data_profile="", 
            ml_plan={}, 
            requirements_txt="", 
            readme_md="", 
            generated_code="", 
            execution_log="", 
            artifacts={}, 
            error=None, 
            correction_attempts=0
        )
        
        final_state = predictive_modeling_graph.invoke(initial_state, thread_config)
        
        if final_state.get("error"):
            raise HTTPException(status_code=500, detail=final_state["error"])
            
        code = final_state.get("generated_code", "")
        zip_path = settings.PROCESSED_DIR / f"{request.session_id}_pipeline.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("pipeline.py", code)
            zf.writestr("requirements.txt", final_state.get("requirements_txt", ""))
            zf.writestr("README.md", final_state.get("readme_md", ""))

        return {
            "generated_code": code,
            "requirements_txt": final_state.get("requirements_txt", ""),
            "readme_md": final_state.get("readme_md", ""),
            "step_log": final_state.get("step_log", []),
            "download_path": str(zip_path)
        }
    except Exception as e:
        logger.error(f"Error starting modeling pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute_modeling_pipeline", tags=["Predictive Modeling"])
async def execute_modeling_pipeline(request: ExecuteModelingRequest):
    try:
        thread_config = {"configurable": {"thread_id": request.session_id}}
        final_state = predictive_modeling_graph.invoke(None, thread_config)
        
        if final_state.get("error"):
            final_log = final_state.get("execution_log", "No execution log available.")
            raise HTTPException(status_code=500, detail=f"The agent failed to correct the code after multiple attempts.\n\nFINAL ERROR LOG:\n{final_log}")
            
        return {"execution_log": final_state.get("execution_log", ""), "artifacts": final_state.get("artifacts", {}), "step_log": final_state.get("step_log", [])}
    except Exception as e:
        logger.error(f"Error executing modeling pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export_insights_report", tags=["Data Insights"])
async def export_insights_report(request: ExportReportRequest):
    try:
        # The chat history now contains relative paths, which is what the agent needs
        history_str = json.dumps(request.chat_history)
        report_md = report_generator_agent.generate(request.source_name, history_str)
        return {"report_markdown": report_md}
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
# ==============================================================================
# 7. SESSION RESUME API (read-only)
# ==============================================================================
@app.get("/session/{session_id}", tags=["Session"])
async def get_session(session_id: str):
    """
    Load a previously saved PRISM session from data/prism_sessions.db as written by prism.py.
    Returns { session_id, sources, active_source_name, modeling } or 404 if not found.
    """
    try:
        db_path = Path("./data/prism_sessions.db")
        if not db_path.exists():
            raise HTTPException(status_code=404, detail="Session store not found")
        with sqlite3.connect(str(db_path)) as conn:
            cur = conn.execute("SELECT state_json FROM sessions WHERE session_id = ?", (session_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="PRISM Session ID not found")
            try:
                state = json.loads(row[0])
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Corrupted session state")
        # Ensure only expected fields are returned
        response = {
            "session_id": session_id,
            "sources": state.get("sources", {}),
            "active_source_name": state.get("active_source_name"),
            "modeling": state.get("modeling", {}),
        }
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load session")

# @app.post("/export_insights_report_pdf", tags=["Data Insights"])
# async def export_insights_report_pdf(request: ExportReportRequest):
#     # First, check if the required command-line tool is installed
#     if not shutil.which("markdown-pdf"):
#         raise HTTPException(
#             status_code=501, 
#             detail="The 'markdown-pdf' command-line tool is not installed on the server. Please run 'npm install -g markdown-pdf'."
#         )
        
#     try:
#         history_str = json.dumps(request.chat_history)
#         report_md = report_generator_agent.generate(request.source_name, history_str)

#         with tempfile.TemporaryDirectory() as temp_dir:
#             temp_path = Path(temp_dir)
#             md_path = temp_path / "report.md"
#             pdf_path = temp_path / "report.pdf"
            
#             # Write the generated markdown to a temporary file
#             md_path.write_text(report_md, encoding='utf-8')
            
#             # Run the markdown-pdf command
#             command = ["markdown-pdf", str(md_path)]
#             process = subprocess.run(command, capture_output=True, text=True, timeout=60)
            
#             if process.returncode != 0:
#                 logger.error(f"markdown-pdf failed: {process.stderr}")
#                 raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {process.stderr}")

#             if not pdf_path.exists():
#                 raise HTTPException(status_code=500, detail="PDF generation failed: Output file not found.")

#             # Read the generated PDF bytes
#             pdf_bytes = pdf_path.read_bytes()
            
#             return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={
#                 "Content-Disposition": f"attachment; filename=PRISM_Report_{request.source_name.replace(' ', '_')}.pdf"
#             })

#     except Exception as e:
#         logger.error(f"Error generating PDF report: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))