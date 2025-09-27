import { Box, Button, Flex, Spinner, Textarea } from "@chakra-ui/react";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  loading?: boolean;
  placeholder?: string;
  disabled?: boolean;
}

export default function ChatInput({ 
  value, 
  onChange, 
  onSend, 
  loading = false, 
  placeholder = "Type your message...",
  disabled = false
}: ChatInputProps) {
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!loading && value.trim()) {
        onSend();
      }
    }
  };

  return (
    <Box 
      bg="linear-gradient(135deg, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.06) 100%)"
      borderRadius="xl"
      p={4}
      border="1px solid"
      borderColor="whiteAlpha.300"
      backdropFilter="blur(20px)"
      boxShadow="0 8px 32px rgba(0,0,0,0.15)"
      position="relative"
      _before={{
        content: '""',
        position: "absolute",
        top: "-1px",
        left: "0",
        right: "0",
        height: "1px",
        background: "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%)",
      }}
    >
      <Flex gap={3} align="end">
        <Textarea 
          placeholder={placeholder}
          value={value} 
          onChange={(e) => onChange(e.target.value)}
          onKeyPress={handleKeyPress}
          variant="unstyled"
          resize="none"
          rows={3}
          flex="1"
          bg="transparent"
          color="white"
          _placeholder={{ 
            color: "whiteAlpha.600",
            fontSize: "sm"
          }}
          fontSize="sm"
          lineHeight="1.5"
          border="none"
          _focus={{
            outline: "none",
            boxShadow: "none",
          }}
          _hover={{
            outline: "none",
            boxShadow: "none",
          }}
        />
        <Button 
          onClick={onSend} 
          isDisabled={!value.trim() || loading || disabled}
          minW="120px"
          size="lg"
          variant="solid"
          borderRadius="lg"
          bg="linear-gradient(135deg, brand.500 0%, brand.400 100%)"
          color="white"
          fontWeight="semibold"
          _hover={{ 
            transform: "translateY(-2px)",
            boxShadow: "0 8px 25px rgba(132,64,255,0.4)",
            bg: "linear-gradient(135deg, brand.600 0%, brand.500 100%)"
          }}
          _active={{
            transform: "translateY(0px)",
          }}
          transition="all 0.2s ease"
          boxShadow="0 4px 16px rgba(132,64,255,0.3)"
        >
          {loading ? (
            <Flex align="center" gap={2}>
              <Spinner size="sm" />
              <Text fontSize="sm">Sending...</Text>
            </Flex>
          ) : (
            <Flex align="center" gap={2}>
              <Text>Send</Text>
              <Text fontSize="lg">🚀</Text>
            </Flex>
          )}
        </Button>
      </Flex>
      
      {/* Subtle hint */}
      <Text 
        fontSize="xs" 
        color="whiteAlpha.500" 
        mt={2} 
        textAlign="center"
        fontStyle="italic"
      >
        Press Enter to send, Shift+Enter for new line
      </Text>
    </Box>
  );
}
