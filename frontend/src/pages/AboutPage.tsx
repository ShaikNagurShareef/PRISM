import { 
  Box, 
  Flex, 
  Text, 
  Image, 
  VStack, 
  HStack, 
  Heading, 
  Button,
  Container,
  SimpleGrid,
  Icon,
  useColorModeValue,
  IconButton
} from "@chakra-ui/react";
import { motion } from "framer-motion";
import { 
  FiTrendingUp, 
  FiCpu, 
  FiDatabase, 
  FiZap, 
  FiBarChart, 
  FiActivity,
  FiShield,
  FiPocket,
  FiTarget,
  FiLayers,
  FiGlobe,
  FiArrowRight,
  FiArrowLeft
} from "react-icons/fi";
import { useNavigate } from "react-router-dom";

const MotionBox = motion(Box);
const MotionText = motion(Text);
const MotionHeading = motion(Heading);

export default function AboutPage() {
  const navigate = useNavigate();

  const features = [
    {
      icon: FiTrendingUp,
      title: "AI-Powered Insights",
      description: "Transform raw data into actionable insights with cutting-edge AI algorithms",
      color: "prismTeal.400",
      bgGradient: "linear(135deg, prismTeal.500 0%, prismTeal.300 100%)"
    },
    {
      icon: FiCpu,
      title: "Sandbox Environment",
      description: "Automated ML pipeline generation and execution within sandbox environments",
      color: "brand.400",
      bgGradient: "linear(135deg, brand.500 0%, brand.300 100%)"
    },
    {
      icon: FiDatabase,
      title: "AutoRAG Management System",
      description: "Advanced Retrieval-Augmented Generation for intelligent data queries",
      color: "accent.400",
      bgGradient: "linear(135deg, accent.500 0%, accent.300 100%)"
    },
    {
      icon: FiDatabase,
      title: "AutoVector DB",
      description: "Seamless connection to PostgreSQL, MySQL, SQLite with automatic schema detection",
      color: "cyan.400",
      bgGradient: "linear(135deg, cyan.500 0%, cyan.300 100%)"
    },
    {
      icon: FiCpu,
      title: "Auto-Configurable Models",
      description: "Intelligent model selection and hyperparameter tuning for optimal performance",
      color: "pink.400",
      bgGradient: "linear(135deg, pink.500 0%, pink.300 100%)"
    },
    {
      icon: FiActivity,
      title: "Intelligent Analysis",
      description: "Deep learning models that understand your data patterns and trends",
      color: "purple.400",
      bgGradient: "linear(135deg, purple.500 0%, purple.300 100%)"
    },
    {
      icon: FiShield,
      title: "Secure & Private",
      description: "Enterprise-grade security with complete data privacy protection",
      color: "green.400",
      bgGradient: "linear(135deg, green.500 0%, green.300 100%)"
    },
    {
      icon: FiPocket,
      title: "Lightning Fast",
      description: "Optimized performance with real-time processing capabilities",
      color: "orange.400",
      bgGradient: "linear(135deg, orange.500 0%, orange.300 100%)"
    },
    
  ];

  const stats = [
    { label: "Data Sources", value: "Unlimited", icon: FiDatabase },
    { label: "AI Models", value: "30+", icon: FiActivity },
    { label: "Developement Speed", value: "10x Faster", icon: FiZap },
    { label: "Execution Accuracy", value: "99.9%", icon: FiTarget }
  ];

  return (
    <Box minH="100vh" bg="gray.900" position="relative" overflow="hidden">
      {/* Back Button */}
      <MotionBox
        position="fixed"
        top={6}
        left={6}
        zIndex={10}
        initial={{ x: -50, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <IconButton
          aria-label="Back to app"
          icon={<FiArrowLeft />}
          size="lg"
          borderRadius="full"
          bg="linear-gradient(135deg, brand.500 0%, brand.400 100%)"
          color="white"
          boxShadow="0 8px 32px rgba(132,64,255,0.3)"
          border="2px solid"
          borderColor="brand.400"
          _hover={{
            bg: "linear-gradient(135deg, brand.400 0%, brand.300 100%)",
            transform: "translateY(-2px)",
            boxShadow: "0 12px 40px rgba(132,64,255,0.4)"
          }}
          _active={{
            transform: "translateY(0)"
          }}
          onClick={() => navigate("/insights")}
        />
      </MotionBox>

      {/* Background Effects */}
      <Box
        position="absolute"
        top={0}
        left={0}
        right={0}
        bottom={0}
        backgroundImage="
          radial-gradient(ellipse 1200px 400px at 10% 0%, rgba(132,64,255,0.15) 0%, transparent 60%),
          radial-gradient(ellipse 800px 300px at 90% 0%, rgba(20,184,166,0.12) 0%, transparent 60%),
          radial-gradient(ellipse 600px 200px at 50% 100%, rgba(255,26,107,0.08) 0%, transparent 70%),
          radial-gradient(ellipse 400px 150px at 30% 50%, rgba(255,193,7,0.06) 0%, transparent 80%)
        "
        backgroundAttachment="fixed"
        pointerEvents="none"
        zIndex={0}
      />

      <Container maxW="1400px" position="relative" zIndex={1} py={20}>
        {/* Header Section */}
        <VStack spacing={8} mb={20} textAlign="center">
          <MotionBox
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, type: "spring" }}
          >
            <Image
              src="/prism_logo.png?v=2"
              alt="PRISM"
              boxSize={{ base: "120px", md: "160px", lg: "200px" }}
              borderRadius="full"
              boxShadow="0 0 60px rgba(132,64,255,0.6), 0 0 120px rgba(132,64,255,0.4)"
              border="4px solid"
              borderColor="brand.400"
              filter="drop-shadow(0 0 30px rgba(132,64,255,0.5))"
            />
          </MotionBox>

          <MotionHeading
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            fontSize={{ base: "4xl", md: "5xl", lg: "6xl" }}
            fontWeight="extrabold"
            bgGradient="linear(135deg, brand.300 0%, prismTeal.300 50%, accent.300 100%)"
            bgClip="text"
            textShadow="0 0 30px rgba(132,64,255,0.3)"
            letterSpacing="wider"
          >
            PRISM
          </MotionHeading>

          <MotionText
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            fontSize={{ base: "xl", md: "2xl" }}
            color="whiteAlpha.800"
            fontWeight="medium"
            maxW="800px"
            lineHeight="1.6"
          >
            The Next Gen AI-Powered Data Intelligence Platform
          </MotionText>

          <MotionText
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            fontSize={{ base: "lg", md: "xl" }}
            color="whiteAlpha.600"
            maxW="600px"
            lineHeight="1.6"
          >
            Transform your data into actionable insights with cutting-edge AI technology. 
            Experience the future of data analysis with PRISM's intelligent automation.
          </MotionText>
        </VStack>

        {/* Stats Section */}
        <Box mb={20}>
          <MotionHeading
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.8 }}
            textAlign="center"
            mb={12}
            fontSize={{ base: "2xl", md: "3xl" }}
            fontWeight="bold"
            color="white"
          >
            Why Choose PRISM?
          </MotionHeading>

          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={8}>
            {stats.map((stat, index) => (
              <MotionBox
                key={stat.label}
                initial={{ y: 30, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.6, delay: 1 + index * 0.1 }}
                p={6}
                borderRadius="2xl"
                bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
                backdropFilter="saturate(180%) blur(40px)"
                border="1px solid"
                borderColor="whiteAlpha.200"
                boxShadow="0 8px 32px rgba(0,0,0,0.12)"
                textAlign="center"
                _hover={{
                  transform: "translateY(-5px)",
                  boxShadow: "0 20px 40px rgba(0,0,0,0.2)",
                  borderColor: "brand.400"
                }}
              >
                <Icon as={stat.icon} boxSize={8} color="brand.400" mb={4} />
                <Text fontSize="3xl" fontWeight="bold" color="white" mb={2}>
                  {stat.value}
                </Text>
                <Text fontSize="sm" color="whiteAlpha.700" fontWeight="medium">
                  {stat.label}
                </Text>
              </MotionBox>
            ))}
          </SimpleGrid>
        </Box>

        {/* Features Section */}
        <Box mb={20}>
          <MotionHeading
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, delay: 1.4 }}
            textAlign="center"
            mb={12}
            fontSize={{ base: "2xl", md: "3xl" }}
            fontWeight="bold"
            color="white"
          >
            Powerful Features
          </MotionHeading>

          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={8}>
            {features.map((feature, index) => (
              <MotionBox
                key={feature.title}
                initial={{ y: 30, opacity: 0, scale: 0.9 }}
                animate={{ y: 0, opacity: 1, scale: 1 }}
                transition={{ duration: 0.6, delay: 1.6 + index * 0.1 }}
                p={8}
                borderRadius="2xl"
                bg="linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
                backdropFilter="saturate(180%) blur(40px)"
                border="1px solid"
                borderColor="whiteAlpha.200"
                boxShadow="0 8px 32px rgba(0,0,0,0.12)"
                position="relative"
                overflow="hidden"
                _hover={{
                  transform: "translateY(-10px) scale(1.02)",
                  boxShadow: "0 25px 50px rgba(0,0,0,0.2)",
                  borderColor: feature.color
                }}
                _before={{
                  content: '""',
                  position: "absolute",
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: feature.bgGradient,
                  opacity: 0.1,
                  zIndex: -1
                }}
              >
                <VStack spacing={4} align="start">
                  <HStack spacing={4}>
                    <Box
                      p={3}
                      borderRadius="xl"
                      bg={feature.bgGradient}
                      boxShadow={`0 4px 20px ${feature.color}40`}
                    >
                      <Icon as={feature.icon} boxSize={6} color="white" />
                    </Box>
                    <Text fontSize="xl" fontWeight="bold" color="white">
                      {feature.title}
                    </Text>
                  </HStack>
                  <Text color="whiteAlpha.700" lineHeight="1.6">
                    {feature.description}
                  </Text>
                </VStack>
              </MotionBox>
            ))}
          </SimpleGrid>
        </Box>

        {/* CTA Section */}
        <MotionBox
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8, delay: 2.2 }}
          textAlign="center"
          p={12}
          borderRadius="3xl"
          bg="linear-gradient(135deg, rgba(132,64,255,0.2) 0%, rgba(20,184,166,0.2) 100%)"
          backdropFilter="saturate(180%) blur(40px)"
          border="1px solid"
          borderColor="whiteAlpha.200"
          boxShadow="0 8px 32px rgba(0,0,0,0.12)"
        >
          <VStack spacing={6}>
            <Heading fontSize={{ base: "2xl", md: "3xl" }} color="white" fontWeight="bold">
              Ready to Transform Your Data?
            </Heading>
            <Text fontSize="lg" color="whiteAlpha.700" maxW="600px">
              Join thousands of users who are already leveraging PRISM's AI capabilities 
              to unlock the full potential of their data.
            </Text>
            <HStack spacing={4}>
              <Button
                size="lg"
                bg="linear-gradient(135deg, brand.500 0%, brand.400 100%)"
                color="white"
                px={8}
                py={6}
                borderRadius="xl"
                fontSize="lg"
                fontWeight="bold"
                boxShadow="0 8px 32px rgba(132,64,255,0.3)"
                border="2px solid"
                borderColor="brand.400"
                _hover={{
                  bg: "linear-gradient(135deg, brand.400 0%, brand.300 100%)",
                  transform: "translateY(-2px)",
                  boxShadow: "0 12px 40px rgba(132,64,255,0.4)"
                }}
                _active={{
                  transform: "translateY(0)"
                }}
                rightIcon={<FiArrowRight />}
                onClick={() => navigate("/insights")}
              >
                Get Started
              </Button>
            </HStack>
          </VStack>
        </MotionBox>
      </Container>
    </Box>
  );
}
