import { useRef, useState } from "react";
import {
  Box,
  Button,
  Divider,
  Flex,
  Heading,
  Icon,
  Input,
  NumberInput,
  NumberInputField,
  InputGroup,
  InputRightElement,
  Select,
  Text,
  useToast,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  VStack,
  FormControl,
  FormLabel,
  Code,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
} from "@chakra-ui/react";
import { FiPlus, FiSend, FiRefreshCcw, FiEye, FiEyeOff } from "react-icons/fi";
import { useAppStore, resetState, setActiveSource, updateSource } from "../state/appStore";
import { SourceConfig } from "../types";
import { prismApi, uploadSourceFile, fetchSession } from "../api/client";

export default function Sidebar() {
  const toast = useToast();
  const { sources, active_source_name, session_id } = useAppStore();

  const [fileSourceName, setFileSourceName] = useState("");
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [dbType, setDbType] = useState<"postgresql" | "mysql" | "sqlite">("postgresql");
  const [dbSourceName, setDbSourceName] = useState("");
  const [dbHost, setDbHost] = useState("localhost");
  const [dbPort, setDbPort] = useState(5432);
  const [dbUsername, setDbUsername] = useState("nagurshareefshaik");
  const [dbPassword, setDbPassword] = useState("");
  const [dbDatabase, setDbDatabase] = useState("healthcare");
  const [sqliteUpload, setSqliteUpload] = useState<File | null>(null);
  const [resumeSessionId, setResumeSessionId] = useState("");
  const [analyzingSource, setAnalyzingSource] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  // Mirror prism.py defaults for DB connections
  function applyDbDefaults(nextType: "postgresql" | "mysql" | "sqlite") {
    if (nextType === "sqlite") {
      return;
    }
    const defaults = {
      postgresql: { host: "localhost", port: 5432, username: "nagurshareefshaik", database: "healthcare" },
      mysql: { host: "localhost", port: 3306, username: "root", database: "walmart" },
    };
    const config = defaults[nextType];
    setDbHost(config.host);
    setDbPort(config.port);
    setDbUsername(config.username);
    setDbDatabase(config.database);
    setDbPassword("");
  }

  function isDbFormValid() {
    if (dbType === "sqlite") {
      return !!sqliteUpload;
    }
    return !!(dbHost && dbPort && dbUsername && dbDatabase);
  }

  async function handleAnalyze(name: string) {
    setAnalyzingSource(name);
    const source = sources[name];
    try {
      const res = await prismApi.post("/process_source", { source_config: source.config });
      const result = res.data;
      if (result?.summary) {
        updateSource(name, {
          analyzed: true,
          summary: result.summary,
          data_context: result.data_context,
          messages: [{ role: "assistant", content: result.summary }],
        });
        setActiveSource(name);
        toast({ status: "success", title: `Analyzed ${name}` });
      } else {
        toast({ status: "error", title: "Invalid response from backend" });
      }
    } catch (e: any) {
      toast({ status: "error", title: e?.response?.data?.detail ?? String(e) });
    } finally {
      setAnalyzingSource(null);
    }
  }

  async function handleAddFileSource() {
    if (!fileSourceName || !fileToUpload) return;
    try {
      const path = await uploadSourceFile(session_id, fileToUpload);
    const config: SourceConfig = { type: "file", path };
    updateSource(fileSourceName, { config, analyzed: false });
    setFileSourceName("");
      setFileToUpload(null);
      toast({ status: "success", title: "File uploaded" });
    } catch (e: any) {
      toast({ status: "error", title: e?.response?.data?.detail ?? String(e) });
    }
  }

  async function handleAddDbSource() {
    if (!dbSourceName || !isDbFormValid()) return;
    try {
    let config: SourceConfig;
    if (dbType === "sqlite") {
        if (!sqliteUpload) return;
        const path = await uploadSourceFile(session_id, sqliteUpload);
        config = { type: "sqlite", path } as any;
    } else {
      config = {
        type: dbType,
          host: dbHost,
          port: dbPort,
          username: dbUsername,
          password: dbPassword,
          database: dbDatabase,
      } as any;
    }
    updateSource(dbSourceName, { config, analyzed: false });
    setDbSourceName("");
      setSqliteUpload(null);
      toast({ status: "success", title: "DB source added" });
    } catch (e: any) {
      toast({ status: "error", title: e?.response?.data?.detail ?? String(e) });
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] || null;
    setFileToUpload(file);
    if (file && !fileSourceName) {
      const base = file.name.replace(/\.[^.]+$/, "");
      setFileSourceName(base);
    }
  }

  function handleSqliteFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] || null;
    setSqliteUpload(file);
  }

  function handleNewSession() {
    resetState();
    toast({ status: "info", title: "Started new session" });
  }

  function handleResumeSession() {
    if (!resumeSessionId) return;
    (async () => {
      try {
        const data = await fetchSession(resumeSessionId.trim());
        useAppStore.setState({
          session_id: data.session_id,
          sources: data.sources ?? {},
          active_source_name: data.active_source_name ?? null,
          modeling: data.modeling ?? useAppStore.getState().modeling,
        });
        toast({ status: "success", title: "PRISM session resumed" });
      } catch (e: any) {
        toast({ status: "error", title: e?.response?.data?.detail ?? "Failed to resume session" });
      }
    })();
  }

  return (
    <Box
      w="320px"
      h="100vh"
      bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
      backdropFilter="saturate(180%) blur(40px)"
      borderRight="1px solid"
      borderColor="whiteAlpha.200"
      boxShadow="0 8px 32px rgba(0,0,0,0.12), 0 4px 16px rgba(0,0,0,0.08)"
      p={6}
      overflowY="auto"
      position="fixed"
      left={0}
      top={0}
      zIndex={10}
      _before={{
        content: '""',
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: "linear-gradient(135deg, rgba(255,255,255,0.08) 0%, transparent 50%, rgba(255,255,255,0.03) 100%)",
        pointerEvents: "none",
        zIndex: 1,
      }}
    >
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box textAlign="center" mb={8} position="relative" zIndex={2}>
          <Heading 
            size="lg" 
            bgGradient="linear(135deg, brand.300 0%, prismTeal.300 50%, accent.300 100%)" 
            bgClip="text"
            textShadow="0 0 20px rgba(132,64,255,0.3)"
            letterSpacing="wide"
            mb={3}
            fontWeight="extrabold"
          >
            Data Sources
          </Heading>
          <Text fontSize="sm" color="whiteAlpha.700" fontWeight="medium" mb={4}>
            Connect & Analyze Your Data
          </Text>
          <Box 
            w="100%" 
            h="1px" 
            bgGradient="linear(90deg, transparent 0%, whiteAlpha.300 50%, transparent 100%)"
            mb={2}
          />
        </Box>

        {/* Add New Data Source */}
        <Box
          bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
          borderRadius="xl"
          p={6}
          border="1px solid"
          borderColor="whiteAlpha.200"
          backdropFilter="blur(20px)"
          boxShadow="0 4px 16px rgba(0,0,0,0.1)"
          position="relative"
          zIndex={2}
          _hover={{
            boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
            borderColor: "whiteAlpha.300",
            transform: "translateY(-2px)",
          }}
          transition="all 0.3s ease"
        >
          <Accordion allowToggle defaultIndex={0}>
            <AccordionItem border="none">
              <AccordionButton
                _hover={{ bg: "transparent" }}
                px={5}
                py={4}
                borderRadius="lg"
                bg="linear-gradient(135deg, brand.500 0%, brand.400 100%)"
                color="white"
                fontWeight="bold"
                boxShadow="0 4px 16px rgba(132,64,255,0.3)"
                border="1px solid"
                borderColor="brand.400"
                _expanded={{ 
                  bg: "linear-gradient(135deg, brand.600 0%, brand.500 100%)",
                  boxShadow: "0 6px 20px rgba(132,64,255,0.4)",
                  transform: "translateY(-1px)",
                }}
                transition="all 0.3s ease"
              >
                <Box flex="1" textAlign="left" display="flex" alignItems="center" gap={2}>
                  <Text fontSize="md" fontWeight="semibold">➕ Add New Data Source</Text>
                </Box>
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel px={0} pb={0}>
                <Tabs variant="enclosed" colorScheme="teal" mt={4}>
                  <TabList 
                    bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)" 
                    borderRadius="lg" 
                    p={1}
                    border="1px solid"
                    borderColor="whiteAlpha.200"
                    backdropFilter="blur(20px)"
                    boxShadow="0 2px 8px rgba(0,0,0,0.1)"
                  >
                    <Tab 
                      borderRadius="md" 
                      fontWeight="semibold"
                      fontSize="sm"
                      _selected={{ 
                        bg: "linear-gradient(135deg, prismTeal.500 0%, prismTeal.400 100%)",
                        color: "white",
                        boxShadow: "0 4px 12px rgba(20,184,166,0.3)",
                        transform: "translateY(-1px)",
                      }}
                      transition="all 0.3s ease"
                    >
                      📁 File Upload
                    </Tab>
                    <Tab 
                      borderRadius="md" 
                      fontWeight="semibold"
                      fontSize="sm"
                      _selected={{ 
                        bg: "linear-gradient(135deg, brand.500 0%, brand.400 100%)",
                        color: "white",
                        boxShadow: "0 4px 12px rgba(132,64,255,0.3)",
                        transform: "translateY(-1px)",
                      }}
                      transition="all 0.3s ease"
                    >
                      🗄️ Database
                    </Tab>
                  </TabList>

                  <TabPanels>
                    {/* File Upload Tab */}
                    <TabPanel px={0} py={4} bg="linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)" borderRadius="lg" mt={3}>
                      <VStack spacing={4} align="stretch">
                        <FormControl>
                          <FormLabel color="white" fontSize="sm" fontWeight="semibold" mb={2}>
                            File Source Name
                          </FormLabel>
                          <Input
                            placeholder="Enter source name"
                            value={fileSourceName}
                            onChange={(e) => setFileSourceName(e.target.value)}
                            variant="modern"
                            size="sm"
                            _placeholder={{ color: "whiteAlpha.600" }}
                          />
                        </FormControl>

                        <FormControl>
                          <FormLabel color="white" fontSize="sm" fontWeight="semibold" mb={2}>
                            Upload an Excel file
                          </FormLabel>
                          <Input
                            type="file"
                            accept=".xlsx"
                            onChange={handleFileChange}
                            variant="modern"
                            size="sm"
                            p={2}
                          />
                        </FormControl>

                        <Button
                          colorScheme="teal"
                          onClick={handleAddFileSource}
                          isDisabled={!fileSourceName || !fileToUpload}
                          size="sm"
                          borderRadius="lg"
                          _hover={{ transform: "translateY(-1px)" }}
                          variant="solid"
                        >
                          Add File Source
                        </Button>
                      </VStack>
                    </TabPanel>

                    {/* Database Tab */}
                    <TabPanel px={0} py={4} bg="linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)" borderRadius="lg" mt={3}>
                      <VStack spacing={4} align="stretch">
                        <FormControl>
                          <FormLabel color="white" fontSize="sm">
                            Database Type
                          </FormLabel>
                          <Select
                            value={dbType}
                            onChange={(e) => {
                              const v = e.target.value as any;
                              setDbType(v);
                              applyDbDefaults(v);
                            }}
                            bg="whiteAlpha.200"
                            border="none"
                            color="white"
                            _focus={{ bg: "whiteAlpha.300", ring: "2px", ringColor: "prismTeal.400" }}
                            borderRadius="md"
                            _hover={{ bg: "whiteAlpha.300" }}
                          >
            <option value="postgresql">postgresql</option>
            <option value="mysql">mysql</option>
            <option value="sqlite">sqlite</option>
          </Select>
                        </FormControl>

                        <FormControl>
                          <FormLabel color="white" fontSize="sm">
                            DB Source Name
                          </FormLabel>
                          <Input
                            placeholder="Enter source name"
                            value={dbSourceName}
                            onChange={(e) => setDbSourceName(e.target.value)}
                            bg="whiteAlpha.200"
                            border="none"
                            color="white"
                            _placeholder={{ color: "whiteAlpha.700" }}
                            _focus={{ bg: "whiteAlpha.300", ring: "2px", ringColor: "prismTeal.400" }}
                          />
                        </FormControl>

          {dbType === "sqlite" ? (
                          <FormControl>
                            <FormLabel color="white" fontSize="sm">
                              Upload SQLite Database File
                            </FormLabel>
                            <Input
                              type="file"
                              accept=".db,.sqlite,.sqlite3"
                              onChange={handleSqliteFileChange}
                              p={1}
                              bg="whiteAlpha.200"
                              border="none"
                              color="white"
                              _focus={{ bg: "whiteAlpha.300", ring: "2px", ringColor: "prismTeal.400" }}
                            />
                          </FormControl>
          ) : (
            <>
                            <FormControl>
                              <FormLabel color="white" fontSize="sm">
                                Host
                              </FormLabel>
                              <Input
                                placeholder="localhost"
                                value={dbHost}
                                onChange={(e) => setDbHost(e.target.value)}
                                bg="whiteAlpha.200"
                                border="none"
                                color="white"
                                _placeholder={{ color: "whiteAlpha.700" }}
                                _focus={{ bg: "whiteAlpha.300", ring: "2px", ringColor: "prismTeal.400" }}
                              />
                            </FormControl>

                            <FormControl>
                              <FormLabel color="white" fontSize="sm">
                                Port
                              </FormLabel>
                              <NumberInput
                                value={dbPort}
                                onChange={(_, value) => setDbPort(value || 0)}
                                bg="whiteAlpha.200"
                                border="none"
                                color="white"
                                _focus={{ bg: "whiteAlpha.300", ring: "2px", ringColor: "prismTeal.400" }}
                              >
                                <NumberInputField
                                  placeholder={dbType === "postgresql" ? "5432" : "3306"}
                                  _placeholder={{ color: "whiteAlpha.700" }}
                                />
              </NumberInput>
                            </FormControl>

                            <FormControl>
                              <FormLabel color="white" fontSize="sm">
                                Username
                              </FormLabel>
                              <Input
                                placeholder={dbType === "postgresql" ? "nagurshareefshaik" : "root"}
                                value={dbUsername}
                                onChange={(e) => setDbUsername(e.target.value)}
                                bg="whiteAlpha.200"
                                border="none"
                                color="white"
                                _placeholder={{ color: "whiteAlpha.700" }}
                                _focus={{ bg: "whiteAlpha.300", ring: "2px", ringColor: "prismTeal.400" }}
                              />
                            </FormControl>

                            <FormControl>
                              <FormLabel color="white" fontSize="sm">
                                Password
                              </FormLabel>
                              <InputGroup>
                                <Input
                                  type={showPassword ? "text" : "password"}
                                  value={dbPassword}
                                  onChange={(e) => setDbPassword(e.target.value)}
                                  bg="whiteAlpha.200"
                                  border="none"
                                  color="white"
                                  _placeholder={{ color: "whiteAlpha.700" }}
                                  _focus={{ bg: "whiteAlpha.300", ring: "2px", ringColor: "prismTeal.400" }}
                                />
                                <InputRightElement width="2.5rem">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setShowPassword((s) => !s)}
                                    _hover={{ bg: "whiteAlpha.200" }}
                                  >
                                    {showPassword ? <FiEyeOff /> : <FiEye />}
                                  </Button>
                                </InputRightElement>
                              </InputGroup>
                            </FormControl>

                            <FormControl>
                              <FormLabel color="white" fontSize="sm">
                                Database Name
                              </FormLabel>
                              <Input
                                placeholder={dbType === "postgresql" ? "healthcare" : "walmart"}
                                value={dbDatabase}
                                onChange={(e) => setDbDatabase(e.target.value)}
                                bg="whiteAlpha.200"
                                border="none"
                                color="white"
                                _placeholder={{ color: "whiteAlpha.700" }}
                                _focus={{ bg: "whiteAlpha.300", ring: "2px", ringColor: "prismTeal.400" }}
                              />
                            </FormControl>
            </>
          )}

                        <Button
                          colorScheme="teal"
                          onClick={handleAddDbSource}
                          isDisabled={!dbSourceName || !isDbFormValid()}
                          size="sm"
                          borderRadius="md"
                          _hover={{ transform: "translateY(-1px)" }}
                        >
                          Add DB Source
                        </Button>
                      </VStack>
                    </TabPanel>
                  </TabPanels>
                </Tabs>
              </AccordionPanel>
            </AccordionItem>
          </Accordion>
      </Box>

        <Divider borderColor="whiteAlpha.300" />

        {/* Configured Data Sources */}
        <Box>
          <Heading size="md" color="white" mb={4} fontWeight="bold">
            Data Sources
          </Heading>
          {Object.keys(sources).length === 0 ? (
            <Box 
              bg="linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)"
              borderRadius="lg"
              p={4}
              border="1px solid"
              borderColor="whiteAlpha.200"
              textAlign="center"
            >
              <Text color="whiteAlpha.600" fontSize="sm" fontWeight="medium">
                No data sources added yet.
              </Text>
            </Box>
          ) : (
            <VStack spacing={3} align="stretch">
              {Object.entries(sources).map(([name, sourceData]) => (
                <Box
                  key={name}
                  bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
                  borderRadius="lg"
                  p={4}
                  border="1px solid"
                  borderColor="whiteAlpha.200"
                  backdropFilter="blur(20px)"
                  boxShadow="0 2px 8px rgba(0,0,0,0.1)"
                  _hover={{ 
                    bg: "linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.08) 100%)",
                    transform: "translateY(-2px)",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.15)"
                  }}
                  transition="all 0.3s ease"
                >
                  <VStack spacing={3} align="stretch">
                    <Text color="white" fontWeight="bold" fontSize="sm">
                      {name} ({sourceData.config.type})
                    </Text>
                    {!sourceData.analyzed ? (
                      <Button
                        colorScheme="teal"
                        size="sm"
                        onClick={() => handleAnalyze(name)}
                        isLoading={analyzingSource === name}
                        _hover={{ transform: "translateY(-1px)" }}
                        variant="solid"
                        borderRadius="lg"
                      >
                        Analyze
                      </Button>
                    ) : (
                      <Button
                        colorScheme={active_source_name === name ? "teal" : "gray"}
                        variant={active_source_name === name ? "solid" : "outline"}
                        size="sm"
                        onClick={() => setActiveSource(name)}
                        _hover={{ transform: "translateY(-1px)" }}
                        borderRadius="lg"
                      >
                        Chat
                      </Button>
                    )}
                  </VStack>
                </Box>
              ))}
            </VStack>
          )}
        </Box>

        <Divider borderColor="whiteAlpha.300" />

        {/* Session Control */}
        <Box>
          <Heading size="md" color="white" mb={4} fontWeight="bold">
            Session Control
          </Heading>
          <VStack spacing={4} align="stretch">
            <Button
              colorScheme="red"
              variant="outline"
              onClick={handleNewSession}
              size="sm"
              _hover={{ transform: "translateY(-1px)" }}
              borderRadius="lg"
            >
              Start New Session
            </Button>

            <Box
              bg="linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)"
              borderRadius="lg"
              p={4}
              border="1px solid"
              borderColor="whiteAlpha.200"
            >
              <Text color="white" fontSize="sm" mb={3} fontWeight="semibold">
                Current Session ID:
              </Text>
              <Code
                colorScheme="gray"
                p={3}
                borderRadius="md"
                fontSize="xs"
                wordBreak="break-all"
                bg="whiteAlpha.100"
                color="white"
                display="block"
                whiteSpace="pre-wrap"
              >
                {session_id}
              </Code>
              <Text color="whiteAlpha.600" fontSize="xs" mt={2} fontWeight="medium">
                Copy this ID to resume your PRISM session later.
              </Text>
            </Box>

            {/* Resume Session Form */}
            <Box
              bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
              borderRadius="lg"
              p={4}
              border="1px solid"
              borderColor="whiteAlpha.200"
              backdropFilter="blur(20px)"
              boxShadow="0 4px 16px rgba(0,0,0,0.1)"
              position="relative"
              zIndex={2}
              _hover={{
                boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
                borderColor: "whiteAlpha.300",
                transform: "translateY(-2px)",
              }}
              transition="all 0.3s ease"
            >
              <Text 
                color="white" 
                fontSize="sm" 
                mb={3}
                fontWeight="semibold"
                bgGradient="linear(135deg, prismTeal.300 0%, brand.300 100%)"
                bgClip="text"
              >
                🔄 Resume Session
              </Text>
              <VStack spacing={3} align="stretch">
                <Input
                  placeholder="Paste session ID here"
                  value={resumeSessionId}
                  onChange={(e) => setResumeSessionId(e.target.value)}
                  variant="modern"
                  size="sm"
                  _placeholder={{ color: "whiteAlpha.600" }}
                />
                <Button
                  onClick={handleResumeSession}
                  bg="linear-gradient(135deg, prismTeal.500 0%, prismTeal.400 100%)"
                  color="white"
                  size="sm"
                  borderRadius="lg"
                  fontWeight="semibold"
                  boxShadow="0 4px 12px rgba(20,184,166,0.3)"
                  border="1px solid"
                  borderColor="prismTeal.400"
                  isDisabled={!resumeSessionId}
                  _hover={{ 
                    transform: "translateY(-1px) scale(1.02)",
                    boxShadow: "0 6px 16px rgba(20,184,166,0.4)",
                    bg: "linear-gradient(135deg, prismTeal.400 0%, prismTeal.300 100%)",
                  }}
                  _active={{
                    transform: "translateY(0) scale(0.98)",
                  }}
                  transition="all 0.3s ease"
                >
                  Resume Session
                </Button>
              </VStack>
            </Box>
          </VStack>
      </Box>
      </VStack>
    </Box>
  );
}