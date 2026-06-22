import React, { useState, useEffect, useCallback } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Badge, Typography, Tag, Select, message } from 'antd';
import {
  DashboardOutlined, NodeIndexOutlined, LineChartOutlined,
  ApartmentOutlined, WarningOutlined,
} from '@ant-design/icons';
import { realtimeClient } from '../../utils/websocket';
import { getDatasets, switchDataset } from '../../api';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/supply-chain', icon: <NodeIndexOutlined />, label: '供应链全景' },
  { key: '/forecast', icon: <LineChartOutlined />, label: '需求预测' },
  { key: '/route-planner', icon: <ApartmentOutlined />, label: '路径规划' },
  { key: '/risk-monitor', icon: <WarningOutlined />, label: '风险监控' },
];

interface DatasetOption {
  id: string;
  name: string;
  description: string;
  items: number;
}

export default function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [wsData, setWsData] = useState<any>({});
  const [currentTime, setCurrentTime] = useState(new Date());
  const [datasets, setDatasets] = useState<DatasetOption[]>([]);
  const [activeDataset, setActiveDataset] = useState('');
  const [switching, setSwitching] = useState(false);

  const loadDatasets = useCallback(async () => {
    try {
      const res: any = await getDatasets();
      setDatasets(res.datasets || []);
      setActiveDataset(res.active?.id || res.active?.active || '');
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    realtimeClient.connect();
    const unsub = realtimeClient.onMessage((data) => setWsData(data));
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    loadDatasets();
    return () => {
      unsub();
      realtimeClient.disconnect();
      clearInterval(timer);
    };
  }, [loadDatasets]);

  const handleDatasetChange = async (value: string) => {
    setSwitching(true);
    try {
      await switchDataset(value);
      message.success(`已切换到数据集: ${datasets.find(d => d.id === value)?.name || value}`);
      // 刷新页面以重新加载所有数据
      setTimeout(() => window.location.reload(), 500);
    } catch {
      message.error('切换数据集失败');
      setSwitching(false);
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={220} theme="dark" style={{ position: 'fixed', left: 0, top: 0, bottom: 0, zIndex: 100 }}>
        <div style={{
          height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center',
          borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: 8,
        }}>
          <DashboardOutlined style={{ fontSize: 24, color: '#1890ff', marginRight: 10 }} />
          <Typography.Text style={{ color: '#fff', fontSize: 15, fontWeight: 700, whiteSpace: 'nowrap' }}>
            AI供应链分析
          </Typography.Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout style={{ marginLeft: 220 }}>
        <Header style={{
          background: '#fff', padding: '0 24px', display: 'flex',
          alignItems: 'center', justifyContent: 'space-between',
          boxShadow: '0 1px 4px rgba(0,0,0,0.08)', position: 'sticky', top: 0, zIndex: 99,
        }}>
          <Typography.Title level={5} style={{ margin: 0 }}>
            AI 赋能企业供应链的可视化分析系统
          </Typography.Title>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 14 }}>
            <Select
              value={activeDataset || undefined}
              onChange={handleDatasetChange}
              loading={switching}
              style={{ width: 200 }}
              placeholder="选择数据集"
              options={datasets.map(d => ({
                value: d.id,
                label: `${d.name} (${d.items}种商品)`,
              }))}
            />
            <Tag color="blue">实时监控中</Tag>
            <span style={{ color: '#666' }}>{currentTime.toLocaleString('zh-CN')}</span>
            {wsData?.active_alerts > 0 && (
              <Badge count={wsData.active_alerts} size="small" offset={[4, -2]}>
                <DashboardOutlined style={{ fontSize: 18, color: '#faad14' }} />
              </Badge>
            )}
          </div>
        </Header>
        <Content style={{ margin: 16, minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}