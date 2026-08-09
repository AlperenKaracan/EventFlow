import { alpha, createTheme } from '@mui/material/styles'

const primary = '#a78bfa'
const secondary = '#67e8f9'

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: primary,
      dark: '#8b5cf6',
      light: '#c4b5fd',
      contrastText: '#0b0d12',
    },
    secondary: { main: secondary, dark: '#22d3ee', light: '#cffafe' },
    success: { main: '#34d399' },
    warning: { main: '#fbbf24' },
    error: { main: '#fb7185' },
    text: { primary: '#f8fafc', secondary: '#94a3b8' },
    background: { default: '#080b11', paper: '#111722' },
    divider: 'rgba(148, 163, 184, 0.16)',
  },
  shape: { borderRadius: 16 },
  typography: {
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    h1: {
      fontSize: 'clamp(2.25rem, 5vw, 4.25rem)',
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
          backgroundColor: '#080b11',
          colorScheme: 'dark',
          minHeight: '100vh',
        },
        html: {
          scrollbarColor: '#374151 #080b11',
        },
        '::selection': {
          backgroundColor: alpha(primary, 0.3),
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(148, 163, 184, 0.14)',
          backgroundColor: 'rgba(8, 11, 17, 0.94)',
          backdropFilter: 'blur(14px)',
          color: '#f8fafc',
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
            backgroundColor: primary,
            backgroundImage: 'none',
            boxShadow: 'none',
            '&:hover': {
              backgroundColor: '#b9a4fb',
              boxShadow: `0 8px 22px ${alpha(primary, 0.18)}`,
            },
          },
          '&.MuiButton-outlined': {
            borderColor: 'rgba(167, 139, 250, 0.34)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#111722',
          backgroundImage: 'none',
          borderColor: 'rgba(148, 163, 184, 0.16)',
          boxShadow: '0 18px 45px rgba(0, 0, 0, 0.18)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          borderColor: 'rgba(148, 163, 184, 0.16)',
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          backgroundColor: '#0b1019',
          transition: 'box-shadow 160ms ease, border-color 160ms ease',
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: 'rgba(196, 181, 253, 0.62)',
          },
          '&.Mui-focused': {
            boxShadow: `0 0 0 4px ${alpha(primary, 0.1)}`,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 750 },
        outlined: { backgroundColor: 'rgba(255, 255, 255, 0.018)' },
      },
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
