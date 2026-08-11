import { expect, test } from '@playwright/test'

const viewports = [
  { width: 360, height: 800 },
  { width: 390, height: 844 },
  { width: 412, height: 915 },
  { width: 768, height: 1024 },
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
  { width: 1920, height: 1080 },
] as const

test('public discovery fits every target viewport without horizontal overflow', async ({
  page,
}, testInfo) => {
  test.skip(
    testInfo.project.name !== 'desktop-chrome',
    'Viewport matrix is exercised once.',
  )

  for (const viewport of viewports) {
    await page.setViewportSize(viewport)
    await page.goto('/')
    await expect(
      page.getByRole('heading', { name: 'Yaklaşan etkinlikler' }),
    ).toBeVisible()

    const layout = await page.evaluate(() => ({
      documentWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    }))
    expect(
      layout.documentWidth,
      `${viewport.width}x${viewport.height} genişliğinde taşma`,
    ).toBeLessThanOrEqual(layout.viewportWidth)
  }
})

test('mobile navigation exposes the primary destinations by keyboard', async ({
  page,
}, testInfo) => {
  test.skip(
    testInfo.project.name !== 'mobile-chrome',
    'Mobile navigation is exercised once.',
  )

  await page.goto('/')
  const menuButton = page.getByRole('button', { name: 'Menüyü aç' })
  await menuButton.focus()
  await expect(menuButton).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(
    page.getByRole('menuitem', { name: 'Etkinlikleri keşfet' }),
  ).toBeVisible()
  await expect(page.getByRole('menuitem', { name: 'Giriş yap' })).toBeVisible()
  await expect(
    page.getByRole('menuitem', { name: 'Ücretsiz kaydol' }),
  ).toBeVisible()
})
