import { alpha, createTheme } from '@mui/material/styles'

export const designTokens = {
  color: {
    canvas: '#070a10',
    canvasSubtle: '#0a0f18',
    surface: '#101722',
    surfaceRaised: '#151e2c',
    surfaceHover: '#192435',
    brand: '#9d7cff',
    brandHover: '#b29cff',
    brandActive: '#8565e8',
    cyan: '#58c7d8',
    success: '#55d6a5',
    warning: '#f4bd62',
    error: '#ff7e92',
    info: '#6ab8ff',
    text: '#f4f7fb',
    textMuted: '#a9b4c8',
    textSubtle: '#7f8ca4',
    border: 'rgba(184, 197, 222, 0.12)',
    borderStrong: 'rgba(184, 197, 222, 0.23)',
    focus: '#c9bbff',
  },
  radius: { sm: 8, md: 12, lg: 18, xl: 24 },
  shadow: {
    card: '0 18px 48px rgba(0, 0, 0, 0.2)',
    floating: '0 24px 64px rgba(0, 0, 0, 0.32)',
  },
  layout: { contentMaxWidth: 1280, readingMaxWidth: 760 },
  transition: { fast: '140ms ease', normal: '200ms ease' },
} as const

const { color, radius, shadow, transition } = designTokens

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: color.brand,
      dark: color.brandActive,
      light: color.brandHover,
      contrastText: '#090b11',
    },
    secondary: { main: color.cyan },
    success: { main: color.success },
    warning: { main: color.warning },
    error: { main: color.error },
    info: { main: color.info },
    text: { primary: color.text, secondary: color.textMuted },
    background: { default: color.canvas, paper: color.surface },
    divider: color.border,
    action: {
      hover: alpha(color.text, 0.055),
      selected: alpha(color.brand, 0.12),
      disabled: alpha(color.text, 0.38),
      disabledBackground: alpha(color.text, 0.08),
    },
  },
  shape: { borderRadius: radius.md },
  typography: {
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    h1: {
      fontSize: 'clamp(2.35rem, 5vw, 4.4rem)',
      fontWeight: 820,
      letterSpacing: '-0.052em',
      lineHeight: 0.99,
    },
    h2: {
      fontSize: 'clamp(1.9rem, 3.8vw, 3.15rem)',
      fontWeight: 800,
      letterSpacing: '-0.043em',
      lineHeight: 1.06,
    },
    h3: {
      fontSize: 'clamp(1.55rem, 2.8vw, 2.25rem)',
      fontWeight: 780,
      letterSpacing: '-0.035em',
      lineHeight: 1.12,
    },
    h4: { fontWeight: 780, letterSpacing: '-0.03em', lineHeight: 1.15 },
    h5: { fontWeight: 760, letterSpacing: '-0.025em', lineHeight: 1.2 },
    h6: { fontWeight: 740, letterSpacing: '-0.018em', lineHeight: 1.3 },
    body1: { lineHeight: 1.68 },
    body2: { lineHeight: 1.58 },
    button: {
      fontWeight: 760,
      letterSpacing: '-0.01em',
      textTransform: 'none',
    },
    overline: { fontWeight: 800, letterSpacing: '0.09em', lineHeight: 1.6 },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        ':root': { colorScheme: 'dark' },
        html: { scrollbarColor: `${color.borderStrong} ${color.canvas}` },
        body: {
          backgroundColor: color.canvas,
          backgroundImage: `radial-gradient(circle at 12% 0%, ${alpha(color.brand, 0.065)}, transparent 31rem)`,
          colorScheme: 'dark',
          minHeight: '100vh',
        },
        a: { textUnderlineOffset: '0.2em' },
        '::selection': { backgroundColor: alpha(color.brand, 0.32) },
        ':focus-visible': {
          outline: `3px solid ${alpha(color.focus, 0.8)}`,
          outlineOffset: 3,
        },
        '@media (prefers-reduced-motion: reduce)': {
          '*, *::before, *::after': {
            scrollBehavior: 'auto !important',
            transitionDuration: '0.01ms !important',
            animationDuration: '0.01ms !important',
            animationIterationCount: '1 !important',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${color.border}`,
          backgroundColor: alpha(color.canvas, 0.9),
          backdropFilter: 'blur(18px)',
          color: color.text,
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: {
          minHeight: 44,
          borderRadius: radius.md,
          paddingInline: 18,
          transition: `background-color ${transition.fast}, border-color ${transition.fast}, transform ${transition.fast}`,
          '&:active:not(.Mui-disabled)': { transform: 'translateY(1px)' },
          '&.MuiButton-containedPrimary': {
            backgroundColor: color.brand,
            backgroundImage: 'none',
            color: '#090b11',
            '&:hover': { backgroundColor: color.brandHover },
          },
          '&.MuiButton-outlined': {
            borderColor: color.borderStrong,
            '&:hover': { borderColor: alpha(color.brand, 0.65) },
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: color.surface,
          backgroundImage: 'none',
          borderColor: color.border,
          borderRadius: radius.lg,
          boxShadow: shadow.card,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: 'none', borderColor: color.border },
        rounded: { borderRadius: radius.lg },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          minHeight: 52,
          backgroundColor: color.canvasSubtle,
          borderRadius: radius.md,
          transition: `box-shadow ${transition.fast}, background-color ${transition.fast}`,
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: color.borderStrong,
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: alpha(color.brandHover, 0.62),
          },
          '&.Mui-focused': {
            boxShadow: `0 0 0 4px ${alpha(color.brand, 0.12)}`,
          },
          '&.Mui-disabled': { backgroundColor: alpha(color.text, 0.045) },
        },
      },
    },
    MuiInputLabel: { styleOverrides: { root: { fontWeight: 650 } } },
    MuiChip: {
      styleOverrides: {
        root: { borderRadius: radius.sm, fontWeight: 750 },
        outlined: { backgroundColor: alpha(color.text, 0.018) },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          border: '1px solid currentColor',
          borderRadius: radius.md,
          '&.MuiAlert-standardError': {
            backgroundColor: alpha(color.error, 0.08),
          },
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          border: `1px solid ${color.borderStrong}`,
          borderRadius: radius.xl,
          boxShadow: shadow.floating,
          padding: 8,
        },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          border: `1px solid ${color.borderStrong}`,
          marginTop: 8,
          minWidth: 210,
        },
      },
    },
    MuiSkeleton: {
      styleOverrides: { root: { backgroundColor: alpha(color.text, 0.075) } },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: { backgroundColor: alpha(color.text, 0.08), borderRadius: 999 },
        bar: { borderRadius: 999 },
      },
    },
    MuiTooltip: { styleOverrides: { tooltip: { fontSize: '0.78rem' } } },
    MuiTableCell: { styleOverrides: { root: { borderColor: color.border } } },
  },
})
