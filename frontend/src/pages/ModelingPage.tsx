import { useState } from "react";
import { Box, Button, Code, Flex, Heading, Spinner, Tab, TabList, TabPanel, TabPanels, Tabs, Text, Textarea, useToast, Select, Image } from "@chakra-ui/react";
import { useAppStore, setModeling } from "../state/appStore";
import { startModelingPipeline, executeModelingPipeline, getArtifactUrl, downloadFile, getPlotUrl } from "../api/client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function ModelingPage() {
  const toast = useToast();
  const { session_id, sources, modeling } = useAppStore();
  const [selected, setSelected] = useState<string | null>(modeling.source_name);
  const [task, setTask] = useState(modeling.task);
  const [loading, setLoading] = useState(false);
  const [execLoading, setExecLoading] = useState(false);

  const analyzedSources = Object.entries(sources).filter(([_, v]) => v.analyzed).map(([k]) => k);

  async function generate() {
    if (!selected || !task) {
      toast({ 
        status: "warning", 
        title: "Missing information",
        description: "Please select a data source and enter a modeling objective."
      });
      return;
    }
    
    setLoading(true);
    try {
      const source_info = sources[selected];
      
      console.log("Generating ML pipeline with:", { session_id, task, config: source_info.config, data_context: source_info.data_context });
      const result = await startModelingPipeline(session_id, task, source_info.config, source_info.data_context);
      
      console.log("Generation response:", result);
      
      // Save to global state for persistence
      setModeling({
        source_name: selected,
        task: task,
        generated_code: result.generated_code,
        requirements_txt: result.requirements_txt,
        readme_md: result.readme_md,
        step_log: result.step_log || [],
        download_path: result.download_path || null,
      });
      
      toast({ 
        status: "success", 
        title: "ML Pipeline Generated!",
        description: "Review the generated code and proceed to execution."
      });
    } catch (e: any) {
      console.error("Generation error:", e);
      toast({ 
        status: "error", 
        title: "Generation failed",
        description: e?.response?.data?.detail ?? String(e)
      });
    } finally {
      setLoading(false);
    }
  }

  async function execute() {
    setExecLoading(true);
    try {
      const result = await executeModelingPipeline(session_id);
      
      // Save execution results to global state
      setModeling({
        execution_results: {
          execution_log: result.execution_log || "",
          artifacts: result.artifacts || {},
          step_log: result.step_log || [],
          plots: result.plots || []
        },
      });
      
      toast({ 
        status: "success", 
        title: "Pipeline executed successfully!",
        description: "Check the results and artifacts below."
      });
    } catch (e: any) {
      console.error("Execution error:", e);
      toast({ 
        status: "error", 
        title: "Execution failed",
        description: e?.response?.data?.detail ?? String(e)
      });
    } finally {
      setExecLoading(false);
    }
  }

  return (
    <Flex direction="column" gap={6}>
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
        <Heading size="lg" color="white" mb={2} fontWeight="bold">
          🤖 Generate an ML Pipeline
        </Heading>
        <Text color="whiteAlpha.700" fontSize="sm" fontWeight="medium">
          Create custom machine learning pipelines for your data
        </Text>
      </Box>

      {analyzedSources.length === 0 ? (
        <Box 
          bg="linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)"
          borderRadius="lg"
          p={6}
          border="1px solid"
          borderColor="whiteAlpha.200"
          textAlign="center"
        >
          <Text color="whiteAlpha.600" fontSize="sm" fontWeight="medium">
            Analyze at least one data source first to generate ML pipelines.
          </Text>
        </Box>
      ) : (
        <Box 
          bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
          borderRadius="xl"
          p={6}
          border="1px solid"
          borderColor="whiteAlpha.200"
          backdropFilter="blur(20px)"
          boxShadow="0 4px 16px rgba(0,0,0,0.1)"
        >
          <Box mb={4}>
            <Text color="white" fontSize="sm" fontWeight="semibold" mb={2}>Select Data Source</Text>
            <Select 
              placeholder="Select Source" 
              value={selected ?? ""} 
              onChange={(e) => setSelected(e.target.value)}
              variant="modern"
              size="lg"
            >
              {analyzedSources.map((name) => (
                <option key={name} value={name}>{name}</option>
              ))}
            </Select>
          </Box>
          <Box mb={6}>
            <Text color="white" fontSize="sm" fontWeight="semibold" mb={2}>Modeling Objective</Text>
            <Textarea 
              placeholder="Describe your modeling objective" 
              value={task} 
              onChange={(e) => setTask(e.target.value)}
              variant="modern"
              rows={4}
            />
          </Box>
          <Button 
            onClick={generate} 
            isDisabled={!selected || !task || loading} 
            size="lg"
            variant="solid"
            borderRadius="lg"
            _hover={{ transform: "translateY(-1px)" }}
          >
            {loading ? <Spinner size="sm" /> : "Generate ML Pipeline"}
          </Button>
        </Box>
      )}

      {modeling.generated_code && (
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
            📋 Review and Execute Pipeline
          </Heading>
          <Tabs variant="enclosed" colorScheme="teal">
            <TabList 
              bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
              borderRadius="lg"
              p={1}
              border="1px solid"
              borderColor="whiteAlpha.200"
              backdropFilter="blur(20px)"
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
                pipeline.py
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
                requirements.txt
              </Tab>
              <Tab 
                borderRadius="md"
                fontWeight="semibold"
                fontSize="sm"
                _selected={{ 
                  bg: "linear-gradient(135deg, accent.500 0%, accent.400 100%)",
                  color: "white",
                  boxShadow: "0 4px 12px rgba(255,26,107,0.3)",
                  transform: "translateY(-1px)",
                }}
                transition="all 0.3s ease"
              >
                README.md
              </Tab>
            </TabList>
            <TabPanels mt={4}>
              <TabPanel px={0} py={4}>
                <Box 
                  bg="linear-gradient(135deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.05) 100%)"
                  borderRadius="lg"
                  p={4}
                  border="1px solid"
                  borderColor="whiteAlpha.200"
                  backdropFilter="blur(20px)"
                >
                  <pre style={{ 
                    color: "white", 
                    fontFamily: "mono", 
                    fontSize: "12px", 
                    lineHeight: "1.4",
                    overflow: "auto",
                    whiteSpace: "pre-wrap"
                  }}>
                    <code>{modeling.generated_code}</code>
                  </pre>
                </Box>
              </TabPanel>
              <TabPanel px={0} py={4}>
                <Box 
                  bg="linear-gradient(135deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.05) 100%)"
                  borderRadius="lg"
                  p={4}
                  border="1px solid"
                  borderColor="whiteAlpha.200"
                  backdropFilter="blur(20px)"
                >
                  <pre style={{ 
                    color: "white", 
                    fontFamily: "mono", 
                    fontSize: "12px", 
                    lineHeight: "1.4",
                    overflow: "auto",
                    whiteSpace: "pre-wrap"
                  }}>
                    <code>{modeling.requirements_txt}</code>
                  </pre>
                </Box>
              </TabPanel>
              <TabPanel px={0} py={4}>
                <Box 
                  bg="linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%)"
                  borderRadius="lg"
                  p={6}
                  border="1px solid"
                  borderColor="whiteAlpha.200"
                  backdropFilter="blur(20px)"
                >
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {modeling.readme_md}
                  </ReactMarkdown>
                </Box>
              </TabPanel>
            </TabPanels>
          </Tabs>
          <Flex mt={6} gap={4} flexWrap="wrap">
            {modeling.download_path && (
              <Button 
                onClick={() => {
                  const url = getArtifactUrl(modeling.download_path || '');
                  downloadFile(url, `${session_id}_pipeline.zip`);
                }}
                colorScheme="blue"
                variant="outline"
                size="lg"
                borderRadius="lg"
                _hover={{ transform: "translateY(-1px)" }}
              >
                📦 Download Project as .zip
              </Button>
            )}
            <Button 
              onClick={execute} 
              isDisabled={execLoading} 
              size="lg"
              variant="solid"
              borderRadius="lg"
              _hover={{ transform: "translateY(-1px)" }}
            >
              {execLoading ? <Spinner size="sm" /> : "Proceed to Execute & Train Model"}
            </Button>
          </Flex>
        </Box>
      )}

      {modeling.execution_results && (
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
            📊 View Results and Artifacts
          </Heading>
          <Box 
            bg="linear-gradient(135deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.05) 100%)"
            borderRadius="lg"
            p={4}
            border="1px solid"
            borderColor="whiteAlpha.200"
            backdropFilter="blur(20px)"
            mb={6}
          >
            <Textarea 
              value={modeling.execution_results.execution_log ?? ""} 
              readOnly 
              height="300px"
              variant="modern"
              fontFamily="mono"
              fontSize="sm"
            />
          </Box>
          
          {/* Display plots if they exist - check for plots in artifacts */}
          {modeling.execution_results.artifacts && Object.keys(modeling.execution_results.artifacts).some(key => key.endsWith('.png') || key.endsWith('.jpg') || key.endsWith('.jpeg')) && (
            <Box mb={6}>
              <Heading size="md" mb={4} color="prismTeal.300" fontWeight="bold">📊 Generated Plots</Heading>
              <Flex direction="column" gap={4}>
                {Object.entries(modeling.execution_results.artifacts)
                  .filter(([name, _]) => name.endsWith('.png') || name.endsWith('.jpg') || name.endsWith('.jpeg'))
                  .map(([name, path], index) => (
                  <Box 
                    key={index} 
                    bg="linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%)"
                    p={4} 
                    borderRadius="lg" 
                    border="1px solid" 
                    borderColor="whiteAlpha.200"
                    backdropFilter="blur(20px)"
                    boxShadow="0 2px 8px rgba(0,0,0,0.1)"
                  >
                    <Text fontSize="sm" color="prismTeal.300" mb={3} fontWeight="semibold">
                      📈 Plot {index + 1}: {name}
                    </Text>
                    <Image 
                      src={getArtifactUrl(path as string)} 
                      alt={`Generated plot ${index + 1}`} 
                      maxH="500px" 
                      objectFit="contain"
                      borderRadius="lg"
                      border="1px solid"
                      borderColor="whiteAlpha.300"
                      boxShadow="0 4px 12px rgba(0,0,0,0.1)"
                      onError={(e) => {
                        console.error('❌ Plot load error:', e);
                        console.error('Failed URL:', getArtifactUrl(path as string));
                      }}
                      onLoad={() => {
                        console.log('✅ Plot loaded successfully:', getArtifactUrl(path as string));
                      }}
                    />
                  </Box>
                ))}
              </Flex>
            </Box>
          )}
          
          {modeling.execution_results.artifacts && Object.keys(modeling.execution_results.artifacts).length > 0 ? (
            <Box 
              bg="linear-gradient(135deg, rgba(34,197,94,0.1) 0%, rgba(34,197,94,0.05) 100%)"
              borderRadius="lg"
              p={4}
              border="1px solid"
              borderColor="green.300"
              backdropFilter="blur(20px)"
            >
              <Text color="green.300" mb={4} fontWeight="semibold">✅ Model and metrics saved successfully!</Text>
              <Flex gap={3} flexWrap="wrap">
                {Object.entries(modeling.execution_results.artifacts).map(([name, path]) => (
                  <Button
                    key={name}
                    size="md"
                    colorScheme="green"
                    variant="outline"
                    borderRadius="lg"
                    _hover={{ transform: "translateY(-1px)" }}
                    onClick={() => {
                      const url = getArtifactUrl(path as string);
                      downloadFile(url, name);
                    }}
                  >
                    📥 Download {name}
                  </Button>
                ))}
              </Flex>
            </Box>
          ) : (
            <Box 
              bg="linear-gradient(135deg, rgba(239,68,68,0.1) 0%, rgba(239,68,68,0.05) 100%)"
              borderRadius="lg"
              p={4}
              border="1px solid"
              borderColor="red.300"
              backdropFilter="blur(20px)"
            >
              <Text color="red.300" fontWeight="semibold">
                ⚠️ Execution finished, but no artifacts were found. Check the log for details.
              </Text>
            </Box>
          )}
        </Box>
      )}
    </Flex>
  );
}
