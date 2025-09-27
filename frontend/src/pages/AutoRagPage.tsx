import { useEffect, useMemo, useRef, useState } from "react";
import { autoragApi } from "../api/client";
import ChatMessage from "../components/ChatMessage";
import ChatInput from "../components/ChatInput";
import {
  Box,
  Button,
  Flex,
  Heading,
  Input,
  Select,
  Spinner,
  Text,
  Textarea,
  useToast,
  Image,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Code,
  VStack,
} from "@chakra-ui/react";
import { useAppStore } from "../state/appStore";

async function getCapabilities() {
  const res = await autoragApi.get("/rags/capabilities");
  return res.data;
}
async function getAllRags() {
  const res = await autoragApi.get("/rags/");
  return res.data?.rags ?? [];
}
async function createRag(payload: any) {
  const res = await autoragApi.post("/rags/", payload);
  return res.data;
}
async function updateRag(ragId: string, payload: any) {
  const res = await autoragApi.put(`/rags/${ragId}`, payload);
  return res.data;
}
async function deleteRag(ragId: string) {
  const res = await autoragApi.delete(`/rags/${ragId}`);
  return res.data;
}
async function getDocuments(ragId: string) {
  const res = await autoragApi.get(`/rags/${ragId}/documents`);
  return res.data?.documents ?? [];
}
async function getChatHistory(ragId: string) {
  const res = await autoragApi.get(`/rags/${ragId}/chat/history`);
  return res.data ?? [];
}
async function postQuery(ragId: string, query: string, sessionId: string | null | undefined) {
  const res = await autoragApi.post(`/rags/${ragId}/chat`, { query, session_id: sessionId ?? null });
  return res.data;
}
async function uploadFile(ragId: string, file: File) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await autoragApi.post(`/rags/${ragId}/documents`, fd, { headers: { "Content-Type": "multipart/form-data" } });
  return res.data;
}
async function buildRagImage(ragId: string) {
  const res = await autoragApi.post(`/rags/${ragId}/export`);
  return res.data;
}

function ManagementView({ onOpenChat, onOpenEdit }: { onOpenChat: (id: string) => void; onOpenEdit: (id: string) => void }) {
  const toast = useToast();
  const [capabilities, setCapabilities] = useState<any>(null);
  const [rags, setRags] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [llmProvider, setLlmProvider] = useState("");
  const [llmModel, setLlmModel] = useState("");
  const [embedProvider, setEmbedProvider] = useState("");
  const [embedModel, setEmbedModel] = useState("");
  const [vectorStore, setVectorStore] = useState("");
  const [chunker, setChunker] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("You are a helpful AI assistant...");

  async function refresh() {
    setLoading(true);
    try {
      const [caps, list] = await Promise.all([getCapabilities(), getAllRags()]);
      setCapabilities(caps);
      setRags(list);
      const lp = Object.keys(caps?.available_llms || {})[0] || "";
      setLlmProvider(lp);
      setLlmModel(Object.keys(caps?.available_llms?.[lp] || {})[0] || "");
      const ep = Object.keys(caps?.available_embedders || {})[0] || "";
      setEmbedProvider(ep);
      setEmbedModel(Object.keys(caps?.available_embedders?.[ep] || {})[0] || "");
      setVectorStore(Object.keys(caps?.available_vector_stores || {})[0] || "");
      setChunker(Object.keys(caps?.available_chunkers || {})[0] || "");
    } catch (e: any) {
      toast({ status: "error", title: e?.response?.data?.detail ?? "AutoRAG backend not available" });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, []);

  // Ensure defaults are set after capabilities load (and when provider changes)
  useEffect(() => {
    if (!capabilities) return;
    const llmProviders = Object.keys(capabilities.available_llms || {});
    const embedProviders = Object.keys(capabilities.available_embedders || {});
    const stores = Object.keys(capabilities.available_vector_stores || {});
    const chunkers = Object.keys(capabilities.available_chunkers || {});
    if (!llmProvider && llmProviders.length > 0) setLlmProvider(llmProviders[0]);
    if (llmProvider && !llmModel) {
      const models = Object.keys(capabilities.available_llms?.[llmProvider] || {});
      if (models.length > 0) setLlmModel(models[0]);
    }
    if (!embedProvider && embedProviders.length > 0) setEmbedProvider(embedProviders[0]);
    if (embedProvider && !embedModel) {
      const models = Object.keys(capabilities.available_embedders?.[embedProvider] || {});
      if (models.length > 0) setEmbedModel(models[0]);
    }
    if (!vectorStore && stores.length > 0) setVectorStore(stores[0]);
    if (!chunker && chunkers.length > 0) setChunker(chunkers[0]);
  }, [capabilities, llmProvider, embedProvider]);

  async function handleCreate() {
    if (!name.trim() || !description.trim() || !systemPrompt.trim()) {
      toast({ status: "warning", title: "Name, Description, and Prompt are required" });
      return;
    }
    try {
      const payload = {
        name,
        description,
        system_prompt: systemPrompt,
        config: {
          llm_provider: llmProvider,
          llm_model: llmModel,
          embedding_provider: embedProvider,
          embedding_model: embedModel,
          vector_store: vectorStore,
          chunker,
        },
      };
      const result = await createRag(payload);
      toast({ status: "success", title: `Created RAG: ${result.name}` });
      setName(""); setDescription(""); setSystemPrompt("You are a helpful AI assistant...");
      refresh();
    } catch (e: any) {
      toast({ status: "error", title: e?.response?.data?.detail ?? String(e) });
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteRag(id);
      toast({ status: "success", title: "Deleted RAG" });
      refresh();
    } catch (e: any) {
      toast({ status: "error", title: e?.response?.data?.detail ?? String(e) });
    }
  }

  if (loading) return <Spinner />;
  if (!capabilities) return <Text color="gray.400">AutoRAG backend not available.</Text>;

  const llmProviders = Object.keys(capabilities.available_llms || {});
  const embedProviders = Object.keys(capabilities.available_embedders || {});
  const vectorStores = Object.keys(capabilities.available_vector_stores || {});
  const chunkers = Object.keys(capabilities.available_chunkers || {});

  return (
    <Flex direction="column" gap={8}>
      {/* Create RAG Section */}
      <Box 
        bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
        borderRadius="xl"
        p={6}
        border="1px solid"
        borderColor="whiteAlpha.200"
        backdropFilter="blur(20px)"
        boxShadow="0 4px 16px rgba(0,0,0,0.1)"
      >
        <Heading size="lg" color="white" mb={4} fontWeight="bold">
          🚀 Create a New RAG Instance
        </Heading>
        <Text color="whiteAlpha.700" fontSize="sm" mb={6} fontWeight="medium">
          Configure your RAG system with custom models and settings
        </Text>
        
        {/* Configuration Grid */}
        <Box 
          bg="linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)"
          borderRadius="xl"
          p={6}
          border="1px solid"
          borderColor="whiteAlpha.200"
          backdropFilter="blur(20px)"
          boxShadow="0 4px 16px rgba(0,0,0,0.1)"
        >
          <Text color="white" fontSize="md" fontWeight="semibold" mb={4} display="flex" alignItems="center" gap={2}>
            <Text>⚙️</Text>
            <Text>Configuration Settings</Text>
          </Text>
          
          <Flex gap={6} mt={4} wrap="wrap" justify="space-between">
            {/* LLM Provider */}
            <Box minW="280px" flex="1" maxW="400px">
              <Text color="white" fontSize="sm" fontWeight="semibold" mb={3} display="flex" alignItems="center" gap={2}>
                <Text>🤖</Text>
                <Text>LLM Provider</Text>
              </Text>
              <Select 
                value={llmProvider} 
                onChange={(e) => { const v=e.target.value; setLlmProvider(v); setLlmModel(""); }} 
                variant="modern"
                placeholder={llmProviders.length ? undefined : "No providers"}
                bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
                border="1px solid"
                borderColor="whiteAlpha.200"
                _focus={{
                  borderColor: "brand.400",
                  boxShadow: "0 0 0 1px rgba(132,64,255,0.3)",
                  bg: "rgba(255,255,255,0.15)"
                }}
                _hover={{
                  borderColor: "whiteAlpha.300",
                  bg: "rgba(255,255,255,0.1)"
                }}
                transition="all 0.3s ease"
              >
                {llmProviders.map((p) => <option key={p} value={p}>{p}</option>)}
              </Select>
            </Box>

            {/* LLM Model */}
            <Box minW="280px" flex="1" maxW="400px">
              <Text color="white" fontSize="sm" fontWeight="semibold" mb={3} display="flex" alignItems="center" gap={2}>
                <Text>🧠</Text>
                <Text>LLM Model</Text>
              </Text>
              <Select 
                value={llmModel} 
                onChange={(e) => setLlmModel(e.target.value)} 
                placeholder={llmProvider ? "Select a model" : "Select provider first"} 
                variant="modern"
                bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
                border="1px solid"
                borderColor="whiteAlpha.200"
                _focus={{
                  borderColor: "brand.400",
                  boxShadow: "0 0 0 1px rgba(132,64,255,0.3)",
                  bg: "rgba(255,255,255,0.15)"
                }}
                _hover={{
                  borderColor: "whiteAlpha.300",
                  bg: "rgba(255,255,255,0.1)"
                }}
                transition="all 0.3s ease"
              >
                {Object.keys(capabilities.available_llms?.[llmProvider]||{}).map((m) => <option key={m} value={m}>{m}</option>)}
              </Select>
            </Box>

            {/* Embedding Provider */}
            <Box minW="280px" flex="1" maxW="400px">
              <Text color="white" fontSize="sm" fontWeight="semibold" mb={3} display="flex" alignItems="center" gap={2}>
                <Text>🔗</Text>
                <Text>Embedding Provider</Text>
              </Text>
              <Select 
                value={embedProvider} 
                onChange={(e) => { const v=e.target.value; setEmbedProvider(v); setEmbedModel(""); }} 
                variant="modern"
                placeholder={embedProviders.length ? undefined : "No providers"}
                bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
                border="1px solid"
                borderColor="whiteAlpha.200"
                _focus={{
                  borderColor: "prismTeal.400",
                  boxShadow: "0 0 0 1px rgba(20,184,166,0.3)",
                  bg: "rgba(255,255,255,0.15)"
                }}
                _hover={{
                  borderColor: "whiteAlpha.300",
                  bg: "rgba(255,255,255,0.1)"
                }}
                transition="all 0.3s ease"
              >
                {embedProviders.map((p) => <option key={p} value={p}>{p}</option>)}
              </Select>
            </Box>

            {/* Embedding Model */}
            <Box minW="280px" flex="1" maxW="400px">
              <Text color="white" fontSize="sm" fontWeight="semibold" mb={3} display="flex" alignItems="center" gap={2}>
                <Text>🎯</Text>
                <Text>Embedding Model</Text>
              </Text>
              <Select 
                value={embedModel} 
                onChange={(e) => setEmbedModel(e.target.value)} 
                placeholder={embedProvider ? "Select a model" : "Select provider first"} 
                variant="modern"
                bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
                border="1px solid"
                borderColor="whiteAlpha.200"
                _focus={{
                  borderColor: "prismTeal.400",
                  boxShadow: "0 0 0 1px rgba(20,184,166,0.3)",
                  bg: "rgba(255,255,255,0.15)"
                }}
                _hover={{
                  borderColor: "whiteAlpha.300",
                  bg: "rgba(255,255,255,0.1)"
                }}
                transition="all 0.3s ease"
              >
                {Object.keys(capabilities.available_embedders?.[embedProvider]||{}).map((m) => <option key={m} value={m}>{m}</option>)}
              </Select>
            </Box>

            {/* Vector Store */}
            <Box minW="280px" flex="1" maxW="400px">
              <Text color="white" fontSize="sm" fontWeight="semibold" mb={3} display="flex" alignItems="center" gap={2}>
                <Text>🗄️</Text>
                <Text>Vector Store</Text>
              </Text>
              <Select 
                value={vectorStore} 
                onChange={(e) => setVectorStore(e.target.value)} 
                variant="modern"
                bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
                border="1px solid"
                borderColor="whiteAlpha.200"
                _focus={{
                  borderColor: "brand.400",
                  boxShadow: "0 0 0 1px rgba(132,64,255,0.3)",
                  bg: "rgba(255,255,255,0.15)"
                }}
                _hover={{
                  borderColor: "whiteAlpha.300",
                  bg: "rgba(255,255,255,0.1)"
                }}
                transition="all 0.3s ease"
              >
                {Object.keys(capabilities.available_vector_stores||{}).map((v) => <option key={v} value={v}>{v}</option>)}
              </Select>
            </Box>

            {/* Chunking Strategy */}
            <Box minW="280px" flex="1" maxW="400px">
              <Text color="white" fontSize="sm" fontWeight="semibold" mb={3} display="flex" alignItems="center" gap={2}>
                <Text>✂️</Text>
                <Text>Chunking Strategy</Text>
              </Text>
              <Select 
                value={chunker} 
                onChange={(e) => setChunker(e.target.value)} 
                variant="modern"
                bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
                border="1px solid"
                borderColor="whiteAlpha.200"
                _focus={{
                  borderColor: "prismTeal.400",
                  boxShadow: "0 0 0 1px rgba(20,184,166,0.3)",
                  bg: "rgba(255,255,255,0.15)"
                }}
                _hover={{
                  borderColor: "whiteAlpha.300",
                  bg: "rgba(255,255,255,0.1)"
                }}
                transition="all 0.3s ease"
              >
                {Object.keys(capabilities.available_chunkers||{}).map((c) => <option key={c} value={c}>{capabilities.available_chunkers[c]?.name ?? c}</option>)}
              </Select>
            </Box>
          </Flex>
        </Box>
        
        {/* RAG Details Section */}
        <Box 
          bg="linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)"
          borderRadius="xl"
          p={6}
          border="1px solid"
          borderColor="whiteAlpha.200"
          backdropFilter="blur(20px)"
          boxShadow="0 4px 16px rgba(0,0,0,0.1)"
          mt={6}
        >
          <Text color="white" fontSize="md" fontWeight="semibold" mb={4} display="flex" alignItems="center" gap={2}>
            <Text>📝</Text>
            <Text>RAG Details</Text>
          </Text>
          
          <VStack spacing={6} align="stretch">
            {/* RAG Name */}
            <Box>
              <Text color="white" fontSize="sm" fontWeight="semibold" mb={3} display="flex" alignItems="center" gap={2}>
                <Text>🏷️</Text>
                <Text>RAG Name</Text>
              </Text>
              <Input 
                value={name} 
                onChange={(e) => setName(e.target.value)} 
                placeholder="e.g., Financial Analyst Bot" 
                variant="modern"
                size="lg"
                bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
                border="1px solid"
                borderColor="whiteAlpha.200"
                _focus={{
                  borderColor: "brand.400",
                  boxShadow: "0 0 0 1px rgba(132,64,255,0.3)",
                  bg: "rgba(255,255,255,0.15)"
                }}
                _hover={{
                  borderColor: "whiteAlpha.300",
                  bg: "rgba(255,255,255,0.1)"
                }}
                transition="all 0.3s ease"
              />
            </Box>

            {/* Description */}
            <Box>
              <Text color="white" fontSize="sm" fontWeight="semibold" mb={3} display="flex" alignItems="center" gap={2}>
                <Text>📄</Text>
                <Text>Description</Text>
              </Text>
              <Textarea 
                value={description} 
                onChange={(e) => setDescription(e.target.value)} 
                placeholder="Provide a brief description of what this RAG instance does..." 
                variant="modern"
                rows={3}
                bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
                border="1px solid"
                borderColor="whiteAlpha.200"
                _focus={{
                  borderColor: "prismTeal.400",
                  boxShadow: "0 0 0 1px rgba(20,184,166,0.3)",
                  bg: "rgba(255,255,255,0.15)"
                }}
                _hover={{
                  borderColor: "whiteAlpha.300",
                  bg: "rgba(255,255,255,0.1)"
                }}
                transition="all 0.3s ease"
                resize="vertical"
              />
            </Box>

            {/* System Prompt */}
            <Box>
              <Text color="white" fontSize="sm" fontWeight="semibold" mb={3} display="flex" alignItems="center" gap={2}>
                <Text>🤖</Text>
                <Text>Custom System Prompt</Text>
              </Text>
              <Textarea 
                value={systemPrompt} 
                onChange={(e) => setSystemPrompt(e.target.value)} 
                rows={6} 
                variant="modern"
                bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
                border="1px solid"
                borderColor="whiteAlpha.200"
                _focus={{
                  borderColor: "brand.400",
                  boxShadow: "0 0 0 1px rgba(132,64,255,0.3)",
                  bg: "rgba(255,255,255,0.15)"
                }}
                _hover={{
                  borderColor: "whiteAlpha.300",
                  bg: "rgba(255,255,255,0.1)"
                }}
                transition="all 0.3s ease"
                resize="vertical"
                placeholder="Define how the AI assistant should behave and respond..."
              />
            </Box>
          </VStack>
        </Box>

        {/* Create Button */}
        <Button 
          mt={6} 
          onClick={handleCreate}
          size="lg"
          variant="solid"
          borderRadius="lg"
          bg="linear-gradient(135deg, brand.500 0%, brand.400 100%)"
          color="white"
          fontWeight="semibold"
          _hover={{ 
            transform: "translateY(-2px)",
            boxShadow: "0 8px 24px rgba(132,64,255,0.4)",
            bg: "linear-gradient(135deg, brand.600 0%, brand.500 100%)"
          }}
          _active={{
            transform: "translateY(0px)"
          }}
          transition="all 0.3s ease"
          leftIcon={<Text fontSize="lg">🚀</Text>}
        >
          Create RAG Instance
        </Button>
      </Box>

      {/* Available RAG Instances */}
      <Box 
        bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
        borderRadius="xl"
        p={6}
        border="1px solid"
        borderColor="whiteAlpha.200"
        backdropFilter="blur(20px)"
        boxShadow="0 4px 16px rgba(0,0,0,0.1)"
      >
        <Heading size="lg" color="white" mb={4} fontWeight="bold">
          📚 Available RAG Instances
        </Heading>
        {rags.length === 0 ? (
          <Box 
            bg="linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)"
            borderRadius="lg"
            p={6}
            border="1px solid"
            borderColor="whiteAlpha.200"
            textAlign="center"
          >
            <Text color="whiteAlpha.600" fontSize="sm" fontWeight="medium">
              No RAG instances found. Create one above to get started.
            </Text>
          </Box>
        ) : (
          <Box mt={4} display="grid" gap={4}>
            {rags.map((rag: any) => (
              <Box 
                key={rag.id} 
                bg="linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%)"
                p={5} 
                borderRadius="lg"
                border="1px solid"
                borderColor="whiteAlpha.200"
                backdropFilter="blur(20px)"
                boxShadow="0 2px 8px rgba(0,0,0,0.1)"
                _hover={{
                  boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                  transform: "translateY(-2px)",
                  borderColor: "whiteAlpha.300"
                }}
                transition="all 0.3s ease"
              >
                <Flex justify="space-between" align="center" mb={4}>
                  <Box flex="1">
                    <Heading size="md" color="white" mb={2} fontWeight="bold">{rag.name}</Heading>
                    <Text fontSize="xs" color="whiteAlpha.600" mb={2}>ID: {rag.id}</Text>
                    <Text color="whiteAlpha.700" fontSize="sm">{rag.description || "No description."}</Text>
                  </Box>
                  <Flex gap={3}>
                    <Button 
                      onClick={() => onOpenChat(rag.id)}
                      size="sm"
                      variant="solid"
                      borderRadius="lg"
                      _hover={{ transform: "translateY(-1px)" }}
                    >
                      💬 Chat
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={() => onOpenEdit(rag.id)}
                      size="sm"
                      borderRadius="lg"
                      _hover={{ transform: "translateY(-1px)" }}
                    >
                      ✏️ Edit
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={() => handleDelete(rag.id)}
                      size="sm"
                      borderRadius="lg"
                      colorScheme="red"
                      _hover={{ transform: "translateY(-1px)" }}
                    >
                      🗑️ Delete
                    </Button>
                  </Flex>
                </Flex>
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
                        <Text fontSize="sm" fontWeight="semibold" color="prismTeal.300">View Configuration</Text>
                      </Box>
                      <AccordionIcon />
                    </AccordionButton>
                    <AccordionPanel px={0} pb={0} mt={2}>
                      <Box 
                        bg="linear-gradient(135deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.05) 100%)" 
                        p={4} 
                        borderRadius="lg" 
                        border="1px solid" 
                        borderColor="whiteAlpha.200"
                        backdropFilter="blur(20px)"
                      >
                        <Code 
                          fontSize="xs" 
                          whiteSpace="pre-wrap" 
                          p={3} 
                          bg="rgba(0,0,0,0.2)" 
                          color="white" 
                          borderRadius="md"
                          display="block"
                          fontFamily="mono"
                        >
                          {JSON.stringify(rag.config, null, 2)}
                        </Code>
                      </Box>
                    </AccordionPanel>
                  </AccordionItem>
                </Accordion>
              </Box>
            ))}
          </Box>
        )}
      </Box>
    </Flex>
  );
}

function EditView({ ragId, onBack }: { ragId: string; onBack: () => void }) {
  const toast = useToast();
  const [capabilities, setCapabilities] = useState<any>(null);
  const [rag, setRag] = useState<any>(null);

  const [llmProvider, setLlmProvider] = useState("");
  const [llmModel, setLlmModel] = useState("");
  const [embedProvider, setEmbedProvider] = useState("");
  const [embedModel, setEmbedModel] = useState("");
  const [vectorStore, setVectorStore] = useState("");
  const [chunker, setChunker] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [caps, list] = await Promise.all([getCapabilities(), getAllRags()]);
        setCapabilities(caps);
        const rd = list.find((r: any) => r.id === ragId);
        if (!rd) throw new Error("Could not load RAG details");
        setRag(rd);
        setName(rd.name);
        setDescription(rd.description);
        setSystemPrompt(rd.system_prompt);
        const cc = rd.config || {};
        setLlmProvider(cc.llm_provider);
        setLlmModel(cc.llm_model);
        setEmbedProvider(cc.embedding_provider);
        setEmbedModel(cc.embedding_model);
        setVectorStore(cc.vector_store);
        setChunker(cc.chunker);
      } catch (e: any) {
        toast({ status: "error", title: e?.response?.data?.detail ?? String(e) });
      }
    })();
  }, [ragId]);

  async function handleSave() {
    try {
      const payload = {
        name,
        description,
        system_prompt: systemPrompt,
        config: { llm_provider: llmProvider, llm_model: llmModel, embedding_provider: embedProvider, embedding_model: embedModel, vector_store: vectorStore, chunker },
      };
      const result = await updateRag(ragId, payload);
      toast({ status: "success", title: `Updated RAG: ${result.name}` });
      onBack();
    } catch (e: any) {
      toast({ status: "error", title: e?.response?.data?.detail ?? String(e) });
    }
  }

  if (!rag || !capabilities) return <Spinner />;

  return (
    <Flex direction="column" gap={4}>
      <Button variant="outline" onClick={onBack}>Back to Management</Button>
      <Heading size="md">Edit RAG Instance</Heading>
      <Flex gap={3} wrap="wrap">
        <Box minW="220px">
          <Text>LLM Provider</Text>
          <Select value={llmProvider} onChange={(e) => { const v=e.target.value; setLlmProvider(v); setLlmModel(Object.keys(capabilities.available_llms?.[v]||{})[0]||""); }}>
            {Object.keys(capabilities.available_llms||{}).map((p) => <option key={p} value={p}>{p}</option>)}
          </Select>
        </Box>
        <Box minW="220px">
          <Text>LLM Model</Text>
          <Select value={llmModel} onChange={(e) => setLlmModel(e.target.value)}>
            {Object.keys(capabilities.available_llms?.[llmProvider]||{}).map((m) => <option key={m} value={m}>{m}</option>)}
          </Select>
        </Box>
        <Box minW="220px">
          <Text>Embedding Provider</Text>
          <Select value={embedProvider} onChange={(e) => { const v=e.target.value; setEmbedProvider(v); setEmbedModel(Object.keys(capabilities.available_embedders?.[v]||{})[0]||""); }}>
            {Object.keys(capabilities.available_embedders||{}).map((p) => <option key={p} value={p}>{p}</option>)}
          </Select>
        </Box>
        <Box minW="220px">
          <Text>Embedding Model</Text>
          <Select value={embedModel} onChange={(e) => setEmbedModel(e.target.value)}>
            {Object.keys(capabilities.available_embedders?.[embedProvider]||{}).map((m) => <option key={m} value={m}>{m}</option>)}
          </Select>
        </Box>
        <Box minW="220px">
          <Text>Vector Store</Text>
          <Select value={vectorStore} isDisabled>
            {Object.keys(capabilities.available_vector_stores||{}).map((v) => <option key={v} value={v}>{v}</option>)}
          </Select>
          <Text fontSize="xs" color="gray.500">Changing vector store is not supported.</Text>
        </Box>
        <Box minW="220px">
          <Text>Chunking Strategy</Text>
          <Select value={chunker} onChange={(e) => setChunker(e.target.value)}>
            {Object.keys(capabilities.available_chunkers||{}).map((c) => <option key={c} value={c}>{capabilities.available_chunkers[c]?.name ?? c}</option>)}
          </Select>
        </Box>
      </Flex>
      <Box>
        <Text>RAG Name</Text>
        <Input value={name} onChange={(e) => setName(e.target.value)} />
      </Box>
      <Box>
        <Text>Description</Text>
        <Textarea value={description} onChange={(e) => setDescription(e.target.value)} />
      </Box>
      <Box>
        <Text>Custom System Prompt</Text>
        <Textarea value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} rows={6} />
      </Box>
      <Button onClick={handleSave}>Save Changes</Button>
    </Flex>
  );
}

function ChatView({ ragId, onBack }: { ragId: string; onBack: () => void }) {
  const toast = useToast();
  const { session_ids = {}, chat_histories = {} } = useAppStore();
  const [documents, setDocuments] = useState<any[]>([]);
  const [ragDetails, setRagDetails] = useState<any>(null);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const history = chat_histories[ragId] ?? [];
  const sessionId = session_ids[ragId] ?? null;

  useEffect(() => {
    (async () => {
      try {
        const list = await getAllRags();
        const rd = list.find((r: any) => r.id === ragId);
        setRagDetails(rd);
      } catch {}
    })();
  }, [ragId]);

  useEffect(() => {
    (async () => {
      try {
        const docs = await getDocuments(ragId);
        setDocuments(docs);
      } catch {}
      setLoadingDocs(false);
    })();
  }, [ragId]);

  useEffect(() => {
    (async () => {
      if (!history || history.length === 0) {
        try {
          const h = await getChatHistory(ragId);
          const reconstructed = h.map((m: any) => ({ role: m.role, content: m.content, sources: m?.metadata?.sources ?? [] }));
          useAppStore.setState((s) => ({ chat_histories: { ...s.chat_histories, [ragId]: reconstructed } }));
        } catch {}
      }
    })();
  }, [ragId]);

  async function send() {
    if (!input.trim()) return;
    const newHistory = [...history, { role: "user", content: input }];
    useAppStore.setState((s) => ({ chat_histories: { ...s.chat_histories, [ragId]: newHistory } }));
    setInput("");
    setSending(true);
    try {
      const res = await postQuery(ragId, newHistory[newHistory.length - 1].content, sessionId);
      const answer = res?.answer ?? "Sorry, I encountered an error.";
      const sources = res?.sources ?? [];
      const nextSessionId = res?.session_id ?? sessionId ?? null;
      useAppStore.setState((s) => ({
        chat_histories: { ...s.chat_histories, [ragId]: [...newHistory, { role: "assistant", content: answer, sources }] },
        session_ids: { ...(s.session_ids ?? {}), [ragId]: nextSessionId },
      }));
    } catch (e: any) {
      toast({ status: "error", title: e?.response?.data?.detail ?? String(e) });
    } finally {
      setSending(false);
    }
  }

  async function onUploadFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      try { await uploadFile(ragId, f); } catch {}
    }
    setLoadingDocs(true);
    try { setDocuments(await getDocuments(ragId)); } catch {}
    setLoadingDocs(false);
    toast({ status: "success", title: "Upload triggered. Ingestion in background." });
  }

  return (
    <Flex direction="column" gap={3}>
      <Flex justify="space-between" align="center">
        <Heading size="md">Chat with: {ragDetails?.name ?? ragId}</Heading>
        <Button variant="outline" onClick={onBack}>Back to Management</Button>
      </Flex>

      <Flex gap={6}>
        <Box w="320px">
          <Heading size="sm">Knowledge Base</Heading>
          <Text fontSize="sm" color="gray.500">Manage documents for this RAG.</Text>
          <Input type="file" ref={fileInputRef} multiple mt={2} onChange={(e) => onUploadFiles(e.target.files)} />
          <Box mt={3}>
            <Heading size="xs">Ingested Documents</Heading>
            {loadingDocs ? (
              <Spinner size="sm" mt={2} />
            ) : documents.length === 0 ? (
              <Text mt={2} color="gray.400">No documents have been ingested yet.</Text>
            ) : (
              <Box mt={2} display="grid" gap={2}>
                {documents.map((doc: any) => {
                  const statusIcon = doc.status === 'COMPLETED' ? '✅' : (['PROCESSING','PENDING'].includes(doc.status) ? '⏳' : '❌');
                  const dt = doc.created_at ? new Date(doc.created_at).toLocaleString() : '';
                  return <Box key={doc.id} p={2} borderWidth="1px" borderRadius="md">{statusIcon} {doc.file_name} <Text as="span" color="gray.500">({dt})</Text></Box>;
                })}
              </Box>
            )}
          </Box>
        </Box>

        <Box flex="1">
          {(history ?? []).map((m: any, idx: number) => (
            <ChatMessage
              key={idx}
              role={m.role}
              content={m.content}
              sources={m.sources}
              timestamp={new Date().toLocaleTimeString()}
            />
          ))}

          <Box mt={4}>
            <ChatInput
              value={input}
              onChange={setInput}
              onSend={send}
              loading={sending}
              placeholder="Ask a question about your documents..."
            />
          </Box>
        </Box>
      </Flex>
    </Flex>
  );
}

export default function AutoRagPage() {
  const { selected_rag_id, editing_rag_id } = useAppStore();
  if (editing_rag_id) {
    return <EditView ragId={editing_rag_id} onBack={() => useAppStore.setState({ editing_rag_id: null })} />;
  }
  if (selected_rag_id) {
    return <ChatView ragId={selected_rag_id} onBack={() => useAppStore.setState({ selected_rag_id: null })} />;
  }
  return (
    <ManagementView onOpenChat={(id) => useAppStore.setState({ selected_rag_id: id })} onOpenEdit={(id) => useAppStore.setState({ editing_rag_id: id })} />
  );
}
