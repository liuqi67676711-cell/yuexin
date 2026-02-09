/**
 * Vercel Serverless Function - 動態路由代理
 * 捕獲所有 /api/* 路徑的請求並代理到後端
 * 
 * 使用方式：前端請求 /api/popular/everyone-watching
 * 會被代理到 http://120.55.36.217/api/popular/everyone-watching
 */

// ECS 後端地址（從環境變數讀取）
const BACKEND_URL = process.env.BACKEND_URL || 'http://120.55.36.217';

export default async function handler(request: Request) {
  // 處理 CORS 預檢請求
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS, PATCH',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '86400',
      },
    });
  }

  if (!['GET', 'POST', 'PUT', 'DELETE', 'PATCH'].includes(request.method)) {
    return new Response(
      JSON.stringify({ error: 'Method not allowed' }),
      {
        status: 405,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      }
    );
  }

  try {
    // 從 URL 中提取路徑
    const url = new URL(request.url);
    // 移除 /api 前綴，保留後面的路徑
    const path = url.pathname.replace(/^\/api/, '') || '/';
    
    // 構建後端 URL
    const backendUrl = `${BACKEND_URL}${path}${url.search}`;
    
    // 構建請求選項
    const fetchOptions: RequestInit = {
      method: request.method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    // 如果有請求體，添加到選項中
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      try {
        const body = await request.text();
        if (body) {
          fetchOptions.body = body;
        }
      } catch {
        // 如果讀取 body 失敗，忽略
      }
    }

    // 發送請求到後端
    const response = await fetch(backendUrl, fetchOptions);
    
    // 讀取響應數據
    const data = await response.text();
    
    // 嘗試解析 JSON
    let jsonData: any;
    try {
      jsonData = JSON.parse(data);
    } catch {
      jsonData = data;
    }

    // 返回響應，設置 CORS 頭
    return new Response(
      typeof jsonData === 'string' ? jsonData : JSON.stringify(jsonData),
      {
        status: response.status,
        headers: {
          'Content-Type': response.headers.get('Content-Type') || 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS, PATCH',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
      }
    );
  } catch (error: any) {
    console.error('代理請求失敗:', error);
    return new Response(
      JSON.stringify({
        error: '代理請求失敗',
        message: error.message,
      }),
      {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      }
    );
  }
}
