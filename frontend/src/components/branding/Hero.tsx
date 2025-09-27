import { Box, Button, Flex, Heading, Image, Text } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";

const MotionBox = motion(Box);

export default function Hero() {
  return (
    <Flex direction={{ base: "column", md: "row" }} align="center" justify="space-between" gap={8} py={10}>
      <MotionBox initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
        <Heading size={{ base: "xl", md: "2xl" }} lineHeight={1.1}>PRISM</Heading>
        <Text mt={3} color="gray.500" maxW="640px">
          AI-Powered Data Intelligence. Explore insights, build predictive models, and manage your RAG knowledge base — all in one place.
        </Text>
        <Flex mt={6} gap={3} wrap="wrap">
          <Button as={Link} to="/insights">Start with Insights</Button>
          <Button variant="outline" as={Link} to="/autorag">Open AutoRAG</Button>
        </Flex>
      </MotionBox>
      <MotionBox initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6, delay: 0.1 }}>
        <Image src="/prism_logo.png?v=2" alt="PRISM Logo" maxH="180px" objectFit="contain" />
      </MotionBox>
    </Flex>
  );
}
