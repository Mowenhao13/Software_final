import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Table, Tag, Spin, Tabs } from 'antd';
import {
  ShoppingCartOutlined, DollarOutlined, CheckCircleOutlined,
  SyncOutlined, WarningOutlined, ArrowUpOutlined, ArrowDownOutlined, TeamOutlined,
  AppstoreOutlined, BoxPlotOutlined,
} from '@ant-design/icons';
import BaseChart from '../../components/Charts/BaseChart';
import {
  getKPIs, getTrends, getSupplierDist, getOrderStatus,
  getCategoryDistribution, getItemsSummary,
} from '../../api';

export default function Dashboard() {
  const [kpis, setKpis] = useState<any>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [supplierDist, setSupplierDist] = useState<any[]>([]);
  const [orderStatus, setOrderStatus] = useState<any[]>([]);
  const [catDist, setCatDist] = useState<any[]>([]);
  const [itemSummary, setItemSummary] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getKPIs(), getTrends(), getSupplierDist(), getOrderStatus(),
      getCategoryDistribution(), getItemsSummary(),
    ]).then(([k, t, s, o, c, ism]) => {
      setKpis(k);
      setTrends((t as any).trends || []);
      setSupplierDist(s as any[]);
      setOrderStatus(o as any[]);
      setCatDist(c as any[]);
      setItemSummary(ism as any[]);
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

  // 品类分布饼图
  const catColorMap: Record<string, string> = {
    electronics: '#1890ff', apparel: '#722ed1', automotive: '#fa8c16',
    food: '#52c41a', pharma: '#eb2f96',
  };
  const catPieOption = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['40%', '70%'], avoidLabelOverlap: false,
      label: { show: true, formatter: '{b}\n{c}' },
      emphasis: { label: { fontSize: 16, fontWeight: 'bold' } },
      data: catDist.map((c: any) => ({
        name: c.category,
        value: c.total_demand,
        itemStyle: { color: catColorMap[c.category] || '#999' },
      })),
    }],
  };

  // 品类数量分布柱状图
  const catBarOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 10, bottom: 30 },
    xAxis: { type: 'category', data: catDist.map((c: any) => c.category) },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar', data: catDist.map((c: any) => c.count),
      itemStyle: { color: (p: any) => catColorMap[catDist[p.dataIndex]?.category] || '#1890ff', borderRadius: [4, 4, 0, 0] },
    }],
  };

  // 物品周需求对比柱状图 (Top 10)
  const topItems = [...itemSummary].sort((a, b) => b.avg_weekly - a.avg_weekly).slice(0, 10);
  const itemBarOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 10, bottom: 60 },
    xAxis: { type: 'category', data: topItems.map((i: any) => i.name && i.name !== i.item_id ? i.name : i.item_id), axisLabel: { rotate: 45, fontSize: 10 } },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar', data: topItems.map((i: any) => i.avg_weekly),
      itemStyle: { color: (p: any) => catColorMap[topItems[p.dataIndex]?.category] || '#1890ff', borderRadius: [4, 4, 0, 0] },
    }],
  };

  const itemColumns = [
    { title: '物品ID', dataIndex: 'item_id', key: 'id', width: 80 },
    { title: '商品名称', dataIndex: 'name', key: 'name', width: 120,
      render: (v: string, r: any) => v && v !== r.item_id ? v : '-' },
    { title: '品类', dataIndex: 'category', key: 'cat', width: 100,
      render: (v: string) => <Tag color={catColorMap[v] || '#999'}>{v}</Tag> },
    { title: '总需求量', dataIndex: 'total_demand', key: 'total', width: 120, sorter: (a: any, b: any) => a.total_demand - b.total_demand },
    { title: '周均需求', dataIndex: 'avg_weekly', key: 'avg', width: 100, sorter: (a: any, b: any) => a.avg_weekly - b.avg_weekly,
      render: (v: number) => v.toFixed(1) },
    { title: '周标准差', dataIndex: 'std_weekly', key: 'std', width: 100, sorter: (a: any, b: any) => a.std_weekly - b.std_weekly,
      render: (v: number) => v.toFixed(1) },
    { title: '最近一周', dataIndex: 'latest_week', key: 'latest', width: 100,
      render: (v: number) => v.toFixed(1) },
  ];

  return (
    <div>
      {/* KPI 卡片 — 更多指标 */}
      <Row gutter={[16, 16]}>
        {[
          { title: '总订单量', value: kpis?.total_orders, icon: <ShoppingCartOutlined />, suffix: '单', color: '#1890ff' },
          { title: '总交易额', value: kpis?.total_amount?.toFixed(1), icon: <DollarOutlined />, suffix: '万元', color: '#52c41a' },
          { title: '准时交付率', value: kpis?.on_time_delivery_rate, icon: <CheckCircleOutlined />, suffix: '%', color: '#13c2c2' },
          { title: '库存周转率', value: kpis?.inventory_turnover, icon: <SyncOutlined />, suffix: '次/年', color: '#722ed1' },
          { title: '活跃供应商', value: kpis?.active_suppliers, icon: <TeamOutlined />, suffix: '家', color: '#fa8c16' },
          { title: '活跃预警', value: kpis?.risk_count, icon: <WarningOutlined />, suffix: '条', color: (kpis?.risk_count || 0) > 5 ? '#ff4d4f' : '#faad14' },
          { title: '物品总数', value: kpis?.total_items, icon: <AppstoreOutlined />, suffix: '种', color: '#2f54eb' },
          { title: '周均需求', value: kpis?.avg_weekly_demand, icon: <BoxPlotOutlined />, suffix: '', color: '#08979c',
            precision: 0 },
        ].map((item, i) => (
          <Col xs={12} sm={8} md={3} key={i}>
            <Card hoverable>
              <Statistic
                title={item.title}
                value={item.value}
                suffix={item.suffix}
                prefix={React.cloneElement(item.icon as any, { style: { color: item.color, fontSize: 20 } })}
                valueStyle={{ fontSize: 20, fontWeight: 700 }}
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
                <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>预测置信度</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#1890ff' }}>
                  {(kpis?.prediction_confidence * 100).toFixed(0)}%</div>
                <div style={{ fontSize: 12, color: '#999', marginBottom: 4, marginTop: 12 }}>总成本</div>
                <div style={{ fontSize: 20, fontWeight: 700 }}>{kpis?.cost_total?.toFixed(1)}
                  <span style={{ fontSize: 12, color: '#999' }}> 万元</span></div>
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

      {/* 品类分布 + 物品周需求对比 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={8}>
          <Card title="品类需求分布" style={{ height: 380 }}>
            <BaseChart option={catPieOption} height={300} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card title="品类物品数量" style={{ height: 380 }}>
            <BaseChart option={catBarOption} height={300} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card title="Top 10 物品周均需求" style={{ height: 380 }}>
            <BaseChart option={itemBarOption} height={300} />
          </Card>
        </Col>
      </Row>

      {/* 供应商分布 + 订单状态 */}
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
          <Card title="品类分布概览" style={{ height: 380 }}>
            <div style={{ padding: '0 8px' }}>
              {(catDist || []).map((c: any) => (
                <div key={c.category} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                  <span><Tag color={catColorMap[c.category] || '#999'}>{c.category}</Tag></span>
                  <span><strong>{c.count}</strong> 种物品</span>
                  <span>{c.total_demand.toLocaleString()} 需求</span>
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      {/* 所有物品汇总表 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title={`全部物品需求汇总 (共 ${itemSummary.length} 种物品)`}>
            <Table
              dataSource={itemSummary}
              rowKey="item_id"
              columns={itemColumns}
              pagination={{ pageSize: 15, showSizeChanger: true, showTotal: (t) => `共 ${t} 项` }}
              size="small"
              scroll={{ x: 700 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}