import { useState, useEffect } from "react";
import { 
  Box, 
  Flex, 
  Text, 
  Image, 
  Button, 
  VStack,
  HStack,
  useColorModeValue
} from "@chakra-ui/react";
import { motion, AnimatePresence } from "framer-motion";
import { FiZap, FiTrendingUp, FiCpu, FiDatabase } from "react-icons/fi";

const MotionBox = motion(Box);
const MotionText = motion(Text);
const MotionButton = motion(Button);

interface SplashScreenProps {
  onEnter: () => void;
}

export default function SplashScreen({ onEnter }: SplashScreenProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    // Initial load animation
    const timer1 = setTimeout(() => setIsLoaded(true), 500);
    const timer2 = setTimeout(() => setShowContent(true), 1000);
    
    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
  }, []);

  return (
    <Box
      position="fixed"
      top={0}
      left={0}
      right={0}
      bottom={0}
      bg="linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)"
      backgroundImage="
        radial-gradient(ellipse 1200px 400px at 10% 0%, rgba(132,64,255,0.15) 0%, transparent 60%),
        radial-gradient(ellipse 800px 300px at 90% 0%, rgba(20,184,166,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 600px 200px at 50% 100%, rgba(255,26,107,0.08) 0%, transparent 70%),
        radial-gradient(ellipse 400px 150px at 30% 50%, rgba(255,193,7,0.06) 0%, transparent 80%)
      "
      backgroundAttachment="fixed"
      zIndex={9999}
      overflow="hidden"
    >
      {/* Animated background particles */}
      <Box
        position="absolute"
        top={0}
        left={0}
        right={0}
        bottom={0}
        background="
          radial-gradient(circle at 20% 20%, rgba(132,64,255,0.08) 0%, transparent 50%),
          radial-gradient(circle at 80% 80%, rgba(20,184,166,0.06) 0%, transparent 50%),
          radial-gradient(circle at 40% 60%, rgba(255,26,107,0.04) 0%, transparent 50%)
        "
        pointerEvents="none"
      />

      <Flex
        height="100vh"
        direction="column"
        align="center"
        justify="center"
        position="relative"
        zIndex={1}
      >
        <AnimatePresence>
          {isLoaded && (
            <MotionBox
              initial={{ scale: 0, opacity: 0, rotate: -180 }}
              animate={{ scale: 1, opacity: 1, rotate: 0 }}
              transition={{ 
                duration: 1.2, 
                type: "spring", 
                stiffness: 100,
                damping: 15
              }}
              whileHover={{ 
                scale: 1.1, 
                rotate: 5,
                transition: { duration: 0.3 }
              }}
            >
              <Image
                src="/prism_logo.png?v=2"
                alt="PRISM"
                boxSize={{ base: "120px", md: "160px", lg: "200px" }}
                borderRadius="full"
                boxShadow="0 0 60px rgba(132,64,255,0.6), 0 0 120px rgba(132,64,255,0.4), 0 0 180px rgba(132,64,255,0.2)"
                border="4px solid"
                borderColor="brand.400"
                filter="drop-shadow(0 0 30px rgba(132,64,255,0.5))"
              />
            </MotionBox>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {showContent && (
            <VStack spacing={8} mt={12}>
              <MotionText
                initial={{ y: 50, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.8, delay: 0.5 }}
                fontSize={{ base: "3xl", md: "4xl", lg: "5xl" }}
                fontWeight="extrabold"
                bgGradient="linear(135deg, brand.300 0%, prismTeal.300 50%, accent.300 100%)"
                bgClip="text"
                textShadow="0 0 30px rgba(132,64,255,0.3)"
                letterSpacing="wider"
                textAlign="center"
              >
                PRISM
              </MotionText>
              <MotionText
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.8, delay: 1.1 }}
                fontSize="md"
                color="whiteAlpha.600"
                textAlign="center"
                maxW="500px"
                px={4}
                lineHeight="1.0"
              >
                Predicting & Reporting Insights with Scalable Models
              </MotionText>

              <MotionText
                initial={{ y: 30, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.8, delay: 0.8 }}
                fontSize={{ base: "lg", md: "xl" }}
                color="whiteAlpha.700"
                fontWeight="medium"
                textAlign="center"
                maxW="600px"
                px={4}
              >
                Next Gen AI-Powered Data Intelligence Platform
              </MotionText>

              <MotionText
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.8, delay: 1.1 }}
                fontSize="md"
                color="whiteAlpha.600"
                textAlign="center"
                maxW="500px"
                px={4}
                lineHeight="1.6"
              >
                Transform your data into actionable insights with cutting-edge AI technology
              </MotionText>

              {/* Feature icons */}
              <MotionBox
                initial={{ y: 30, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.8, delay: 1.4 }}
              >
                <HStack spacing={8} justify="center" wrap="wrap">
                  <VStack spacing={2}>
                    <Box
                      p={3}
                      borderRadius="full"
                      bg="linear-gradient(135deg, prismTeal.500 0%, prismTeal.400 100%)"
                      boxShadow="0 4px 20px rgba(20,184,166,0.3)"
                    >
                      <FiTrendingUp size={24} color="white" />
                    </Box>
                    <Text fontSize="sm" color="whiteAlpha.700" fontWeight="medium">
                      Insights
                    </Text>
                  </VStack>
                  
                  <VStack spacing={2}>
                    <Box
                      p={3}
                      borderRadius="full"
                      bg="linear-gradient(135deg, brand.500 0%, brand.400 100%)"
                      boxShadow="0 4px 20px rgba(132,64,255,0.3)"
                    >
                      <FiCpu size={24} color="white" />
                    </Box>
                    <Text fontSize="sm" color="whiteAlpha.700" fontWeight="medium">
                      Modeling
                    </Text>
                  </VStack>
                  
                  <VStack spacing={2}>
                    <Box
                      p={3}
                      borderRadius="full"
                      bg="linear-gradient(135deg, accent.500 0%, accent.400 100%)"
                      boxShadow="0 4px 20px rgba(255,26,107,0.3)"
                    >
                      <FiDatabase size={24} color="white" />
                    </Box>
                    <Text fontSize="sm" color="whiteAlpha.700" fontWeight="medium">
                      AutoRAG
                    </Text>
                  </VStack>
                </HStack>
              </MotionBox>

              {/* Let's Go Button */}
              <MotionButton
                initial={{ y: 30, opacity: 0, scale: 0.8 }}
                animate={{ y: 0, opacity: 1, scale: 1 }}
                transition={{ duration: 0.8, delay: 1.7 }}
                whileHover={{ 
                  scale: 1.05,
                  boxShadow: "0 8px 32px rgba(132,64,255,0.4)",
                  transition: { duration: 0.2 }
                }}
                whileTap={{ scale: 0.95 }}
                onClick={() => {
                  // Navigate to About page instead of entering main app
                  window.location.href = '/about';
                }}
                size="lg"
                bg="linear-gradient(135deg, brand.500 0%, brand.400 50%, brand.300 100%)"
                color="white"
                px={12}
                py={6}
                borderRadius="xl"
                fontSize="lg"
                fontWeight="bold"
                boxShadow="0 8px 32px rgba(132,64,255,0.3)"
                border="2px solid"
                borderColor="brand.400"
                _hover={{
                  bg: "linear-gradient(135deg, brand.400 0%, brand.300 50%, brand.200 100%)",
                  transform: "translateY(-2px)",
                }}
                _active={{
                  bg: "linear-gradient(135deg, brand.600 0%, brand.500 50%, brand.400 100%)",
                  transform: "translateY(0)",
                }}
                leftIcon={<FiZap size={20} />}
              >
                Features
              </MotionButton>
            </VStack>
          )}
        </AnimatePresence>
      </Flex>
    </Box>
  );
}
