import { useQueryClient } from '@tanstack/react-query'
import {
  Link,
  Outlet,
  useNavigate,
  useRouterState,
} from '@tanstack/react-router'
import {
  AppBar,
  Avatar,
  Box,
  Button,
  Container,
  Divider,
  IconButton,
  Menu,
  MenuItem,
  Stack,
  Toolbar,
  Typography,
} from '@mui/material'
import { Suspense, useState } from 'react'

import { useAuth } from '../auth/authContext'
import { LoadingState } from '../shared/AsyncState'
import { ProductMark } from '../shared/ui/ProductMark'
import { designTokens } from './theme'

type NavItem = {
  label: string
  to:
    | '/'
    | '/attendee/reservations'
    | '/organizer/events'
    | '/organizer/events/new'
}

function NavButton({ item, active }: { item: NavItem; active: boolean }) {
  return (
    <Button
      component={Link}
      to={item.to}
      aria-current={active ? 'page' : undefined}
      color="inherit"
      sx={{
        backgroundColor: active ? 'action.selected' : 'transparent',
        color: active ? 'text.primary' : 'text.secondary',
        minHeight: 38,
        px: 1.5,
        '&:hover': { backgroundColor: 'action.hover', color: 'text.primary' },
      }}
    >
      {item.label}
    </Button>
  )
}

export function RootLayout() {
  const auth = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })
  const [menuAnchor, setMenuAnchor] = useState<HTMLElement | null>(null)

  const handleLogout = async () => {
    setMenuAnchor(null)
    try {
      await auth.logout()
    } finally {
      queryClient.clear()
      await navigate({ to: '/' })
    }
  }

  const navItems: NavItem[] =
    auth.session.status !== 'authenticated'
      ? [{ label: 'Etkinlikleri keşfet', to: '/' }]
      : auth.session.user.role === 'organizer'
        ? [
            { label: 'Etkinliklerim', to: '/organizer/events' },
            { label: 'Yeni etkinlik', to: '/organizer/events/new' },
          ]
        : [
            { label: 'Etkinlikler', to: '/' },
            { label: 'Rezervasyonlarım', to: '/attendee/reservations' },
          ]

  const isActive = (to: NavItem['to']) =>
    to === '/'
      ? pathname === '/' || pathname.startsWith('/events/')
      : to === '/organizer/events'
        ? pathname === to ||
          (pathname.startsWith(`${to}/`) && !pathname.endsWith('/new'))
        : pathname === to

  const initials =
    auth.session.status === 'authenticated'
      ? auth.session.user.fullName
          .split(/\s+/)
          .slice(0, 2)
          .map((part) => part.charAt(0).toLocaleUpperCase('tr-TR'))
          .join('')
      : ''

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <AppBar position="sticky" color="inherit" elevation={0}>
        <Container
          maxWidth={false}
          sx={{ maxWidth: designTokens.layout.contentMaxWidth }}
        >
          <Toolbar
            disableGutters
            sx={{ gap: 2, minHeight: { xs: 64, md: 72 } }}
          >
            <Box
              component={Link}
              to="/"
              aria-label="EventFlow ana sayfa"
              sx={{
                color: 'text.primary',
                display: 'inline-flex',
                textDecoration: 'none',
              }}
            >
              <ProductMark />
            </Box>

            <Stack
              component="nav"
              aria-label="Ana navigasyon"
              direction="row"
              sx={{ display: { xs: 'none', md: 'flex' }, gap: 0.5, ml: 2 }}
            >
              {navItems.map((item) => (
                <NavButton
                  key={item.to}
                  item={item}
                  active={isActive(item.to)}
                />
              ))}
            </Stack>

            <Box sx={{ flexGrow: 1 }} />

            <Stack
              direction="row"
              sx={{
                alignItems: 'center',
                display: { xs: 'none', md: 'flex' },
                gap: 1,
              }}
            >
              {auth.session.status === 'authenticated' ? (
                <>
                  <Stack
                    direction="row"
                    sx={{ alignItems: 'center', gap: 1.1, pl: 1 }}
                  >
                    <Avatar
                      aria-hidden="true"
                      sx={{
                        bgcolor: 'action.selected',
                        color: 'primary.light',
                        fontSize: 13,
                        fontWeight: 850,
                        height: 36,
                        width: 36,
                      }}
                    >
                      {initials}
                    </Avatar>
                    <Box sx={{ maxWidth: 150 }}>
                      <Typography
                        noWrap
                        variant="body2"
                        sx={{ fontWeight: 750, lineHeight: 1.25 }}
                      >
                        {auth.session.user.fullName}
                      </Typography>
                      <Typography color="text.secondary" variant="caption">
                        {auth.session.user.role === 'organizer'
                          ? 'Organizatör'
                          : 'Katılımcı'}
                      </Typography>
                    </Box>
                  </Stack>
                  <Button
                    color="inherit"
                    onClick={() => void handleLogout()}
                    sx={{ color: 'text.secondary' }}
                  >
                    Çıkış yap
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    component={Link}
                    to="/login"
                    color="inherit"
                    sx={{ color: 'text.secondary' }}
                  >
                    Giriş yap
                  </Button>
                  <Button component={Link} to="/register" variant="contained">
                    Ücretsiz kaydol
                  </Button>
                </>
              )}
            </Stack>

            <IconButton
              aria-label="Menüyü aç"
              aria-controls={menuAnchor ? 'mobile-navigation' : undefined}
              aria-expanded={Boolean(menuAnchor)}
              onClick={(event) => setMenuAnchor(event.currentTarget)}
              sx={{ display: { md: 'none' }, height: 44, width: 44 }}
            >
              <Box
                aria-hidden="true"
                sx={{ display: 'grid', gap: '5px', width: 20 }}
              >
                {[0, 1, 2].map((line) => (
                  <Box
                    key={line}
                    sx={{ bgcolor: 'text.primary', borderRadius: 9, height: 2 }}
                  />
                ))}
              </Box>
            </IconButton>
            <Menu
              id="mobile-navigation"
              anchorEl={menuAnchor}
              open={Boolean(menuAnchor)}
              onClose={() => setMenuAnchor(null)}
              slotProps={{ list: { 'aria-label': 'Mobil navigasyon' } }}
            >
              {auth.session.status === 'authenticated' ? (
                <Box sx={{ px: 2, py: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 760 }}>
                    {auth.session.user.fullName}
                  </Typography>
                  <Typography color="text.secondary" variant="caption">
                    {auth.session.user.role === 'organizer'
                      ? 'Organizatör hesabı'
                      : 'Katılımcı hesabı'}
                  </Typography>
                </Box>
              ) : null}
              {auth.session.status === 'authenticated' ? (
                <Divider sx={{ my: 1 }} />
              ) : null}
              {navItems.map((item) => (
                <MenuItem
                  key={item.to}
                  component={Link}
                  to={item.to}
                  selected={isActive(item.to)}
                  onClick={() => setMenuAnchor(null)}
                >
                  {item.label}
                </MenuItem>
              ))}
              <Divider sx={{ my: 1 }} />
              {auth.session.status === 'authenticated' ? (
                <MenuItem onClick={() => void handleLogout()}>
                  Çıkış yap
                </MenuItem>
              ) : (
                <>
                  <MenuItem
                    component={Link}
                    to="/login"
                    onClick={() => setMenuAnchor(null)}
                  >
                    Giriş yap
                  </MenuItem>
                  <MenuItem
                    component={Link}
                    to="/register"
                    onClick={() => setMenuAnchor(null)}
                  >
                    Ücretsiz kaydol
                  </MenuItem>
                </>
              )}
            </Menu>
          </Toolbar>
        </Container>
      </AppBar>
      <Suspense
        fallback={
          <Container maxWidth="lg">
            <LoadingState label="Sayfa yükleniyor" />
          </Container>
        }
      >
        <Outlet />
      </Suspense>
    </Box>
  )
}
