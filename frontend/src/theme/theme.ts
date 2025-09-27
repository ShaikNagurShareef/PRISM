import { extendTheme, ThemeConfig } from "@chakra-ui/react";

// PRISM-inspired theme: purple + teal, dark default, modern gradients and effects
const config: ThemeConfig = { initialColorMode: "dark", useSystemColorMode: false };

const theme = extendTheme({
  config,
  fonts: {
    heading: "Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
    body: "Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
  },
  styles: {
    global: {
      html: { 
        height: "100%",
        scrollBehavior: "smooth",
        fontFamily: "Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
      },
      body: {
        height: "100%",
        bg: "linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)",
        color: "#f7fafc",
        backgroundImage: `
          radial-gradient(ellipse 1200px 400px at 10% 0%, rgba(132,64,255,0.15) 0%, transparent 60%),
          radial-gradient(ellipse 800px 300px at 90% 0%, rgba(20,184,166,0.12) 0%, transparent 60%),
          radial-gradient(ellipse 600px 200px at 50% 100%, rgba(255,26,107,0.08) 0%, transparent 70%),
          radial-gradient(ellipse 400px 150px at 30% 50%, rgba(255,193,7,0.06) 0%, transparent 80%),
          linear-gradient(135deg, rgba(15,15,35,0.95) 0%, rgba(26,26,46,0.98) 50%, rgba(22,33,62,1) 100%)
        `,
        backgroundAttachment: "fixed",
        overflowX: "hidden",
        position: "relative",
        "&::before": {
          content: '""',
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `
            radial-gradient(circle at 20% 20%, rgba(132,64,255,0.08) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(20,184,166,0.06) 0%, transparent 50%),
            radial-gradient(circle at 40% 60%, rgba(255,26,107,0.04) 0%, transparent 50%)
          `,
          pointerEvents: "none",
          zIndex: 0,
        },
        "&::after": {
          content: '""',
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `
            linear-gradient(45deg, transparent 0%, rgba(132,64,255,0.02) 25%, transparent 50%, rgba(20,184,166,0.02) 75%, transparent 100%)
          `,
          pointerEvents: "none",
          zIndex: 0,
        },
      },
      "#root": { 
        height: "100%",
        position: "relative",
        zIndex: 1,
      },
      "*": {
        scrollbarWidth: "thin",
        scrollbarColor: "rgba(132,64,255,0.4) transparent",
      },
      "*::-webkit-scrollbar": {
        width: "8px",
        height: "8px",
      },
      "*::-webkit-scrollbar-track": {
        background: "rgba(0,0,0,0.1)",
        borderRadius: "4px",
      },
      "*::-webkit-scrollbar-thumb": {
        background: "linear-gradient(135deg, rgba(132,64,255,0.4) 0%, rgba(20,184,166,0.4) 100%)",
        borderRadius: "4px",
        "&:hover": {
          background: "linear-gradient(135deg, rgba(132,64,255,0.6) 0%, rgba(20,184,166,0.6) 100%)",
        },
      },
      "*::-webkit-scrollbar-corner": {
        background: "transparent",
      },
    },
  },
  colors: {
    brand: {
      50: "#f0e7ff",
      100: "#d8c7ff",
      200: "#b793ff",
      300: "#9961ff",
      400: "#8440ff",
      500: "#6e2fe0",
      600: "#5b25b8",
      700: "#4a1f94",
      800: "#3a1873",
      900: "#2a1254",
    },
    prismTeal: {
      50: "#e6fffb",
      100: "#bffaf3",
      200: "#93f2e7",
      300: "#61e6d9",
      400: "#2fd8c9",
      500: "#14b8a6",
      600: "#0e968a",
      700: "#0b766e",
      800: "#095d58",
      900: "#074846",
    },
    accent: {
      50: "#fff0f5",
      100: "#ffd6e8",
      200: "#ff9ec7",
      300: "#ff66a6",
      400: "#ff3d85",
      500: "#ff1a6b",
      600: "#e6005c",
      700: "#cc004d",
      800: "#b3003e",
      900: "#990033",
    },
    glass: {
      50: "rgba(255,255,255,0.05)",
      100: "rgba(255,255,255,0.1)",
      200: "rgba(255,255,255,0.15)",
      300: "rgba(255,255,255,0.2)",
      400: "rgba(255,255,255,0.25)",
      500: "rgba(255,255,255,0.3)",
    },
  },
  shadows: {
    glow: "0 0 0 6px rgba(110,47,224,.25)",
    glowTeal: "0 0 0 6px rgba(20,184,166,.25)",
    glowAccent: "0 0 0 6px rgba(255,26,107,.25)",
    glass: "0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
    glassHover: "0 12px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.15)",
    neon: "0 0 20px rgba(132,64,255,0.5), 0 0 40px rgba(132,64,255,0.3)",
    neonTeal: "0 0 20px rgba(20,184,166,0.5), 0 0 40px rgba(20,184,166,0.3)",
    soft: "0 4px 16px rgba(0,0,0,0.1), 0 2px 8px rgba(0,0,0,0.05)",
    softHover: "0 8px 24px rgba(0,0,0,0.15), 0 4px 12px rgba(0,0,0,0.08)",
    dramatic: "0 20px 60px rgba(0,0,0,0.4), 0 8px 24px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.1)",
    dramaticHover: "0 32px 80px rgba(0,0,0,0.5), 0 12px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.15)",
    ultraGlow: "0 0 30px rgba(132,64,255,0.6), 0 0 60px rgba(132,64,255,0.4), 0 0 90px rgba(132,64,255,0.2)",
    ultraGlowTeal: "0 0 30px rgba(20,184,166,0.6), 0 0 60px rgba(20,184,166,0.4), 0 0 90px rgba(20,184,166,0.2)",
    ultraGlowAccent: "0 0 30px rgba(255,26,107,0.6), 0 0 60px rgba(255,26,107,0.4), 0 0 90px rgba(255,26,107,0.2)",
    floating: "0 16px 48px rgba(0,0,0,0.2), 0 8px 24px rgba(0,0,0,0.1), 0 4px 12px rgba(0,0,0,0.05)",
    floatingHover: "0 24px 64px rgba(0,0,0,0.3), 0 12px 32px rgba(0,0,0,0.15), 0 6px 16px rgba(0,0,0,0.08)",
  },
  components: {
    Button: {
      baseStyle: { 
        borderRadius: 12, 
        fontWeight: 600, 
        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        position: "relative",
        overflow: "hidden",
        _before: {
          content: '""',
          position: "absolute",
          top: 0,
          left: "-100%",
          width: "100%",
          height: "100%",
          background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)",
          transition: "left 0.5s",
        },
        _hover: {
          _before: {
            left: "100%",
          },
        },
      },
      sizes: { 
        sm: { px: 4, py: 2, fontSize: "xs", height: "32px" },
        md: { px: 6, py: 3, fontSize: "sm", height: "40px" },
        lg: { px: 8, py: 4, fontSize: "md", height: "48px" },
        xl: { px: 10, py: 5, fontSize: "lg", height: "56px" },
      },
      variants: {
        solid: {
          bg: "linear-gradient(135deg, brand.500 0%, brand.400 50%, brand.300 100%)",
          color: "white",
          boxShadow: "0 4px 20px rgba(132,64,255,0.3)",
          border: "1px solid",
          borderColor: "brand.400",
          _hover: { 
            bg: "linear-gradient(135deg, brand.400 0%, brand.300 50%, brand.200 100%)",
            transform: "translateY(-2px) scale(1.02)", 
            boxShadow: "0 8px 32px rgba(132,64,255,0.4)",
            borderColor: "brand.300",
          },
          _active: { 
            bg: "linear-gradient(135deg, brand.600 0%, brand.500 50%, brand.400 100%)",
            transform: "translateY(0) scale(0.98)",
            boxShadow: "0 4px 20px rgba(132,64,255,0.3)",
          },
        },
        outline: {
          borderColor: "brand.500",
          color: "brand.200",
          bg: "glass.100",
          backdropFilter: "blur(20px)",
          border: "2px solid",
          boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
          _hover: { 
            bg: "glass.200",
            borderColor: "brand.400",
            transform: "translateY(-2px) scale(1.02)",
            boxShadow: "0 8px 24px rgba(132,64,255,0.2)",
          },
        },
        ghost: {
          color: "brand.300",
          _hover: {
            bg: "glass.200",
            color: "brand.200",
            transform: "translateY(-1px)",
          },
        },
        glass: {
          bg: "glass.200",
          color: "white",
          border: "2px solid",
          borderColor: "whiteAlpha.300",
          backdropFilter: "blur(20px)",
          boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
          _hover: {
            bg: "glass.300",
            borderColor: "whiteAlpha.400",
            transform: "translateY(-2px) scale(1.02)",
            boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
          },
        },
        modern: {
          bg: "linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)",
          color: "white",
          border: "1px solid",
          borderColor: "whiteAlpha.200",
          backdropFilter: "blur(20px)",
          boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
          _hover: {
            bg: "linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.08) 100%)",
            borderColor: "whiteAlpha.300",
            transform: "translateY(-2px) scale(1.02)",
            boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
          },
        },
      },
    },
    Input: {
      baseStyle: { 
        field: { 
          borderRadius: 12,
          transition: "all 0.3s ease",
          backdropFilter: "blur(20px)",
          fontWeight: 500,
        } 
      },
      sizes: { 
        sm: { field: { px: 3, py: 2, fontSize: "xs", height: "32px" } },
        md: { field: { px: 4, py: 3, fontSize: "sm", height: "40px" } },
        lg: { field: { px: 5, py: 4, fontSize: "md", height: "48px" } },
      },
      variants: {
        outline: {
          field: {
            borderColor: "whiteAlpha.300",
            bg: "glass.100",
            border: "2px solid",
            _hover: { 
              borderColor: "whiteAlpha.500",
              bg: "glass.200",
              transform: "translateY(-1px)",
            },
            _focusVisible: { 
              borderColor: "prismTeal.400", 
              boxShadow: "0 0 0 3px rgba(20,184,166,0.2), 0 4px 16px rgba(0,0,0,0.1)",
              bg: "glass.200",
              transform: "translateY(-1px)",
            },
          },
        },
        filled: {
          field: {
            bg: "glass.100",
            border: "2px solid",
            borderColor: "whiteAlpha.200",
            _hover: {
              bg: "glass.200",
              borderColor: "whiteAlpha.300",
              transform: "translateY(-1px)",
            },
            _focus: {
              bg: "glass.200",
              borderColor: "prismTeal.400",
              boxShadow: "0 0 0 3px rgba(20,184,166,0.2), 0 4px 16px rgba(0,0,0,0.1)",
              transform: "translateY(-1px)",
            },
          },
        },
        modern: {
          field: {
            bg: "linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)",
            border: "1px solid",
            borderColor: "whiteAlpha.200",
            backdropFilter: "blur(20px)",
            _hover: {
              bg: "linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.08) 100%)",
              borderColor: "whiteAlpha.300",
              transform: "translateY(-1px)",
            },
            _focus: {
              bg: "linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.1) 100%)",
              borderColor: "prismTeal.400",
              boxShadow: "0 0 0 3px rgba(20,184,166,0.2), 0 4px 16px rgba(0,0,0,0.1)",
              transform: "translateY(-1px)",
            },
          },
        },
      },
    },
    Textarea: { 
      baseStyle: { 
        borderRadius: 12,
        transition: "all 0.3s ease",
        backdropFilter: "blur(20px)",
        fontWeight: 500,
      },
      variants: {
        outline: {
          borderColor: "whiteAlpha.300",
          bg: "glass.100",
          border: "2px solid",
          _hover: { 
            borderColor: "whiteAlpha.500",
            bg: "glass.200",
            transform: "translateY(-1px)",
          },
          _focusVisible: { 
            borderColor: "prismTeal.400", 
            boxShadow: "0 0 0 3px rgba(20,184,166,0.2), 0 4px 16px rgba(0,0,0,0.1)",
            bg: "glass.200",
            transform: "translateY(-1px)",
          },
        },
        modern: {
          bg: "linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)",
          border: "1px solid",
          borderColor: "whiteAlpha.200",
          backdropFilter: "blur(20px)",
          _hover: {
            bg: "linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.08) 100%)",
            borderColor: "whiteAlpha.300",
            transform: "translateY(-1px)",
          },
          _focus: {
            bg: "linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.1) 100%)",
            borderColor: "prismTeal.400",
            boxShadow: "0 0 0 3px rgba(20,184,166,0.2), 0 4px 16px rgba(0,0,0,0.1)",
            transform: "translateY(-1px)",
          },
        },
      },
    },
    Select: {
      baseStyle: {
        field: {
          borderRadius: 12,
          transition: "all 0.3s ease",
          backdropFilter: "blur(20px)",
          fontWeight: 500,
        },
      },
      variants: {
        outline: {
          field: {
            borderColor: "whiteAlpha.300",
            bg: "glass.100",
            border: "2px solid",
            _hover: { 
              borderColor: "whiteAlpha.500",
              bg: "glass.200",
              transform: "translateY(-1px)",
            },
            _focusVisible: { 
              borderColor: "prismTeal.400", 
              boxShadow: "0 0 0 3px rgba(20,184,166,0.2), 0 4px 16px rgba(0,0,0,0.1)",
              bg: "glass.200",
              transform: "translateY(-1px)",
            },
          },
        },
        modern: {
          field: {
            bg: "linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)",
            border: "1px solid",
            borderColor: "whiteAlpha.200",
            backdropFilter: "blur(20px)",
            _hover: {
              bg: "linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.08) 100%)",
              borderColor: "whiteAlpha.300",
              transform: "translateY(-1px)",
            },
            _focus: {
              bg: "linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.1) 100%)",
              borderColor: "prismTeal.400",
              boxShadow: "0 0 0 3px rgba(20,184,166,0.2), 0 4px 16px rgba(0,0,0,0.1)",
              transform: "translateY(-1px)",
            },
          },
        },
      },
    },
    Link: { 
      baseStyle: { 
        color: "prismTeal.400", 
        transition: "all 0.3s ease",
        _hover: { 
          color: "prismTeal.300", 
          textDecoration: "none",
          transform: "translateY(-1px)",
        } 
      } 
    },
    Card: { 
      baseStyle: { 
        container: { 
          borderRadius: 16, 
          backdropFilter: "saturate(180%) blur(40px)", 
          bg: "linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)", 
          border: "1px solid", 
          borderColor: "whiteAlpha.200",
          boxShadow: "0 8px 32px rgba(0,0,0,0.12), 0 4px 16px rgba(0,0,0,0.08)",
          transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
          position: "relative",
          overflow: "hidden",
          _before: {
            content: '""',
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "linear-gradient(135deg, rgba(255,255,255,0.08) 0%, transparent 50%, rgba(255,255,255,0.03) 100%)",
            pointerEvents: "none",
            zIndex: 1,
          },
          _hover: {
            boxShadow: "0 16px 48px rgba(0,0,0,0.2), 0 8px 24px rgba(0,0,0,0.12)",
            transform: "translateY(-4px) scale(1.01)",
            borderColor: "whiteAlpha.300",
            _before: {
              background: "linear-gradient(135deg, rgba(255,255,255,0.12) 0%, transparent 50%, rgba(255,255,255,0.06) 100%)",
            },
          },
        } 
      },
      variants: {
        modern: {
          container: {
            borderRadius: 20,
            bg: "linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.08) 100%)",
            border: "2px solid",
            borderColor: "whiteAlpha.300",
            boxShadow: "0 12px 40px rgba(0,0,0,0.15), 0 6px 20px rgba(0,0,0,0.1)",
            _hover: {
              boxShadow: "0 20px 60px rgba(0,0,0,0.25), 0 10px 30px rgba(0,0,0,0.15)",
              transform: "translateY(-6px) scale(1.02)",
              borderColor: "whiteAlpha.400",
            },
          },
        },
        glass: {
          container: {
            borderRadius: 16,
            bg: "rgba(255,255,255,0.05)",
            border: "1px solid",
            borderColor: "whiteAlpha.100",
            backdropFilter: "blur(20px)",
            boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
            _hover: {
              bg: "rgba(255,255,255,0.08)",
              borderColor: "whiteAlpha.200",
              transform: "translateY(-2px)",
              boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
            },
          },
        },
      } 
    },
    Box: {
      baseStyle: {
        transition: "all 0.3s ease",
      },
    },
  },
});

export default theme;

