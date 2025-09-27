export type SourceConfig =
  | { type: "file"; path: string }
  | { type: "sqlite"; path: string }
  | {
      type: "postgresql" | "mysql";
      host: string;
      port: number;
      username: string;
      password: string;
      database: string;
    };

export interface SourceState {
  config: SourceConfig;
  analyzed: boolean;
  summary?: string;
  data_context?: any;
  messages?: Array<{ role: "user" | "assistant"; content: string; plot_path?: string; step_log?: string[] }>;
}

export interface ModelingState {
  source_name: string | null;
  task: string;
  generated_code?: string | null;
  requirements_txt?: string | null;
  readme_md?: string | null;
  step_log?: string[];
  download_path?: string | null;
  execution_results?: any;
}

export interface AppStateShape {
  session_id: string;
  sources: Record<string, SourceState>;
  active_source_name: string | null;
  modeling: ModelingState;
  // AutoRAG
  selected_rag_id?: string | null;
  editing_rag_id?: string | null;
  session_ids?: Record<string, string | null>; // ragId -> sessionId
  chat_histories?: Record<string, Array<{ role: string; content: string; sources?: any[] }>>;
}
