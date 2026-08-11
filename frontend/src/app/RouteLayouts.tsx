import { useQueryClient } from '@tanstack/react-query'
import { Link, Outlet, useNavigate } from '@tanstack/react-router'
import {
  AppBar,
  Box,
  Button,
  Container,
  Stack,
  Toolbar,
  Typography,
} from '@mui/material'
import { Suspense } from 'react'

import { useAuth } from '../auth/authContext'
import { LoadingState } from '../shared/AsyncState'

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
      <AppBar position="sticky" color="inherit" elevation={0}>
        <Container maxWidth="lg">
          <Toolbar
            disableGutters
            sx={{ gap: { xs: 0.75, sm: 2 }, minHeight: 72 }}
          >
            <Box
              component={Link}
              to="/"
              sx={{
                alignItems: 'center',
                color: 'primary.main',
                display: 'inline-flex',
                gap: 1,
                textDecoration: 'none',
              }}
            >
              <Box
                aria-hidden="true"
                sx={{
                  alignItems: 'center',
                  backgroundColor: 'primary.main',
                  borderRadius: '11px',
                  boxShadow: '0 7px 18px rgba(0, 0, 0, 0.22)',
                  color: 'primary.contrastText',
                  display: 'inline-flex',
                  fontSize: 14,
                  fontWeight: 900,
                  height: 34,
                  justifyContent: 'center',
                  width: 34,
                }}
              >
                EF
              </Box>
              <Typography
                component="span"
                variant="h6"
                sx={{ fontWeight: 900, letterSpacing: '-0.035em' }}
              >
                EventFlow
              </Typography>
            </Box>
            <Box sx={{ flexGrow: 1 }} />
            {auth.session.status === 'authenticated' ? (
              <Stack
                direction="row"
                sx={{ alignItems: 'center', gap: { xs: 0.25, sm: 1 } }}
              >
                {auth.session.user.role === 'organizer' ? (
                  <Button
                    component={Link}
                    to="/organizer/events"
                    size="small"
                    sx={{ px: { xs: 1, sm: 2 } }}
                  >
                    Etkinliklerim
                  </Button>
                ) : (
                  <Button
                    component={Link}
                    to="/attendee/reservations"
                    size="small"
                    sx={{ px: { xs: 1, sm: 2 } }}
                  >
                    Rezervasyonlarım
                  </Button>
                )}
                <Typography
                  variant="body2"
                  sx={{ display: { xs: 'none', md: 'block' }, fontWeight: 700 }}
                >
                  {auth.session.user.fullName}
                </Typography>
                <Button
                  aria-label="Çıkış yap"
                  onClick={() => void handleLogout()}
                  size="small"
                  sx={{ minWidth: 0, px: { xs: 1, sm: 2 } }}
                >
                  <Box
                    component="span"
                    sx={{ display: { xs: 'none', sm: 'inline' } }}
                  >
                    Çıkış yap
                  </Box>
                  <Box
                    component="span"
                    sx={{ display: { xs: 'inline', sm: 'none' } }}
                  >
                    Çıkış
                  </Box>
                </Button>
              </Stack>
            ) : (
              <Stack
                direction="row"
                sx={{ flexShrink: 0, gap: { xs: 0.25, sm: 1 } }}
              >
                <Button
                  component={Link}
                  to="/login"
                  variant="text"
                  size="small"
                  sx={{ px: { xs: 0.75, sm: 1.25 }, whiteSpace: 'nowrap' }}
                >
                  Giriş yap
                </Button>
                <Button
                  component={Link}
                  to="/register"
                  variant="contained"
                  size="small"
                  sx={{ px: { xs: 1.25, sm: 2 }, whiteSpace: 'nowrap' }}
                >
                  Kayıt ol
                </Button>
              </Stack>
            )}
          </Toolbar>
        </Container>
      </AppBar>
      <Suspense fallback={<LoadingState label="Sayfa yükleniyor" />}>
        <Outlet />
      </Suspense>
    </Box>
  )
}
