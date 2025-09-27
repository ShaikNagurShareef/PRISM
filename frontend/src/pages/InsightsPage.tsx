import { useMemo, useState } from "react";
import { Box, Text, useToast, Button, Spinner, Flex } from "@chakra-ui/react";
import { useAppStore, updateSource } from "../state/appStore";
import { prismApi, exportInsightsReport, downloadMarkdownReport } from "../api/client";
import ChatMessage from "../components/ChatMessage";
import ChatInput from "../components/ChatInput";
import ChatContainer from "../components/ChatContainer";
import { FiDownload } from "react-icons/fi";

export default function InsightsPage() {
  const toast = useToast();
  const { active_source_name, sources, session_id } = useAppStore();
  const active = active_source_name ? sources[active_source_name] : null;
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const historyStr = useMemo(() => {
    if (!active?.messages) return "";
    const msgs = active.messages.slice(0, -1);
    return msgs.map((m) => `${m.role}: ${m.content}`).join("\n");
  }, [active?.messages]);

  async function send() {
    if (!active_source_name || !active) return;
    const messages = [...(active.messages ?? []), { role: "user" as const, content: input }];
    updateSource(active_source_name, { messages });
    setInput("");
    setLoading(true);
    try {
      const payload = {
        session_id,
        question: messages[messages.length - 1].content,
        history: historyStr,
        source_config: active.config,
        data_context: active.data_context,
        summary: active.summary,
      };
      const res = await prismApi.post("/invoke_insights", payload);
      const result = res.data;
      const assistant_message: any = { role: "assistant", content: result.final_insight };
      if (result.plot_path) assistant_message.plot_path = result.plot_path;
      if (result.step_log) assistant_message.step_log = result.step_log;
      updateSource(active_source_name, { messages: [...messages, assistant_message] });
    } catch (e: any) {
      toast({ status: "error", title: e?.response?.data?.detail ?? String(e) });
    } finally {
      setLoading(false);
    }
  }

  async function exportReport() {
    if (!active_source_name || !active?.messages) return;
    setExporting(true);
    try {
      const result = await exportInsightsReport(active_source_name, active.messages);
      const filename = `PRISM_Report_${active_source_name.replace(/[^a-zA-Z0-9]/g, '_')}_${new Date().toISOString().split('T')[0]}.md`;
      downloadMarkdownReport(result.report_markdown, filename);
      toast({ 
        status: "success", 
        title: "Report exported successfully!",
        description: `Downloaded as ${filename}`
      });
    } catch (e: any) {
      toast({ status: "error", title: e?.response?.data?.detail ?? String(e) });
    } finally {
      setExporting(false);
    }
  }

  if (!active_source_name) {
    return <Box><Text color="gray.400">Add and analyze a data source from the sidebar to begin.</Text></Box>;
  }

  return (
    <ChatContainer
      title={`Chat with: ${active_source_name}`}
      subtitle="Ask questions about your data and get AI-powered insights"
      icon="💬"
      showExportButton={active?.messages && active.messages.length > 0 && active.messages.some(m => m.role === "assistant")}
      onExport={exportReport}
      isExporting={exporting}
    >
      {/* Chat Messages */}
      <Box flex="1" overflowY="auto" pr={2}>
        {(active?.messages ?? []).map((m, idx) => (
          <ChatMessage
            key={idx}
            role={m.role}
            content={m.content}
            plot_path={m.plot_path}
            step_log={m.step_log}
            timestamp={new Date().toLocaleTimeString()}
          />
        ))}
      </Box>

      {/* Input Area */}
      <ChatInput
        value={input}
        onChange={setInput}
        onSend={send}
        loading={loading}
        placeholder={`Ask a question about ${active_source_name}...`}
        disabled={!active_source_name}
      />
    </ChatContainer>
  );
}
