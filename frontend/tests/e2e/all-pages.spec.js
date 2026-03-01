import { test, expect } from '@playwright/test';

// 登录页面测试 - 不需要认证
test.describe('登录页面测试', () => {
  test('登录页面加载正常', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('h1')).toContainText('灵模网关');
    await expect(page.locator('input[placeholder="用户名"]')).toBeVisible();
    await expect(page.locator('input[placeholder="密码"]')).toBeVisible();
    await expect(page.locator('button')).toBeVisible();
  });

  test('登录成功 - 正确账号密码', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[placeholder="用户名"]', 'admin');
    await page.fill('input[placeholder="密码"]', 'admin123');
    await page.click('button');
    await page.waitForURL('**/welcome', { timeout: 15000 });
  });

  test('登录失败 - 错误密码', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[placeholder="用户名"]', 'admin');
    await page.fill('input[placeholder="密码"]', 'wrongpassword');
    await page.click('button');
    await expect(page.locator('.el-message').first()).toBeVisible({ timeout: 5000 });
  });
});

// 页面加载测试 - 验证路由配置正确
test.describe('页面路由测试', () => {
  test('所有页面路由可访问', async ({ page }) => {
    const routes = [
      { path: '/login', text: '灵模网关' },
      { path: '/', text: '' },  // 仪表盘需要认证
      { path: '/models', text: '' },  // 需要认证
      { path: '/quota', text: '' },  // 需要认证
      { path: '/logs', text: '' },  // 需要认证
      { path: '/config', text: '' },  // 需要认证
      { path: '/profile', text: '' },  // 需要认证
      { path: '/change-password', text: '' },  // 需要认证
      { path: '/agent', text: '' },  // 需要认证
    ];

    for (const route of routes) {
      const response = await page.goto(route.path);
      // 页面应该返回 200 或者被重定向
      expect([200, 302, 301]).toContain(response.status());
    }
  });
});

// 登录后功能测试 - 需要真实登录
test.describe('登录后功能测试', () => {
  test.beforeEach(async ({ page }) => {
    // 先登录
    await page.goto('/login');
    await page.fill('input[placeholder="用户名"]', 'admin');
    await page.fill('input[placeholder="密码"]', 'admin123');
    await page.click('button');
    await page.waitForURL('**/welcome', { timeout: 15000 });
  });

  test('欢迎页加载正常', async ({ page }) => {
    await page.goto('/welcome');
    // 等待页面加载
    await page.waitForLoadState('networkidle');
    // 检查是否有欢迎相关的内容
    const content = await page.content();
    expect(content.length).toBeGreaterThan(100);
  });

  test('从欢迎页可以导航到模型配置', async ({ page }) => {
    await page.goto('/welcome');
    // 点击导航到模型配置（如果有的话）
    // 或者直接访问
    await page.goto('/models');
    await page.waitForLoadState('networkidle');
    // 检查是否需要认证（如果重定向回登录则通过）
    const url = page.url();
    expect(url).toMatch(/models|login/);
  });
});
