import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Table, Tag, Spin, Tabs, Timeline, Badge } from 'antd';
import {
  WarningOutlined, ShoppingCartOutlined, LineChartOutlined,
  ApartmentOutlined, AlertOutlined, ArrowUpOutlined, ArrowDownOutlined,
} from '@ant-design/icons';
import BaseChart from '../../components/Charts/BaseChart';
import {
  getRiskOverview, getSupplyRisks, getDemandRisks,
  getLogisticsRisks, getRiskAlerts,
} from '../../api';

const levelColors: Record<string, string> = {
  high: 'red',
  medium: 'orange',
  low: 'blue',
};
const levelLabels: Record<string, string> = {
  high: '高风险',
  medium: '中风险',
  low: '低风险',
};

export default function RiskMonitor() {
  const [overview, setOverview] = useState<any>(null);
  const [supplyRisks, setSupplyRisks] = useState<any[]>([]);
  const [demandRisks, setDemandRisks] = useState<any[]>([]);
  const [logisticsRisks, setLogisticsRisks] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getRiskOverview(),
      getSupplyRisks(),
      getDemandRisks(),
      getLogisticsRisks(),
      getRiskAlerts(),
    ]).then(([ov, sr, dr, lr, al]) => {
      setOverview(ov);
      setSupplyRisks((sr as any).risks || []);
      setDemandRisks((dr as any).risks || []);
      setLogisticsRisks((lr as any).risks || []);
      setAlerts((al as any).alerts || []);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ textAlign: 'center', padding: 120 }}><Spin size="large" /></div>;

  // ── 等级分布饼图 ──
  const pieOption = {
    tooltip: { trigger: 'item', formatter: '{b}: {c}' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      label: { show: true, formatter: '{b}\n{d}%' },
      data: (overview?.level_distribution || []).map((item: any) => ({
        ...item,
        itemStyle: { color: item.name === '高风险' ? '#ff4d4f' : item.name === '中风险' ? '#faad14' : '#1890ff' },
      })),
    }],
  };

  // ── 风险明细表格列 ──
  const columns = [
    { title: '物品/节点', dataIndex: 'item_id', key: 'item_id', width: 120 },
    { title: '品类', dataIndex: 'category', key: 'category', width: 100 },
    {
      title: '风险等级', dataIndex: 'level', key: 'level', width: 100,
      render: (lvl: string) => <Tag color={levelColors[lvl]}>{levelLabels[lvl]}</Tag>,
    },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  ];

  const supplyColumns = [
    ...columns,
    { title: '变化率', dataIndex: 'change_pct', key: 'change_pct', width: 120,
      render: (v: number) => (
        <span style={{ color: v > 0 ? '#ff4d4f' : '#52c41a' }}>
          {v > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />} {Math.abs(v).toFixed(1)}%
        </span>
      ),
    },
  ];

  const demandColumns = [
    ...columns,
    { title: '波动率 CV', dataIndex: 'cv', key: 'cv', width: 100 },
    { title: '均值', dataIndex: 'mean', key: 'mean', width: 80 },
  ];

  const logisticsColumns = [
    { title: '起始', dataIndex: 'from', key: 'from', width: 130 },
    { title: '终点', dataIndex: 'to', key: 'to', width: 130 },
    { title: '运输方式', dataIndex: 'mode', key: 'mode', width: 90 },
    { title: '风险等级', dataIndex: 'level', key: 'level', width: 100,
      render: (lvl: string) => <Tag color={levelColors[lvl]}>{levelLabels[lvl]}</Tag>,
    },
    { title: '容量使用率', dataIndex: 'load_pct', key: 'load_pct', width: 110,
      render: (v: number) => `${v}%`,
    },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  ];

  return (
    <div>
      {/* ── KPI 卡片 ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card hoverable>
            <Statistic
              title="供给风险"
              value={overview?.supply?.total || 0}
              prefix={<ShoppingCartOutlined style={{ color: '#ff4d4f' }} />}
              suffix={
                <span style={{ fontSize: 13, color: '#999' }}>
                  / 高{overview?.supply?.high || 0} 中{overview?.supply?.medium || 0}
                </span>
              }
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card hoverable>
            <Statistic
              title="需求风险"
              value={overview?.demand?.total || 0}
              prefix={<LineChartOutlined style={{ color: '#faad14' }} />}
              suffix={
                <span style={{ fontSize: 13, color: '#999' }}>
                  / 高{overview?.demand?.high || 0} 中{overview?.demand?.medium || 0}
                </span>
              }
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card hoverable>
            <Statistic
              title="物流风险"
              value={overview?.logistics?.total || 0}
              prefix={<ApartmentOutlined style={{ color: '#1890ff' }} />}
              suffix={
                <span style={{ fontSize: 13, color: '#999' }}>
                  / 高{overview?.logistics?.high || 0} 中{overview?.logistics?.medium || 0}
                </span>
              }
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card hoverable>
            <Statistic
              title="高风险告警"
              value={overview?.total_high || 0}
              prefix={<WarningOutlined style={{ color: '#ff4d4f' }} />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* ── 图表 + 告警时间线 ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card title="风险等级分布" size="small">
            <BaseChart option={pieOption} height={280} />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="实时告警" size="small" bodyStyle={{ maxHeight: 320, overflow: 'auto' }}>
            <Timeline>
              {alerts.map((a, i) => (
                <Timeline.Item
                  key={i}
                  color={levelColors[a.level]}
                  dot={a.level === 'high' ? <Badge status="error" /> : <Badge status="warning" />}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>
                      <Tag color={levelColors[a.level]}>{a.type_label}</Tag>
                      <strong>{a.item_id}</strong> — {a.message}
                    </span>
                    <span style={{ color: '#999', fontSize: 12 }}>{a.timestamp}</span>
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </Col>
      </Row>

      {/* ── Tabs 切换风险明细 ── */}
      <Card title="风险明细" size="small">
        <Tabs defaultActiveKey="supply">
          <Tabs.TabPane tab={<span><WarningOutlined /> 供给风险</span>} key="supply">
            <Table
              dataSource={supplyRisks}
              columns={supplyColumns}
              rowKey="item_id"
              size="small"
              pagination={{ pageSize: 8, showSizeChanger: false }}
            />
          </Tabs.TabPane>
          <Tabs.TabPane tab={<span><LineChartOutlined /> 需求风险</span>} key="demand">
            <Table
              dataSource={demandRisks}
              columns={demandColumns}
              rowKey="item_id"
              size="small"
              pagination={{ pageSize: 8, showSizeChanger: false }}
            />
          </Tabs.TabPane>
          <Tabs.TabPane tab={<span><ApartmentOutlined /> 物流风险</span>} key="logistics">
            <Table
              dataSource={logisticsRisks}
              columns={logisticsColumns}
              rowKey={(r) => `${r.from}-${r.to}`}
              size="small"
              pagination={{ pageSize: 8, showSizeChanger: false }}
            />
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </div>
  );
}