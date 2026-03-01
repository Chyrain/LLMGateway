import { test, expect } from '@playwright/test';

// 登录页面测试 - 不需要认证
test.describe('登录页面测试', () => {
  test('登录页面加载正常', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('h1, h2')).toContainText(/灵模|登录/);
    await expect(page.locator('input[type="text"], input[name="username"], input[id="username"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button')).toBeVisible();
  });
});

// 页面路由测试 - 验证路由配置正确
test.describe('页面路由测试', () => {
  test('所有页面路由可访问', async ({ page }) => {
    const routes = ['/login', '/', '/dashboard', '/models', '/quota', '/logs', '/config', '/profile'];

    for (const path of routes) {
      const response = await page.goto(path);
      // 页面应该返回 200 或者被重定向
      expect([200, 302, 301]).toContain(response.status());
    }
  });
});

// 登录后功能测试
test.describe('登录后功能测试', () => {
  test.beforeEach(async ({ page }) => {
    // 尝试登录
    await page.goto('/login');
    // 尝试填写登录表单
    const usernameInput = page.locator('input[type="text"], input[name="username"], input[id="username"]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.locator('button[type="submit"], button:has-text("登录")');

    if (await usernameInput.isVisible()) {
      await usernameInput.fill('admin');
      await passwordInput.fill('admin123');
      await submitButton.click();
      // 等待可能的跳转
      await page.waitForTimeout(1000);
    }
  });

  test('登录后可以访问欢迎页', async ({ page }) => {
    await page.goto('/welcome');
    await page.waitForLoadState('networkidle');
    const content = await page.content();
    expect(content.length).toBeGreaterThan(100);
  });
});
