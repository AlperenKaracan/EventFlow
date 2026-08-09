import { randomUUID } from 'node:crypto'

import { expect, type Page, test } from '@playwright/test'

const password = 'StrongPassword123!'

async function register(
  page: Page,
  user: { email: string; fullName: string; role: 'Katılımcı' | 'Organizatör' },
) {
  await page.goto('/register')
  await page.getByLabel('Ad soyad').fill(user.fullName)
  await page.getByLabel('E-posta').fill(user.email)
  await page.getByLabel('Şifre').fill(password)
  await page.getByLabel('Hesap türü').click()
  await page.getByRole('option', { name: user.role }).click()
  await page.getByRole('button', { name: 'Hesap oluştur' }).click()
  await expect(page.getByRole('button', { name: 'Çıkış yap' })).toBeVisible()
  await expect(
    page.getByRole('heading', {
      name: user.role === 'Organizatör' ? 'Etkinliklerim' : 'Yaklaşan etkinlikler',
    }),
  ).toBeVisible()
}

async function login(page: Page, email: string) {
  await page.goto('/login')
  await page.getByLabel('E-posta').fill(email)
  await page.getByLabel('Şifre').fill(password)
  await page.getByRole('button', { name: 'Giriş yap', exact: true }).click()
}

async function logout(page: Page) {
  await page.getByRole('button', { name: 'Çıkış yap' }).click()
  await expect(page).toHaveURL(/\/$/)
}

async function cancelActiveReservation(page: Page, eventTitle: string) {
  await page.goto('/attendee/reservations')
  await expect(page.getByRole('heading', { name: eventTitle })).toBeVisible()
  await page.getByRole('button', { name: 'Rezervasyonu iptal et' }).click()
  await expect(
    page.getByRole('button', { name: 'Yeniden yer ayır' }),
  ).toBeVisible()
}

test('P0 organizer and attendee lifecycle', async ({ page, browser }) => {
  test.setTimeout(120_000)
  const suffix = randomUUID().slice(0, 8)
  const organizer = {
    email: `organizer-${suffix}@example.com`,
    fullName: `Organizatör ${suffix}`,
  }
  const attendeeOne = {
    email: `attendee-one-${suffix}@example.com`,
    fullName: `Katılımcı Bir ${suffix}`,
  }
  const attendeeTwo = {
    email: `attendee-two-${suffix}@example.com`,
    fullName: `Katılımcı İki ${suffix}`,
  }
  const eventTitle = `P0 Kapasite ${suffix}`

  await register(page, { ...organizer, role: 'Organizatör' })
  await expect(
    page.getByRole('heading', { name: 'Etkinliklerim' }),
  ).toBeVisible()
  await page.getByRole('link', { name: 'Yeni etkinlik' }).click()
  await page.getByLabel('Kategori').click()
  await page.getByRole('option', { name: 'Teknoloji' }).click()
  await page.getByLabel('Başlık').fill(eventTitle)
  await page
    .getByLabel('Açıklama')
    .fill('P0 tarayıcı yolculuğu için izole etkinlik.')
  await page.getByLabel('Konum').fill('İstanbul')
  await page.getByLabel('Başlangıç').fill('2035-09-20T19:30')
  await page.getByLabel('IANA saat dilimi').fill('Europe/Istanbul')
  await page.getByLabel('Kapasite').fill('1')
  await page.getByRole('button', { name: 'Kaydet' }).click()
  await expect(page).toHaveURL(/\/organizer\/events\/[^/]+\/edit$/)
  const eventId = new URL(page.url()).pathname.split('/')[3]
  const updatedTitle = `${eventTitle} Güncel`
  await page.getByLabel('Başlık').fill(updatedTitle)
  await page.getByRole('button', { name: 'Kaydet' }).click()
  await expect(page.getByLabel('Başlık')).toHaveValue(updatedTitle)
  await logout(page)

  await register(page, { ...attendeeOne, role: 'Katılımcı' })
  await expect(
    page.getByRole('heading', { name: 'Yaklaşan etkinlikler' }),
  ).toBeVisible()
  await page.goto(`/events/${eventId}`)
  await page.getByRole('button', { name: 'Yer ayır', exact: true }).click()
  await expect(page.getByText('Yeriniz ayrıldı.')).toBeVisible()

  await page.reload()
  await expect(page.getByRole('button', { name: 'Kontenjan dolu' })).toBeDisabled()

  await cancelActiveReservation(page, updatedTitle)
  await page.getByRole('button', { name: 'Yeniden yer ayır' }).click()
  await expect(
    page.getByText('Etkinlik için yeniden yer ayırdınız.'),
  ).toBeVisible()
  await cancelActiveReservation(page, updatedTitle)
  await logout(page)

  const secondContext = await browser.newContext()
  const secondPage = await secondContext.newPage()
  await register(secondPage, { ...attendeeTwo, role: 'Katılımcı' })
  await secondPage.goto(`/events/${eventId}`)
  await secondPage
    .getByRole('button', { name: 'Yer ayır', exact: true })
    .click()
  await expect(secondPage.getByText('Yeriniz ayrıldı.')).toBeVisible()
  await secondContext.close()

  await login(page, attendeeOne.email)
  await expect(
    page.getByRole('heading', { name: 'Yaklaşan etkinlikler' }),
  ).toBeVisible()
  await page.goto('/attendee/reservations')
  await page.getByRole('button', { name: 'Yeniden yer ayır' }).click()
  await expect(page.getByText('İstek tamamlanamadı')).toBeVisible()
  await expect(page.getByText(/İstek kimliği:/)).toBeVisible()

  await page.goto('/organizer/events')
  await expect(
    page.getByRole('heading', { name: 'Bu işlem için yetkiniz yok' }),
  ).toBeVisible()
  await logout(page)
  await page.goto('/attendee/reservations')
  await expect(page).toHaveURL(/\/login$/)

  await login(page, organizer.email)
  await expect(
    page.getByRole('heading', { name: 'Etkinliklerim' }),
  ).toBeVisible()
  await page.goto(`/organizer/events/${eventId}/attendees`)
  await expect(page.getByText(attendeeTwo.fullName)).toBeVisible()
  await expect(page.getByText(attendeeTwo.email)).toBeVisible()
  await page.goto('/organizer/events')
  await page.getByRole('button', { name: 'İptal et' }).click()
  const dialog = page.getByRole('dialog', { name: 'Etkinliği iptal et' })
  await dialog.getByRole('button', { name: 'İptal et' }).click()
  await expect(page.getByText('İptal edildi')).toBeVisible()
})
