import { alpha, createTheme } from '@mui/material/styles'

const primary = '#8b5cf6'
const secondary = '#22d3ee'

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: primary, dark: '#7c3aed', light: '#c4b5fd' },
    secondary: { main: secondary, dark: '#0891b2', light: '#a5f3fc' },
    success: { main: '#34d399' },
    warning: { main: '#fbbf24' },
    error: { main: '#fb7185' },
    text: { primary: '#f8fafc', secondary: '#94a3b8' },
    background: { default: '#070a12', paper: '#111827' },
    divider: 'rgba(148, 163, 184, 0.18)',
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
          colorScheme: 'dark',
          backgroundImage: `radial-gradient(circle at 8% 0%, ${alpha(
            primary,
            0.16,
          )}, transparent 26rem), radial-gradient(circle at 92% 12%, ${alpha(
            secondary,
            0.1,
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
          borderBottom: '1px solid rgba(148, 163, 184, 0.14)',
          backgroundColor: 'rgba(7, 10, 18, 0.82)',
          backdropFilter: 'blur(18px)',
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
            backgroundImage: 'linear-gradient(135deg, #7c3aed, #8b5cf6)',
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
          backgroundImage:
            'linear-gradient(145deg, rgba(17, 24, 39, 0.98), rgba(10, 15, 27, 0.98))',
          borderColor: 'rgba(148, 163, 184, 0.16)',
          boxShadow: '0 18px 48px rgba(0, 0, 0, 0.24)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: { borderColor: 'rgba(148, 163, 184, 0.16)' },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(8, 13, 24, 0.78)',
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
