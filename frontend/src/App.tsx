import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import MainLayout from './components/Layout/MainLayout';
import Dashboard from './pages/Dashboard';
import SupplyChain from './pages/SupplyChain';
import ForecastBoard from './pages/ForecastBoard';
import RoutePlanner from './pages/RoutePlanner';
import RiskMonitor from './pages/RiskMonitor';

export default function App() {
  return (
    <ConfigProvider locale={zhCN} theme={{
      token: {
        colorPrimary: '#1890ff',
        borderRadius: 6,
      },
    }}>
      <BrowserRouter>
        <Routes>
          <Route element={<MainLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/supply-chain" element={<SupplyChain />} />
            <Route path="/forecast" element={<ForecastBoard />} />
            <Route path="/route-planner" element={<RoutePlanner />} />
            <Route path="/risk-monitor" element={<RiskMonitor />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}