import axios from "axios";

const prismBaseURL = import.meta.env.VITE_PRISM_BACKEND_URL || 'http://127.0.0.1:8000';
const autoragBaseURL = import.meta.env.VITE_AUTORAG_API_BASE_URL || 'http://127.0.0.1:8001';

export const prismApi = axios.create({ baseURL: prismBaseURL, timeout: 60000 });
export const autoragApi = axios.create({ baseURL: autoragBaseURL, timeout: 60000 });

export { prismBaseURL, autoragBaseURL };

export async function uploadSourceFile(sessionId: string, file: File) {
  const fd = new FormData();
  fd.append("session_id", sessionId);
  fd.append("file", file);
  const res = await prismApi.post("/upload_file", fd, { headers: { "Content-Type": "multipart/form-data" } });
  return res.data?.path as string;
}

export async function fetchSession(sessionId: string) {
  const res = await prismApi.get(`/session/${encodeURIComponent(sessionId)}`);
  return res.data as { session_id: string; sources: any; active_source_name: string | null; modeling: any };
}

export function getPlotUrl(plotPath: string): string {
  if (!plotPath) {
    console.warn('getPlotUrl: plotPath is empty');
    return '';
  }
  
  // Convert backend file path to frontend accessible URL
  // Backend path: data/plots/plot_uuid.png -> Frontend URL: /static/plots/plot_uuid.png
  const cleanPath = plotPath.replace('data/', '');
  const url = `${prismBaseURL}/static/${cleanPath}`;
  
  console.log('Plot URL Generation:', {
    originalPath: plotPath,
    cleanPath: cleanPath,
    baseURL: prismBaseURL,
    finalURL: url
  });
  
  return url;
}

export function getArtifactUrl(artifactPath: string): string {
  if (!artifactPath) return '';
  // Convert backend file path to frontend accessible URL
  // Backend path: data/artifacts/session_id/file.pkl -> Frontend URL: /static/artifacts/session_id/file.pkl
  const cleanPath = artifactPath.replace('data/', '');
  return `${prismBaseURL}/static/${cleanPath}`;
}

export function downloadFile(url: string, filename: string) {
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

export async function exportInsightsReport(sourceName: string, chatHistory: Array<{ role: string; content: string; plot_path?: string; step_log?: string[] }>) {
  const res = await prismApi.post("/export_insights_report", {
    source_name: sourceName,
    chat_history: chatHistory
  });
  return res.data;
}

export function downloadMarkdownReport(markdownContent: string, filename: string) {
  const blob = new Blob([markdownContent], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  downloadFile(url, filename);
  URL.revokeObjectURL(url);
}
