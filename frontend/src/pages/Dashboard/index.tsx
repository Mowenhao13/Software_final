import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Table, Tag, Spin } from 'antd';
import {
  ShoppingCartOutlined, DollarOutlined, CheckCircleOutlined,
  SyncOutlined, WarningOutlined, ArrowUpOutlined, ArrowDownOutlined, TeamOutlined,
} from '@ant-design/icons';
import BaseChart from '../../components/Charts/BaseChart';
import { getKPIs, getTrends, getSupplierDist, getOrderStatus, getRisks } from '../../api';

export default function Dashboard() {
  const [kpis, setKpis] = useState<any>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [supplierDist, setSupplierDist] = useState<any[]>([]);
  const [orderStatus, setOrderStatus] = useState<any[]>([]);
  const [risks, setRisks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getKPIs(), getTrends(), getSupplierDist(), getOrderStatus(),
      getRisks({ limit: 5, status: 'active' }),
    ]).then(([k, t, s, o, r]) => {
      setKpis(k);
      setTrends((t as any).trends || []);
      setSupplierDist(s as any[]);
      setOrderStatus(o as any[]);
      setRisks((r as any).items || []);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ textAlign: 'center', padding: 120 }}><Spin size="large" /></div>;

  const trendOption = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['订单金额(元)', '成本(元)'], bottom: 0 },
    grid: { left: 60, right: 30, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: trends.map((t: any) => t.date?.slice(5)), axisLabel: { rotate: 45, fontSize: 10 } },
    yAxis: { type: 'value' },
    series: [
      { name: '订单金额(元)', type: 'line', data: trends.map((t: any) => t.amount),
        smooth: true, lineStyle: { color: '#1890ff' }, itemStyle: { color: '#1890ff' }, symbol: 'none' },
      { name: '成本(元)', type: 'line', data: trends.map((t: any) => t.cost),
        smooth: true, lineStyle: { color: '#ff4d4f' }, itemStyle: { color: '#ff4d4f' }, symbol: 'none' },
    ],
  };

  const supplierOption = {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['45%', '75%'], avoidLabelOverlap: false,
      label: { show: true, formatter: '{b}\n{d}%' },
      emphasis: { label: { fontSize: 16, fontWeight: 'bold' } },
      data: supplierDist.map((s: any) => ({ name: s.region, value: s.count })),
    }],
  };

  const orderBarOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 10, bottom: 30 },
    xAxis: { type: 'category', data: orderStatus.map((o: any) => o.status) },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar', data: orderStatus.map((o: any) => o.count),
      itemStyle: { color: '#1890ff', borderRadius: [4, 4, 0, 0] },
    }],
  };

  const severityColor = (s: string) => s === 'high' ? 'red' : s === 'medium' ? 'orange' : 'blue';

  return (
    <div>
      {/* KPI 卡片 */}
      <Row gutter={[16, 16]}>
        {[
          { title: '总订单量', value: kpis?.total_orders, icon: <ShoppingCartOutlined />, suffix: '单', color: '#1890ff' },
          { title: '总交易额', value: (kpis?.total_amount / 10000).toFixed(1), icon: <DollarOutlined />, suffix: '万元', color: '#52c41a' },
          { title: '准时交付率', value: kpis?.on_time_delivery_rate, icon: <CheckCircleOutlined />, suffix: '%', color: '#13c2c2' },
          { title: '库存周转率', value: kpis?.inventory_turnover, icon: <SyncOutlined />, suffix: '次/年', color: '#722ed1' },
          { title: '活跃供应商', value: kpis?.active_suppliers, icon: <TeamOutlined />, suffix: '家', color: '#fa8c16' },
          { title: '活跃预警', value: kpis?.risk_count, icon: <WarningOutlined />, suffix: '条', color: kpis?.risk_count > 5 ? '#ff4d4f' : '#faad14' },
        ].map((item, i) => (
          <Col xs={12} sm={8} md={4} key={i}>
            <Card hoverable>
              <Statistic
                title={item.title}
                value={item.value}
                suffix={item.suffix}
                prefix={React.cloneElement(item.icon as any, { style: { color: item.color, fontSize: 20 } })}
                valueStyle={{ fontSize: 24, fontWeight: 700 }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {/* 趋势 + 月度增长 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={5}>
          <Card style={{ height: 390 }}>
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{ fontSize: 14, color: '#999', marginBottom: 8 }}>月环比增长</div>
              <div style={{ fontSize: 48, fontWeight: 800, color: (kpis?.month_growth || 0) >= 0 ? '#52c41a' : '#ff4d4f' }}>
                {(kpis?.month_growth || 0) >= 0 ? '+' : ''}{kpis?.month_growth}%
              </div>
              <div style={{ marginTop: 8 }}>
                {(kpis?.month_growth || 0) >= 0
                  ? <ArrowUpOutlined style={{ color: '#52c41a', fontSize: 20 }} />
                  : <ArrowDownOutlined style={{ color: '#ff4d4f', fontSize: 20 }} />
                }
              </div>
              <div style={{ marginTop: 20, padding: 16, background: '#fafafa', borderRadius: 8, textAlign: 'left' }}>
                <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>订单量</div>
                <div style={{ fontSize: 20, fontWeight: 700 }}>{kpis?.total_orders} <span style={{ fontSize: 12, color: '#999' }}>单</span></div>
                <div style={{ fontSize: 12, color: '#999', marginBottom: 4, marginTop: 12 }}>总成本</div>
                <div style={{ fontSize: 20, fontWeight: 700 }}>{(kpis?.cost_total / 10000).toFixed(1)} <span style={{ fontSize: 12, color: '#999' }}>万元</span></div>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={19}>
          <Card title="近30天趋势" style={{ height: 390 }}>
            <BaseChart option={trendOption} height={300} />
          </Card>
        </Col>
      </Row>

      {/* 供应商分布 + 订单状态 + 最新预警 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={8}>
          <Card title="供应商地区分布" style={{ height: 380 }}>
            <BaseChart option={supplierOption} height={300} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card title="订单状态分布" style={{ height: 380 }}>
            <BaseChart option={orderBarOption} height={300} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card title="最新预警" style={{ height: 380 }}>
            <Table
              dataSource={risks}
              rowKey="id"
              size="small"
              pagination={false}
              showHeader={false}
              columns={[
                {
                  dataIndex: 'title', key: 'title', ellipsis: true,
                  render: (text: string, record: any) => (
                    <div>
                      <Tag color={severityColor(record.severity)} style={{ marginRight: 4 }}>
                        {record.severity === 'high' ? '高' : record.severity === 'medium' ? '中' : '低'}
                      </Tag>
                      {text}
                    </div>
                  ),
                },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
