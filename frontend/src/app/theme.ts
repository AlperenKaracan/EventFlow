import { alpha, createTheme } from '@mui/material/styles'

const primary = '#4f46e5'
const secondary = '#0f766e'

export const theme = createTheme({
  colorSchemes: {
    light: {
      palette: {
        primary: { main: primary, dark: '#3730a3', light: '#818cf8' },
        secondary: { main: secondary, dark: '#115e59', light: '#5eead4' },
        success: { main: '#15803d' },
        warning: { main: '#b45309' },
        error: { main: '#dc2626' },
        text: { primary: '#172033', secondary: '#657089' },
        background: { default: '#f7f8fc', paper: '#ffffff' },
        divider: '#e5e9f2',
      },
    },
  },
  shape: { borderRadius: 16 },
  typography: {
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    h1: {
      fontSize: 'clamp(2.35rem, 6vw, 4.75rem)',
      fontWeight: 850,
      letterSpacing: '-0.045em',
      lineHeight: 1.02,
    },
    h2: {
      fontSize: 'clamp(1.75rem, 4vw, 2.75rem)',
      fontWeight: 820,
      letterSpacing: '-0.035em',
      lineHeight: 1.1,
    },
    h5: { letterSpacing: '-0.02em' },
    h6: { letterSpacing: '-0.015em' },
    body1: { lineHeight: 1.7 },
    button: { fontWeight: 750, textTransform: 'none' },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundAttachment: 'fixed',
          backgroundImage: `radial-gradient(circle at 8% 0%, ${alpha(
            primary,
            0.08,
          )}, transparent 26rem), radial-gradient(circle at 92% 12%, ${alpha(
            secondary,
            0.07,
          )}, transparent 24rem)`,
        },
        '::selection': {
          backgroundColor: alpha(primary, 0.18),
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(226, 230, 239, 0.88)',
          backgroundColor: 'rgba(255, 255, 255, 0.82)',
          backdropFilter: 'blur(18px)',
          color: '#172033',
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: {
          minHeight: 42,
          borderRadius: 12,
          paddingInline: 18,
          '&.MuiButton-containedPrimary': {
            backgroundImage: 'linear-gradient(135deg, #4f46e5, #6366f1)',
            boxShadow: `0 10px 24px ${alpha(primary, 0.2)}`,
            '&:hover': {
              boxShadow: `0 12px 28px ${alpha(primary, 0.3)}`,
            },
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderColor: '#e3e7f0',
          boxShadow: '0 12px 36px rgba(32, 45, 76, 0.06)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: { borderColor: '#e3e7f0' },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          transition: 'box-shadow 160ms ease, border-color 160ms ease',
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: '#aab2c5',
          },
          '&.Mui-focused': {
            boxShadow: `0 0 0 4px ${alpha(primary, 0.1)}`,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: { root: { fontWeight: 750 } },
    },
    MuiAlert: {
      styleOverrides: { root: { borderRadius: 14 } },
    },
    MuiDialog: {
      styleOverrides: {
        paper: { borderRadius: 20, padding: 8 },
      },
    },
  },
})
