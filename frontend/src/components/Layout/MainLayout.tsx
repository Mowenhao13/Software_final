import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Badge, Typography, Tag } from 'antd';
import {
  DashboardOutlined, NodeIndexOutlined, TeamOutlined, InboxOutlined,
  ShoppingCartOutlined, CarOutlined, AlertOutlined, BarChartOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { realtimeClient } from '../../utils/websocket';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/supply-chain', icon: <NodeIndexOutlined />, label: '供应链全景' },
  { key: '/suppliers', icon: <TeamOutlined />, label: '供应商管理' },
  { key: '/inventory', icon: <InboxOutlined />, label: '库存管理' },
  { key: '/orders', icon: <ShoppingCartOutlined />, label: '订单管理' },
  { key: '/logistics', icon: <CarOutlined />, label: '物流追踪' },
  { key: '/risk-monitor', icon: <AlertOutlined />, label: '风险监控' },
  { key: '/analytics', icon: <BarChartOutlined />, label: '分析报表' },
];

export default function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [wsData, setWsData] = useState<any>({});
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    realtimeClient.connect();
    const unsub = realtimeClient.onMessage((data) => setWsData(data));

    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => {
      unsub();
      realtimeClient.disconnect();
      clearInterval(timer);
    };
  }, []);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={220} theme="dark" style={{ position: 'fixed', left: 0, top: 0, bottom: 0, zIndex: 100 }}>
        <div style={{
          height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center',
          borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: 8,
        }}>
          <ThunderboltOutlined style={{ fontSize: 24, color: '#1890ff', marginRight: 10 }} />
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
            <Tag color="blue">实时监控中</Tag>
            <span style={{ color: '#666' }}>{currentTime.toLocaleString('zh-CN')}</span>
            {wsData?.active_alerts > 0 && (
              <Badge count={wsData.active_alerts} size="small" offset={[4, -2]}>
                <AlertOutlined style={{ fontSize: 18, color: '#faad14' }} />
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
