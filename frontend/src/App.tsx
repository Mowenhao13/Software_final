import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import MainLayout from './components/Layout/MainLayout';
import Dashboard from './pages/Dashboard';
import SupplyChain from './pages/SupplyChain';
import Suppliers from './pages/Suppliers';
import Inventory from './pages/Inventory';
import Orders from './pages/Orders';
import Logistics from './pages/Logistics';
import RiskMonitor from './pages/RiskMonitor';
import Analytics from './pages/Analytics';

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
            <Route path="/suppliers" element={<Suppliers />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/logistics" element={<Logistics />} />
            <Route path="/risk-monitor" element={<RiskMonitor />} />
            <Route path="/analytics" element={<Analytics />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}
