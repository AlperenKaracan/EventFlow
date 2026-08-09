import { expect, test } from '@playwright/test'

test('serves the EventFlow foundation', async ({ page }) => {
  await page.goto('/')

  await expect(
    page.getByRole('heading', { name: /etkinlik rezervasyonu/i }),
  ).toBeVisible()
  await expect(page.getByRole('status')).toContainText('Frontend çalışıyor')
})
