import { useQueryClient } from '@tanstack/react-query'
import { Link, Outlet, useNavigate } from '@tanstack/react-router'
import {
  AppBar,
  Box,
  Button,
  Container,
  Toolbar,
  Typography,
} from '@mui/material'

import { useAuth } from '../auth/authContext'

export function RootLayout() {
  const auth = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const handleLogout = async () => {
    try {
      await auth.logout()
    } finally {
      queryClient.clear()
      await navigate({ to: '/' })
    }
  }

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
            {auth.session.status === 'authenticated' ? (
              <>
                {auth.session.user.role === 'organizer' ? (
                  <Button component={Link} to="/organizer/events">
                    Etkinliklerim
                  </Button>
                ) : (
                  <Button component={Link} to="/attendee/reservations">
                    Rezervasyonlarım
                  </Button>
                )}
                <Typography sx={{ display: { xs: 'none', sm: 'block' } }}>
                  {auth.session.user.fullName}
                </Typography>
                <Button onClick={() => void handleLogout()}>Çıkış yap</Button>
              </>
            ) : (
              <>
                <Button component={Link} to="/login" variant="text">
                  Giriş yap
                </Button>
                <Button component={Link} to="/register" variant="contained">
                  Kayıt ol
                </Button>
              </>
            )}
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
