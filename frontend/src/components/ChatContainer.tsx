import { Box, Flex, Heading, Text, Button, Spinner } from "@chakra-ui/react";
import { ReactNode } from "react";
import { FiDownload } from "react-icons/fi";

interface ChatContainerProps {
  title: string;
  subtitle: string;
  children: ReactNode;
  icon?: string;
  showExportButton?: boolean;
  onExport?: () => void;
  isExporting?: boolean;
}

export default function ChatContainer({ 
  title, 
  subtitle, 
  children, 
  icon = "💬", 
  showExportButton = false, 
  onExport, 
  isExporting = false 
}: ChatContainerProps) {
  return (
    <Flex direction="column" gap={6} h="full">
      {/* Header */}
      <Box 
        bg="linear-gradient(135deg, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.06) 100%)"
        borderRadius="xl"
        p={6}
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
        <Flex justify="space-between" align="center" mb={2}>
          <Heading size="lg" color="white" fontWeight="bold">
            {icon} {title}
          </Heading>
          {showExportButton && onExport && (
            <Button
              onClick={onExport}
              isLoading={isExporting}
              loadingText="Exporting..."
              leftIcon={<FiDownload />}
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
              Export Report
            </Button>
          )}
        </Flex>
        <Text color="whiteAlpha.700" fontSize="sm" fontWeight="medium">
          {subtitle}
        </Text>
      </Box>

      {/* Chat Content */}
      {children}
    </Flex>
  );
}
