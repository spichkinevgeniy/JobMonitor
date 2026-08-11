import { expect, test } from '@playwright/test'

const widths = [320, 375, 390]

test('dashboard remains compact without horizontal overflow', async ({ page }) => {
  await page.route('https://telegram.org/**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'text/javascript', body: '' })
  })
  await page.addInitScript(() => {
    Object.assign(window, {
      Telegram: {
        WebApp: {
          initData: 'test-init-data',
          ready: () => undefined,
          expand: () => undefined,
        },
      },
    })
  })
  await page.route('**/miniapp/api/search-profile', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        specializations: ['Инженер по информационной безопасности'],
        skills: [
          'React',
          'TypeScript',
          'Redux Toolkit',
          'JavaScript',
          'Next.js',
          'HTML',
          'CSS',
          'Sass',
          'Docker',
          'Git',
          'Webpack',
          'Vite',
        ],
        work_formats: ['REMOTE'],
        salary: { mode: 'FROM', amount_rub: 150000 },
        level: { grade: 'JUNIOR', mode: 'AT_LEAST' },
        search_active: true,
      }),
    })
  })

  for (const width of widths) {
    await page.setViewportSize({ width, height: 720 })
    await page.goto('/miniapp/dashboard/')

    const title = page.getByRole('heading', {
      name: 'Инженер по информационной безопасности',
    })
    const edit = page.getByRole('button', { name: /Изменить/ })
    const profileCard = page.locator(
      'section[aria-labelledby="active-profile-title"]',
    )

    await expect(title).toBeVisible()
    await expect(edit).toBeVisible()
    await expect(page.getByLabel('Ещё 9 навыков')).toBeVisible()

    const hasHorizontalOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > window.innerWidth,
    )
    expect(hasHorizontalOverflow, `${width}px viewport overflowed`).toBe(false)

    const titleBox = await title.boundingBox()
    const editBox = await edit.boundingBox()
    const cardBox = await profileCard.boundingBox()

    expect(titleBox).not.toBeNull()
    expect(editBox).not.toBeNull()
    expect(cardBox).not.toBeNull()
    expect(editBox!.y).toBeGreaterThanOrEqual(titleBox!.y + titleBox!.height)
    expect(cardBox!.width).toBeLessThanOrEqual(width - 32)
    expect(cardBox!.height).toBeLessThan(300)
  }
})
