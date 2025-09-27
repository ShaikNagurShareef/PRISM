import { useState } from "react";
import { Box, Flex, Text, Image, HStack, Badge, IconButton, useColorModeValue } from "@chakra-ui/react";
import { AnimatePresence, motion } from "framer-motion";
import { NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { FiBarChart2, FiCpu, FiLayers, FiMoon, FiSun, FiZap, FiTrendingUp, FiDatabase } from "react-icons/fi";
import InsightsPage from "./pages/InsightsPage";
import ModelingPage from "./pages/ModelingPage";
import AutoRagPage from "./pages/AutoRagPage";
import AboutPage from "./pages/AboutPage";
import Sidebar from "./components/Sidebar";
import SplashScreen from "./components/SplashScreen";

const MotionBox = motion(Box);

export default function App() {
  const [showSplash, setShowSplash] = useState(true);
  const location = useLocation();
  const navigate = useNavigate();
  const headerBg = useColorModeValue("whiteAlpha.900", "glass.300");
  const borderColor = useColorModeValue("gray.200", "whiteAlpha.300");

  const handleEnterApp = () => {
    setShowSplash(false);
  };

  const handleLogoClick = () => {
    navigate("/about");
  };

  // Hide splash screen if we're on About page or any other page
  const shouldShowSplash = showSplash && location.pathname === "/";

  return (
    <>
      {shouldShowSplash ? (
        <SplashScreen onEnter={handleEnterApp} />
      ) : (
        <Flex h="100vh" overflow="hidden" bg="gray.900">
          {location.pathname !== "/about" && <Sidebar />}
          <Flex direction="column" flex="1" overflow="hidden" ml={location.pathname !== "/about" ? "320px" : "0"}>
        {/* Modern Header with Enhanced Styling - Hidden on About page */}
        {location.pathname !== "/about" && (
          <Flex 
            as="header" 
            align="center" 
            justify="space-between" 
            px={8} 
            py={4} 
            borderBottomWidth="1px" 
            borderColor={borderColor}
            bg={headerBg}
            position="sticky" 
            top={0} 
            zIndex={20} 
            backdropFilter="saturate(180%) blur(40px)"
            boxShadow="0 8px 32px rgba(0,0,0,0.12)"
          >
          <HStack spacing={8}>
            <MotionBox 
              initial={{ scale: 0.8, opacity: 0, rotate: -180 }} 
              animate={{ scale: 1, opacity: 1, rotate: 0 }} 
              transition={{ duration: 0.6, type: "spring", stiffness: 200 }}
              whileHover={{ scale: 1.05, rotate: 2 }}
              cursor="pointer"
              onClick={handleLogoClick}
            >
              <Image 
                src="/prism_logo.png?v=2" 
                alt="PRISM" 
                boxSize="40px" 
                borderRadius="xl" 
                boxShadow="0 8px 32px rgba(132,64,255,0.3)"
                border="2px solid"
                borderColor="brand.400"
                filter="drop-shadow(0 0 20px rgba(132,64,255,0.4))"
              />
            </MotionBox>
            <MotionBox
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <Text 
                fontWeight="extrabold" 
                fontSize="xl" 
                letterSpacing="wider" 
                bgGradient="linear(135deg, brand.400 0%, prismTeal.400 50%, accent.400 100%)" 
                bgClip="text"
                textShadow="0 0 20px rgba(132,64,255,0.3)"
              >
                PRISM
              </Text>
            </MotionBox>
            <HStack spacing={1} fontWeight="semibold">
              <MotionBox
                as={NavLink} 
                to="/insights" 
                px={4} 
                py={2} 
                borderRadius="xl" 
                display="flex"
                alignItems="center"
                gap={2}
                _hover={{ 
                  bg: "whiteAlpha.100",
                  transform: "translateY(-1px)",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.1)"
                }}
                style={({ isActive }: any) => (isActive ? { 
                  background: "linear-gradient(135deg, prismTeal.500 0%, prismTeal.400 100%)", 
                  color: "white",
                  boxShadow: "0 4px 20px rgba(20,184,166,0.3)"
                } : {})}
                transition="all 0.3s ease"
              >
                <FiTrendingUp size={16} />
                Insights
              </MotionBox>
              <MotionBox
                as={NavLink} 
                to="/modeling" 
                px={4} 
                py={2} 
                borderRadius="xl" 
                display="flex"
                alignItems="center"
                gap={2}
                _hover={{ 
                  bg: "whiteAlpha.100",
                  transform: "translateY(-1px)",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.1)"
                }}
                style={({ isActive }: any) => (isActive ? { 
                  background: "linear-gradient(135deg, brand.500 0%, brand.400 100%)", 
                  color: "white",
                  boxShadow: "0 4px 20px rgba(132,64,255,0.3)"
                } : {})}
                transition="all 0.3s ease"
              >
                <FiCpu size={16} />
                Modeling
              </MotionBox>
              <MotionBox
                as={NavLink} 
                to="/autorag" 
                px={4} 
                py={2} 
                borderRadius="xl" 
                display="flex"
                alignItems="center"
                gap={2}
                _hover={{ 
                  bg: "whiteAlpha.100",
                  transform: "translateY(-1px)",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.1)"
                }}
                style={({ isActive }: any) => (isActive ? { 
                  background: "linear-gradient(135deg, accent.500 0%, accent.400 100%)", 
                  color: "white",
                  boxShadow: "0 4px 20px rgba(255,26,107,0.3)"
                } : {})}
                transition="all 0.3s ease"
              >
                <FiDatabase size={16} />
                AutoRAG
              </MotionBox>
            </HStack>
          </HStack>
        </Flex>
        )}
        
        {/* Main Content Area */}
        <Box as="main" flex="1" overflow="auto" position="relative">
          {/* Subtle Background Pattern */}
          <Box
            position="absolute"
            top={0}
            left={0}
            right={0}
            bottom={0}
            backgroundImage="radial-gradient(circle at 25% 25%, rgba(132,64,255,0.1) 0%, transparent 50%), radial-gradient(circle at 75% 75%, rgba(20,184,166,0.08) 0%, transparent 50%)"
            pointerEvents="none"
            zIndex={0}
          />
          
          <Box maxW="1400px" mx="auto" position="relative" zIndex={1} p={8}>
            <AnimatePresence mode="wait">
              <MotionBox 
                key={location.pathname} 
                initial={{ opacity: 0, y: 20, scale: 0.98 }} 
                animate={{ opacity: 1, y: 0, scale: 1 }} 
                exit={{ opacity: 0, y: -20, scale: 0.98 }} 
                transition={{ duration: 0.4, ease: "easeInOut" }}
              >
                <Routes>
                  <Route path="/" element={<InsightsPage />} />
                  <Route path="/insights" element={<InsightsPage />} />
                  <Route path="/modeling" element={<ModelingPage />} />
                  <Route path="/autorag" element={<AutoRagPage />} />
                  <Route path="/about" element={<AboutPage />} />
                </Routes>
              </MotionBox>
            </AnimatePresence>
          </Box>
        </Box>
      </Flex>
    </Flex>
      )}
    </>
  );
}