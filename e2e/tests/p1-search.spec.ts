import { expect, type Locator, test } from '@playwright/test'

async function fillDate(
  group: Locator,
  value: { day: string; month: string; year: string },
) {
  await group.getByRole('spinbutton', { name: 'Day' }).fill(value.day)
  await group.getByRole('spinbutton', { name: 'Month' }).fill(value.month)
  await group.getByRole('spinbutton', { name: 'Year' }).fill(value.year)
}

test('P1 event search, category, and local date filters', async ({ page }) => {
  await page.goto('/')
  await expect(
    page.getByRole('heading', { name: 'Yaklaşan etkinlikler' }),
  ).toBeVisible()

  const filters = page.getByRole('form', { name: 'Etkinlikleri filtrele' })
  await filters.getByRole('textbox', { name: 'Etkinlik ara' }).fill('yazılım')
  await filters.getByRole('combobox', { name: 'Kategori' }).click()
  await page.getByRole('option', { name: 'Eğitim' }).click()
  await fillDate(filters.getByRole('group', { name: 'Başlangıç tarihi' }), {
    day: '18',
    month: '06',
    year: '2035',
  })
  await fillDate(filters.getByRole('group', { name: 'Bitiş tarihi' }), {
    day: '18',
    month: '06',
    year: '2035',
  })

  const filteredResponse = page.waitForResponse((response) => {
    const url = new URL(response.url())
    return (
      url.pathname === '/api/v1/events' &&
      url.searchParams.get('q') === 'yazılım' &&
      url.searchParams.get('category') === 'egitim' &&
      url.searchParams.get('dateFrom') === '2035-06-18' &&
      url.searchParams.get('dateTo') === '2035-06-18'
    )
  })
  await filters.getByRole('button', { name: 'Sonuçları göster' }).click()
  expect((await filteredResponse).status()).toBe(200)

  await expect(
    page.getByRole('heading', { name: 'Berlin Yazılım Atölyesi' }),
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'İstanbul Teknoloji Buluşması' }),
  ).toHaveCount(0)
  await expect(page.getByText('1 etkinlik listeleniyor')).toBeVisible()

  await filters.getByRole('button', { name: 'Filtreleri temizle' }).click()
  await expect(
    page.getByRole('heading', { name: 'İstanbul Teknoloji Buluşması' }),
  ).toBeVisible()
})
