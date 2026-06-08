/** API 请求封装 */
import axios from 'axios';

const http = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// 响应拦截器 — 直接返回 data
http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    console.error('API Error:', err.message);
    return Promise.reject(err);
  }
);

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const api = {
  get: <T = any>(url: string, config?: any): Promise<T> => http.get(url, config) as any,
  post: <T = any>(url: string, data?: any, config?: any): Promise<T> => http.post(url, data, config) as any,
  put: <T = any>(url: string, data?: any, config?: any): Promise<T> => http.put(url, data, config) as any,
  delete: <T = any>(url: string, config?: any): Promise<T> => http.delete(url, config) as any,
};

// ========== Dashboard ==========
export const getKPIs = () => api.get('/dashboard/kpis');
export const getTrends = () => api.get('/dashboard/trends');
export const getSupplierDist = () => api.get('/dashboard/supplier-distribution');
export const getOrderStatus = () => api.get('/dashboard/order-status');

// ========== Suppliers ==========
export const getSuppliers = (params?: any) => api.get('/suppliers/', { params });
export const getSupplierScore = (id: number) => api.get(`/suppliers/${id}/score`);
export const getSupplierRanking = () => api.get('/suppliers/ranking/list');
export const createSupplier = (data: any) => api.post('/suppliers/', data);
export const deleteSupplier = (id: number) => api.delete(`/suppliers/${id}`);

// ========== Products ==========
export const getProducts = (params?: any) => api.get('/products/', { params });
export const getCategories = () => api.get('/products/categories');

// ========== Inventory ==========
export const getInventory = (params?: any) => api.get('/inventory/', { params });
export const getInventorySummary = () => api.get('/inventory/summary');
export const getWarehouses = () => api.get('/inventory/warehouses');

// ========== Orders ==========
export const getOrders = (params?: any) => api.get('/orders/', { params });
export const createOrder = (data: any) => api.post('/orders/', data);
export const updateOrderStatus = (id: number, status: string) =>
  api.put(`/orders/${id}/status?status=${status}`);

// ========== Shipments ==========
export const getShipments = (params?: any) => api.get('/shipments/', { params });
export const getShipmentMap = () => api.get('/shipments/map');
export const getShipmentStats = () => api.get('/shipments/stats');

// ========== Forecast ==========
export const getDemandForecast = (productId?: number) =>
  api.get('/forecast/demand', { params: productId ? { product_id: productId } : {} });

// ========== Risks ==========
export const getRisks = (params?: any) => api.get('/risks/', { params });
export const getRiskSummary = () => api.get('/risks/summary');
export const getRiskHeatmap = () => api.get('/risks/heatmap');
export const detectRisks = () => api.post('/risks/detect');
export const getAnomalies = () => api.get('/risks/anomalies');
export const updateAlertStatus = (id: number, status: string) =>
  api.put(`/risks/${id}/status?status=${status}`);

// ========== Analytics ==========
export const getLogisticsAnalysis = () => api.get('/analytics/logistics');
export const getCostAnalysis = () => api.get('/analytics/cost');
export const getSupplierPerformance = () => api.get('/analytics/supplier-performance');
