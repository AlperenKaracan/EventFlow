import { Link, Outlet } from '@tanstack/react-router'
import {
  AppBar,
  Box,
  Button,
  Container,
  Toolbar,
  Typography,
} from '@mui/material'

export function RootLayout() {
  return (
    <Box sx={{ minHeight: '100vh' }}>
      <AppBar position="static" color="inherit" elevation={0}>
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={{ gap: 2 }}>
            <Typography
              component={Link}
              to="/"
              variant="h6"
              sx={{
                color: 'primary.main',
                fontWeight: 900,
                textDecoration: 'none',
              }}
            >
              EventFlow
            </Typography>
            <Box sx={{ flexGrow: 1 }} />
            <Button component={Link} to="/login" variant="text">
              Giriş yap
            </Button>
            <Button component={Link} to="/register" variant="contained">
              Kayıt ol
            </Button>
          </Toolbar>
        </Container>
      </AppBar>
      <Outlet />
    </Box>
  )
}

export function UpcomingRoute() {
  return (
    <Container component="main" maxWidth="md" sx={{ py: 8 }}>
      <Typography component="h1" variant="h2">
        Bu ekran yakında hazır olacak
      </Typography>
      <Button component={Link} to="/" sx={{ mt: 3 }}>
        Etkinliklere dön
      </Button>
    </Container>
  )
}
