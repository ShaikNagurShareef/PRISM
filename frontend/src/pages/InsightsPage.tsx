import { useMemo, useState } from "react";
import { Box, Button, Flex, Heading, Image, Spinner, Text, Textarea, useToast, Accordion, AccordionItem, AccordionButton, AccordionPanel, AccordionIcon, VStack } from "@chakra-ui/react";
import { useAppStore, updateSource } from "../state/appStore";
import { prismApi, getPlotUrl, exportInsightsReport, downloadMarkdownReport } from "../api/client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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
      const filename = `${active_source_name}_insights_report_${new Date().toISOString().split('T')[0]}.md`;
      downloadMarkdownReport(result.report_markdown, filename);
      toast({ status: "success", title: "Report exported successfully!" });
    } catch (e: any) {
      toast({ status: "error", title: e?.response?.data?.detail ?? "Export failed" });
    } finally {
      setExporting(false);
    }
  }

  if (!active_source_name) {
    return <Box><Text color="gray.400">Add and analyze a data source from the sidebar to begin.</Text></Box>;
  }

  return (
    <Flex direction="column" gap={6} h="full">
      {/* Header */}
      <Box 
        bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
        borderRadius="xl"
        p={6}
        border="1px solid"
        borderColor="whiteAlpha.200"
        backdropFilter="blur(20px)"
        boxShadow="0 4px 16px rgba(0,0,0,0.1)"
      >
        <Flex justifyContent="space-between" alignItems="center" mb={2}>
          <Heading size="lg" color="white" fontWeight="bold">
            💬 Chat with: {active_source_name}
          </Heading>
          {active?.messages && active.messages.length > 0 && active.messages.some(m => m.role === "assistant") && (
            <Button
              onClick={exportReport}
              isLoading={exporting}
              loadingText="Exporting..."
              size="sm"
              variant="outline"
              color="white"
              borderColor="whiteAlpha.300"
              _hover={{
                bg: "whiteAlpha.100",
                borderColor: "whiteAlpha.400",
                transform: "translateY(-1px)"
              }}
              _active={{
                transform: "translateY(0px)"
              }}
              transition="all 0.2s ease"
            >
              📄 Export Report
            </Button>
          )}
        </Flex>
        <Text color="whiteAlpha.700" fontSize="sm" fontWeight="medium">
          Ask questions about your data and get AI-powered insights
        </Text>
      </Box>

      {/* Chat Messages */}
      <Box flex="1" overflowY="auto" pr={2}>
        {(active?.messages ?? []).map((m, idx) => (
          <Box 
            key={idx} 
            mb={4}
            display="flex"
            justifyContent={m.role === "assistant" ? "flex-start" : "flex-end"}
          >
            <Box
              maxW={{ base: "95%", md: "80%" }}
              minW="200px"
              bg={m.role === "assistant" 
                ? "linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
                : "linear-gradient(135deg, brand.500 0%, brand.400 100%)"
              }
              color={m.role === "assistant" ? "white" : "white"}
              p={4}
              borderRadius={m.role === "assistant" ? "20px 20px 20px 8px" : "20px 20px 8px 20px"}
              border="1px solid"
              borderColor={m.role === "assistant" ? "whiteAlpha.200" : "brand.400"}
              backdropFilter="blur(20px)"
              boxShadow={m.role === "assistant" 
                ? "0 4px 16px rgba(0,0,0,0.1)"
                : "0 4px 16px rgba(132,64,255,0.3)"
              }
              position="relative"
              wordBreak="break-word"
              overflowWrap="break-word"
              overflow="hidden"
            >
              <Text 
                fontWeight="bold" 
                mb={2} 
                fontSize="sm"
                color={m.role === "assistant" ? "prismTeal.300" : "white"}
              >
                {m.role === "assistant" ? "🤖 PRISM AI Assistant" : "👤 You"}
              </Text>
              <Box
                wordBreak="break-word"
                overflowWrap="break-word"
                overflow="hidden"
                whiteSpace="pre-wrap"
              >
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {m.content}
                </ReactMarkdown>
              </Box>
              {m.plot_path && (
                <Box 
                  mt={3} 
                  p={4} 
                  bg="linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%)"
                  borderRadius="lg" 
                  border="1px solid" 
                  borderColor="whiteAlpha.200"
                  backdropFilter="blur(20px)"
                  boxShadow="0 2px 8px rgba(0,0,0,0.1)"
                >
                  
                  <Image 
                    src={getPlotUrl(m.plot_path)} 
                    alt="Generated plot" 
                    maxH="400px" 
                    objectFit="contain"
                    borderRadius="lg"
                    border="1px solid"
                    borderColor="whiteAlpha.300"
                    boxShadow="0 4px 12px rgba(0,0,0,0.1)"
                    onError={(e) => {
                      console.error('❌ Image load error:', e);
                      console.error('Failed URL:', getPlotUrl(m.plot_path || ''));
                    }}
                    onLoad={() => {
                      console.log('✅ Image loaded successfully:', getPlotUrl(m.plot_path || ''));
                    }}
                  />
                </Box>
              )}
              {m.step_log && m.step_log.length > 0 && (
                <Box mt={3}>
                  <Accordion allowToggle>
                    <AccordionItem border="none">
                      <AccordionButton 
                        px={0} 
                        py={2} 
                        _hover={{ bg: "transparent" }}
                        bg="linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)"
                        borderRadius="lg"
                        border="1px solid"
                        borderColor="whiteAlpha.200"
                      >
                        <Box flex="1" textAlign="left">
                          <Text fontSize="sm" fontWeight="semibold" color="prismTeal.300">
                            🔍 Agent Activity ({m.step_log.length} steps)
                          </Text>
                        </Box>
                        <AccordionIcon />
                      </AccordionButton>
                      <AccordionPanel px={0} pb={0} mt={2}>
                        <Box 
                          bg="linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%)" 
                          p={4} 
                          borderRadius="lg" 
                          border="1px solid" 
                          borderColor="whiteAlpha.200"
                          backdropFilter="blur(20px)"
                        >
                          <VStack align="stretch" spacing={3}>
                            {m.step_log.map((step, i) => (
                              <Box 
                                key={i} 
                                p={3} 
                                bg="linear-gradient(135deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.05) 100%)" 
                                borderRadius="md" 
                                borderLeft="3px solid" 
                                borderLeftColor="prismTeal.400"
                                boxShadow="0 2px 4px rgba(0,0,0,0.1)"
                              >
                                <Text 
                                  fontSize="xs" 
                                  color="whiteAlpha.800" 
                                  fontFamily="mono" 
                                  lineHeight="1.4"
                                  wordBreak="break-word"
                                  overflowWrap="break-word"
                                  whiteSpace="pre-wrap"
                                >
                                  {step}
                                </Text>
                              </Box>
                            ))}
                          </VStack>
                        </Box>
                      </AccordionPanel>
                    </AccordionItem>
                  </Accordion>
                </Box>
              )}
            </Box>
          </Box>
        ))}
      </Box>

      {/* Input Area */}
      <Box 
        bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
        borderRadius="xl"
        p={4}
        border="1px solid"
        borderColor="whiteAlpha.200"
        backdropFilter="blur(20px)"
        boxShadow="0 4px 16px rgba(0,0,0,0.1)"
      >
        <Flex gap={3} align="end">
          <Textarea 
            placeholder={`Ask a question about ${active_source_name}...`} 
            value={input} 
            onChange={(e) => setInput(e.target.value)}
            variant="modern"
            resize="none"
            rows={3}
            flex="1"
            _placeholder={{ color: "whiteAlpha.600" }}
          />
          <Button 
            onClick={send} 
            isDisabled={!input || loading} 
            minW="120px"
            size="lg"
            variant="solid"
            borderRadius="lg"
            _hover={{ transform: "translateY(-1px)" }}
          >
            {loading ? <Spinner size="sm" /> : "Send"}
          </Button>
        </Flex>
      </Box>
    </Flex>
  );
}
