import { createTheme } from '@mui/material/styles'

export const theme = createTheme({
  colorSchemes: {
    light: {
      palette: {
        primary: { main: '#3157d5' },
        secondary: { main: '#13795b' },
        background: { default: '#f5f7fb', paper: '#ffffff' },
      },
    },
  },
  shape: { borderRadius: 14 },
  typography: {
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    h1: { fontSize: 'clamp(2rem, 5vw, 3.5rem)', fontWeight: 800 },
    h2: { fontSize: 'clamp(1.5rem, 3vw, 2.25rem)', fontWeight: 750 },
    button: { fontWeight: 700, textTransform: 'none' },
  },
  components: {
    MuiButton: { defaultProps: { disableElevation: true } },
    MuiCard: { styleOverrides: { root: { border: '1px solid #dfe5f1' } } },
  },
})
