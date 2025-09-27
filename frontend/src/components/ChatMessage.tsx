import { Box, Flex, Image, Text, Avatar, VStack, Accordion, AccordionItem, AccordionButton, AccordionPanel, AccordionIcon } from "@chakra-ui/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { getPlotUrl } from "../api/client";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  plot_path?: string;
  step_log?: string[];
  sources?: any[];
  timestamp?: string;
}

export default function ChatMessage({ 
  role, 
  content, 
  plot_path, 
  step_log, 
  sources, 
  timestamp 
}: ChatMessageProps) {
  const isAssistant = role === "assistant";
  
  return (
    <Flex 
      mb={6} 
      justifyContent={isAssistant ? "flex-start" : "flex-end"}
      alignItems="flex-start"
      gap={3}
    >
      {/* Avatar */}
      {isAssistant && (
        <Avatar
          size="sm"
          src="/prism_logo.png"
          bg="transparent"
          border="2px solid"
          borderColor="prismTeal.400"
          boxShadow="0 0 20px rgba(20,184,166,0.3)"
        />
      )}
      
      {/* Message Content */}
      <Box
        maxW="75%"
        minW="200px"
        bg={isAssistant 
          ? "linear-gradient(135deg, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.06) 100%)"
          : "linear-gradient(135deg, brand.500 0%, brand.400 100%)"
        }
        color="white"
        p={4}
        borderRadius={isAssistant ? "20px 20px 20px 8px" : "20px 20px 8px 20px"}
        border="1px solid"
        borderColor={isAssistant ? "whiteAlpha.300" : "brand.400"}
        backdropFilter="blur(20px)"
        boxShadow={isAssistant 
          ? "0 8px 32px rgba(0,0,0,0.15)"
          : "0 8px 32px rgba(132,64,255,0.4)"
        }
        position="relative"
        _before={isAssistant ? {
          content: '""',
          position: "absolute",
          bottom: "-8px",
          left: "20px",
          width: "0",
          height: "0",
          borderLeft: "8px solid transparent",
          borderRight: "8px solid transparent",
          borderTop: "8px solid rgba(255,255,255,0.12)",
        } : {
          content: '""',
          position: "absolute",
          bottom: "-8px",
          right: "20px",
          width: "0",
          height: "0",
          borderLeft: "8px solid transparent",
          borderRight: "8px solid transparent",
          borderTop: "8px solid #8440ff",
        }}
      >
        {/* Message Header */}
        <Flex align="center" gap={2} mb={3}>
          <Text 
            fontSize="sm" 
            fontWeight="bold"
            color={isAssistant ? "prismTeal.300" : "white"}
          >
            {isAssistant ? "🔮 Prism" : "👤 You"}
          </Text>
          {timestamp && (
            <Text fontSize="xs" color="whiteAlpha.600" ml="auto">
              {timestamp}
            </Text>
          )}
        </Flex>

        {/* Message Content */}
        <Box>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {content}
          </ReactMarkdown>
        </Box>

        {/* Plot Visualization */}
        {plot_path && (
          <Box 
            mt={4} 
            p={4} 
            bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
            borderRadius="lg" 
            border="1px solid" 
            borderColor="whiteAlpha.300"
            backdropFilter="blur(20px)"
            boxShadow="0 4px 16px rgba(0,0,0,0.1)"
          >
            <Text fontSize="sm" color="prismTeal.300" mb={3} fontWeight="semibold">
              📊 Generated Visualization
            </Text>
            <Image 
              src={getPlotUrl(plot_path)} 
              alt="Generated plot" 
              maxH="400px" 
              objectFit="contain"
              borderRadius="lg"
              border="1px solid"
              borderColor="whiteAlpha.400"
              boxShadow="0 4px 16px rgba(0,0,0,0.1)"
              onError={(e) => {
                console.error('❌ Image load error:', e);
                console.error('Failed URL:', getPlotUrl(plot_path));
              }}
              onLoad={() => {
                console.log('✅ Image loaded successfully:', getPlotUrl(plot_path));
              }}
            />
          </Box>
        )}

        {/* Step Log */}
        {step_log && step_log.length > 0 && (
          <Box mt={4}>
            <Accordion allowToggle>
              <AccordionItem border="none">
                <AccordionButton 
                  px={0} 
                  py={2} 
                  _hover={{ bg: "transparent" }}
                  bg="linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.04) 100%)"
                  borderRadius="lg"
                  border="1px solid"
                  borderColor="whiteAlpha.200"
                >
                  <Box flex="1" textAlign="left">
                    <Text fontSize="sm" fontWeight="semibold" color="prismTeal.300">
                      🔍 Prism Activity ({step_log.length} steps)
                    </Text>
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
                <AccordionPanel px={0} pb={0} mt={2}>
                  <Box 
                    bg="linear-gradient(135deg, rgba(0,0,0,0.15) 0%, rgba(0,0,0,0.08) 100%)" 
                    p={4} 
                    borderRadius="lg" 
                    border="1px solid" 
                    borderColor="whiteAlpha.200"
                    backdropFilter="blur(20px)"
                  >
                    <VStack align="stretch" spacing={3}>
                      {step_log.map((step, i) => (
                        <Box 
                          key={i} 
                          p={3} 
                          bg="linear-gradient(135deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.05) 100%)" 
                          borderRadius="md" 
                          borderLeft="3px solid" 
                          borderLeftColor="prismTeal.400"
                          boxShadow="0 2px 8px rgba(0,0,0,0.1)"
                        >
                          <Text fontSize="xs" color="whiteAlpha.800" fontFamily="mono" lineHeight="1.4">
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

        {/* Sources */}
        {sources && sources.length > 0 && (
          <Box mt={4}>
            <Accordion allowToggle>
              <AccordionItem border="none">
                <AccordionButton 
                  px={0} 
                  py={2} 
                  _hover={{ bg: "transparent" }}
                  bg="linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.04) 100%)"
                  borderRadius="lg"
                  border="1px solid"
                  borderColor="whiteAlpha.200"
                >
                  <Box flex="1" textAlign="left">
                    <Text fontSize="sm" fontWeight="semibold" color="prismTeal.300">
                      📚 Sources ({sources.length} documents)
                    </Text>
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
                <AccordionPanel px={0} pb={0} mt={2}>
                  <Box 
                    bg="linear-gradient(135deg, rgba(0,0,0,0.15) 0%, rgba(0,0,0,0.08) 100%)" 
                    p={4} 
                    borderRadius="lg" 
                    border="1px solid" 
                    borderColor="whiteAlpha.200"
                    backdropFilter="blur(20px)"
                  >
                    <VStack align="stretch" spacing={3}>
                      {sources.map((source, i) => (
                        <Box 
                          key={i} 
                          p={3} 
                          bg="linear-gradient(135deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.05) 100%)" 
                          borderRadius="md" 
                          borderLeft="3px solid" 
                          borderLeftColor="prismTeal.400"
                          boxShadow="0 2px 8px rgba(0,0,0,0.1)"
                        >
                          <Text fontSize="sm" fontWeight="medium" color="prismTeal.200" mb={1}>
                            📄 Source {i+1}: {source.document_name ?? 'Unknown Document'}
                          </Text>
                          <Text fontSize="xs" color="whiteAlpha.700" fontFamily="mono" whiteSpace="pre-wrap">
                            {source.content_snippet ?? 'No content snippet available'}
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

      {/* User Avatar */}
      {!isAssistant && (
        <Avatar
          size="sm"
          name="User"
          bg="brand.500"
          color="white"
          border="2px solid"
          borderColor="brand.400"
          boxShadow="0 0 20px rgba(132,64,255,0.3)"
        />
      )}
    </Flex>
  );
}
