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
  await page.getByRole('radio', { name: new RegExp(`^${user.role}`) }).check()
  await page.getByRole('button', { name: 'Hesap oluştur' }).click()
  await expect(
    page.getByRole('heading', {
      name:
        user.role === 'Organizatör' ? 'Etkinliklerim' : 'Yaklaşan etkinlikler',
    }),
  ).toBeVisible({ timeout: 15_000 })
}

async function login(page: Page, email: string) {
  await page.goto('/login')
  await page.getByLabel('E-posta').fill(email)
  await page.getByLabel('Şifre').fill(password)
  await page.getByRole('button', { name: 'Giriş yap', exact: true }).click()
  await expect(page).not.toHaveURL(/\/login$/)
}

async function logout(page: Page) {
  const desktopLogout = page.getByRole('button', { name: 'Çıkış yap' })
  if (await desktopLogout.isVisible()) {
    await desktopLogout.click()
  } else {
    await page.getByRole('button', { name: 'Menüyü aç' }).click()
    await page.getByRole('menuitem', { name: 'Çıkış yap' }).click()
  }
  await expect(page).toHaveURL(/\/$/)
}

async function cancelActiveReservation(page: Page, eventTitle: string) {
  await page.goto('/attendee/reservations')
  await expect(page.getByRole('heading', { name: eventTitle })).toBeVisible()
  await page.getByRole('button', { name: 'Rezervasyonu iptal et' }).click()
  const dialog = page.getByRole('dialog', {
    name: 'Rezervasyonu iptal etmek istiyor musunuz?',
  })
  await dialog.getByRole('button', { name: 'Rezervasyonu iptal et' }).click()
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
  await page
    .getByRole('link', { name: /Yeni etkinlik/ })
    .last()
    .click()
  await page.getByLabel('Kategori').click()
  await page.getByRole('option', { name: 'Teknoloji' }).click()
  await page.getByLabel('Başlık').fill(eventTitle)
  await page
    .getByLabel('Açıklama')
    .fill('P0 tarayıcı yolculuğu için izole etkinlik.')
  await page.getByLabel('Konum veya platform').fill('İstanbul')
  await page.getByLabel('Saat dilimi').click()
  await page.getByRole('option', { name: /^İstanbul - Türkiye saati/ }).click()
  const startsAtField = page.getByRole('group', {
    name: 'Başlangıç tarihi ve saati',
  })
  await startsAtField.getByRole('spinbutton', { name: 'Day' }).fill('20')
  await startsAtField.getByRole('spinbutton', { name: 'Month' }).fill('09')
  await startsAtField.getByRole('spinbutton', { name: 'Year' }).fill('2035')
  await startsAtField.getByRole('spinbutton', { name: 'Hours' }).fill('19')
  await startsAtField.getByRole('spinbutton', { name: 'Minutes' }).fill('30')
  await page.getByLabel('Kontenjan').fill('1')
  await page.getByRole('button', { name: 'Kaydet ve yayınla' }).click()
  await expect(
    page.getByText(
      'Etkinlik oluşturuldu. Etkinliklerim sayfasına yönlendirildiniz.',
    ),
  ).toBeVisible()
  await expect(page).toHaveURL(/\/organizer\/events$/)
  const createdEventCard = page.getByRole('article').filter({
    hasText: eventTitle,
  })
  await createdEventCard
    .getByRole('link', { name: 'Etkinliği düzenle' })
    .click()
  await expect(page).toHaveURL(/\/organizer\/events\/[^/]+\/edit$/)
  const eventId = new URL(page.url()).pathname.split('/')[3]
  await page.reload()
  await expect(page.getByLabel('Saat dilimi')).toHaveValue(
    'İstanbul - Türkiye saati (UTC+03:00)',
  )
  const persistedStartsAtField = page.getByRole('group', {
    name: 'Başlangıç tarihi ve saati',
  })
  await expect(
    persistedStartsAtField.getByRole('spinbutton', { name: 'Day' }),
  ).toHaveText('20')
  await expect(
    persistedStartsAtField.getByRole('spinbutton', { name: 'Month' }),
  ).toHaveText('09')
  await expect(
    persistedStartsAtField.getByRole('spinbutton', { name: 'Year' }),
  ).toHaveText('2035')
  await expect(
    persistedStartsAtField.getByRole('spinbutton', { name: 'Hours' }),
  ).toHaveText('19')
  await expect(
    persistedStartsAtField.getByRole('spinbutton', { name: 'Minutes' }),
  ).toHaveText('30')
  const stalePage = await page.context().newPage()
  await stalePage.goto(`/organizer/events/${eventId}/edit`)
  await expect(stalePage.getByLabel('Başlık')).toHaveValue(eventTitle)
  const updatedTitle = `${eventTitle} Güncel`
  await page.getByLabel('Başlık').fill(updatedTitle)
  await page.getByRole('button', { name: 'Değişiklikleri kaydet' }).click()
  await expect(page.getByLabel('Başlık')).toHaveValue(updatedTitle)
  await stalePage.getByLabel('Konum veya platform').fill('Ankara')
  await stalePage.getByRole('button', { name: 'Değişiklikleri kaydet' }).click()
  const conflictDialog = stalePage.getByRole('dialog', {
    name: 'Etkinlik başka bir yerde güncellendi',
  })
  await expect(conflictDialog).toBeVisible()
  await expect(conflictDialog.getByText(/Kaydınız uygulanmadı/)).toBeVisible()
  await expect(conflictDialog.getByText(/İstek kimliği:/)).toHaveCount(0)
  await conflictDialog
    .getByRole('button', { name: 'Güncel veriyi yükle' })
    .click()
  await expect(stalePage.getByLabel('Başlık')).toHaveValue(updatedTitle)
  await stalePage.close()
  await logout(page)

  await register(page, { ...attendeeOne, role: 'Katılımcı' })
  await expect(
    page.getByRole('heading', { name: 'Yaklaşan etkinlikler' }),
  ).toBeVisible()
  await page.goto(`/events/${eventId}`)
  await page.getByRole('button', { name: 'Yerimi ayır' }).click()
  await page.getByRole('button', { name: 'Rezervasyonu onayla' }).click()
  await expect(page.getByText(/Yeriniz ayrıldı/)).toBeVisible()

  await page.reload()
  await expect(
    page.getByRole('button', { name: 'Kontenjan dolu' }),
  ).toBeDisabled()

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
  await secondPage.getByRole('button', { name: 'Yerimi ayır' }).click()
  await secondPage.getByRole('button', { name: 'Rezervasyonu onayla' }).click()
  await expect(secondPage.getByText(/Yeriniz ayrıldı/)).toBeVisible()
  await secondContext.close()

  await login(page, attendeeOne.email)
  await expect(
    page.getByRole('heading', { name: 'Yaklaşan etkinlikler' }),
  ).toBeVisible()
  await page.goto('/attendee/reservations')
  await page.getByRole('button', { name: 'Yeniden yer ayır' }).click()
  await expect(page.getByText('Etkinlikte yer kalmadı')).toBeVisible()
  await expect(page.getByText(/İstek kimliği:/)).toHaveCount(0)

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
  await expect(
    page.getByText(attendeeTwo.fullName).filter({ visible: true }),
  ).toBeVisible()
  await expect(
    page.getByText(attendeeTwo.email).filter({ visible: true }),
  ).toBeVisible()
  await page.goto('/organizer/events')
  await page
    .getByRole('article')
    .filter({ hasText: updatedTitle })
    .getByRole('button', { name: 'Etkinliği iptal et' })
    .click()
  const dialog = page.getByRole('dialog', {
    name: 'Etkinliği iptal etmek istiyor musunuz?',
  })
  await dialog.getByRole('button', { name: 'Etkinliği iptal et' }).click()
  await expect(page.getByText('İptal edildi')).toBeVisible()

  const cancelledEventCard = page.getByRole('article').filter({
    hasText: updatedTitle,
  })
  await cancelledEventCard
    .getByRole('link', { name: 'Kaydı görüntüle' })
    .click()
  await expect(
    page.getByRole('heading', { name: 'İptal edilen etkinlik' }),
  ).toBeVisible()
  await expect(page.getByText(/bilgileri artık değiştirilemez/)).toBeVisible()
  await expect(page.getByLabel('Başlık')).toBeDisabled()
  await expect(
    page.getByRole('button', { name: 'İptal edildi' }),
  ).toBeDisabled()

  await logout(page)
  await login(page, attendeeTwo.email)
  await page.goto('/attendee/reservations')
  const cancelledReservationCard = page.getByRole('article').filter({
    hasText: updatedTitle,
  })
  await expect(
    cancelledReservationCard.getByText(/Organizatör bu etkinliği iptal etti/),
  ).toBeVisible()
  await expect(
    cancelledReservationCard.getByRole('button', {
      name: 'Etkinlik iptal edildi',
    }),
  ).toBeDisabled()
  await expect(
    cancelledReservationCard.getByRole('link', { name: 'Etkinlik' }),
  ).toHaveCount(0)
})

test('reservation survives a lost response without duplication', async ({
  page,
}) => {
  const suffix = randomUUID().slice(0, 8)
  const attendee = {
    email: `network-loss-${suffix}@example.com`,
    fullName: `Ağ Kaybı ${suffix}`,
  }
  const eventId = '30000000-0000-7000-8000-000000000004'
  const idempotencyKeys: string[] = []
  let committedResponseWasLost = false

  await register(page, { ...attendee, role: 'Katılımcı' })
  await page.route(
    `**/api/v1/events/${eventId}/reservations`,
    async (route) => {
      if (route.request().method() !== 'POST') {
        await route.continue()
        return
      }

      const key = route.request().headers()['idempotency-key']
      expect(key).toBeTruthy()
      idempotencyKeys.push(key)

      if (!committedResponseWasLost) {
        committedResponseWasLost = true
        const response = await route.fetch()
        expect(response.status()).toBe(201)
        await route.abort('failed')
        return
      }

      await route.continue()
    },
  )

  await page.goto(`/events/${eventId}`)
  await page.getByRole('button', { name: 'Yerimi ayır' }).click()
  await page.getByRole('button', { name: 'Rezervasyonu onayla' }).click()
  await expect(page.getByText(/Yeriniz ayrıldı/)).toBeVisible()
  expect(idempotencyKeys).toHaveLength(2)
  expect(new Set(idempotencyKeys).size).toBe(1)

  await page.goto('/attendee/reservations')
  const reservationCard = page.getByRole('article').filter({
    hasText: 'Boş Kontenjanlı Koşu',
  })
  await expect(reservationCard).toHaveCount(1)
  await expect(
    reservationCard.getByRole('button', { name: 'Rezervasyonu iptal et' }),
  ).toBeEnabled()
})
