import { create } from "zustand";
import { persist } from "zustand/middleware";
import { AppStateShape, SourceState, ModelingState } from "../types";
import { nanoid } from "nanoid/non-secure";

const defaultModeling = {
  source_name: null as string | null,
  task: "",
  generated_code: null as string | null,
  requirements_txt: null as string | null,
  readme_md: null as string | null,
  step_log: [] as string[],
  download_path: null as string | null,
  execution_results: null as any,
};

export const useAppStore = create<AppStateShape>()(
  persist(
    (set, get) => ({
      session_id: nanoid(),
      sources: {},
      active_source_name: null,
      modeling: { ...defaultModeling },
      selected_rag_id: null,
      editing_rag_id: null,
      session_ids: {},
      chat_histories: {},
    }),
    {
      name: "prism-app-state",
      partialize: (state) => ({
        session_id: state.session_id,
        sources: state.sources,
        active_source_name: state.active_source_name,
        modeling: state.modeling,
        selected_rag_id: state.selected_rag_id,
        editing_rag_id: state.editing_rag_id,
        session_ids: state.session_ids,
        chat_histories: state.chat_histories,
      }),
    }
  )
);

export function resetState() {
  const store = useAppStore.getState();
  useAppStore.setState({
    session_id: nanoid(),
    sources: {},
    active_source_name: null,
    modeling: { ...defaultModeling },
    selected_rag_id: null,
    editing_rag_id: null,
    session_ids: {},
    chat_histories: {},
  });
}

export function setActiveSource(name: string | null) {
  useAppStore.setState({ active_source_name: name });
}

export function updateSource(name: string, data: Partial<SourceState>) {
  const { sources } = useAppStore.getState();
  useAppStore.setState({ sources: { ...sources, [name]: { ...sources[name], ...data } } });
}

export function setModeling(data: Partial<ModelingState>) {
  const { modeling } = useAppStore.getState();
  useAppStore.setState({ modeling: { ...modeling, ...data } });
}
