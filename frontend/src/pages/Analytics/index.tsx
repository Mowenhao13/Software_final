import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Spin } from 'antd';
import BaseChart from '../../components/Charts/BaseChart';
import { getCostAnalysis, getSupplierPerformance, getLogisticsAnalysis } from '../../api';

export default function Analytics() {
  const [costData, setCostData] = useState<any>(null);
  const [supplierPerf, setSupplierPerf] = useState<any[]>([]);
  const [logisticsData, setLogisticsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getCostAnalysis(), getSupplierPerformance(), getLogisticsAnalysis()])
      .then(([c, s, l]) => {
        setCostData(c);
        setSupplierPerf(s as any[]);
        setLogisticsData(l);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ textAlign: 'center', padding: 120 }}><Spin size="large" /></div>;

  const catColorMap: Record<string, string> = { procurement: '#1890ff', logistics: '#52c41a', inventory: '#faad14', quality: '#722ed1', other: '#bfbfbf' };
  const catLabelMap: Record<string, string> = { procurement: '采购成本', logistics: '物流成本', inventory: '库存成本', quality: '质量成本', other: '其他' };
  const categoryLabel = (cat: string) => catLabelMap[cat] || cat;

  // 成本构成饼图
  const costPieOption = {
    tooltip: { trigger: 'item', formatter: '{b}: ¥{c} ({d}%)' },
    series: [{
      type: 'pie', radius: ['45%', '75%'],
      data: (costData?.by_category || []).map((c: any) => ({
        name: categoryLabel(c.category), value: c.amount,
        itemStyle: { color: catColorMap[c.category] || '#1890ff' },
      })),
      label: { formatter: '{b}\n{d}%' },
    }],
  };

  // 月度成本趋势
  const costTrendOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 10, bottom: 40 },
    xAxis: { type: 'category', data: (costData?.by_month || []).map((m: any) => m.month),
      axisLabel: { rotate: 45, fontSize: 10 } },
    yAxis: { type: 'value', name: '成本(元)' },
    series: [{
      type: 'line', data: (costData?.by_month || []).map((m: any) => m.amount),
      smooth: true, areaStyle: { color: 'rgba(24,144,255,0.15)' },
      lineStyle: { color: '#1890ff' }, itemStyle: { color: '#1890ff' }, symbol: 'circle', symbolSize: 6,
    }],
  };

  // 部门成本
  const deptBarOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 100, right: 30, top: 10, bottom: 20 },
    xAxis: { type: 'value', name: '成本(元)' },
    yAxis: { type: 'category', data: (costData?.by_department || []).map((d: any) => d.department).reverse() },
    series: [{
      type: 'bar', data: (costData?.by_department || []).map((d: any) => d.amount).reverse(),
      itemStyle: { borderRadius: [0, 4, 4, 0], color: '#52c41a' },
      label: { show: true, position: 'right', formatter: (p: any) => `¥${(p.value / 10000).toFixed(1)}万` },
    }],
  };

  // 供应商绩效散点图
  const supplierScatterOption = {
    tooltip: { trigger: 'item', formatter: (p: any) => `${p.name}<br/>评分: ${p.value[0]}<br/>准时率: ${p.value[1]}%` },
    grid: { left: 60, right: 20, top: 10, bottom: 30 },
    xAxis: { type: 'value', name: '综合评分', min: 70, max: 100 },
    yAxis: { type: 'value', name: '准时交付率(%)', min: 80, max: 100 },
    series: [{
      type: 'scatter', symbolSize: (val: number[]) => val[0] * 0.3,
      data: (supplierPerf || []).map((s: any) => ({
        name: s.name, value: [s.score, s.delivery_rate],
        itemStyle: { color: s.score >= 90 ? '#52c41a' : s.score >= 80 ? '#faad14' : '#ff4d4f' },
      })),
      label: { show: true, formatter: (p: any) => p.name, fontSize: 10, position: 'top' },
    } as any],
  };

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={6}><Card><Statistic title="总成本" value={(costData?.total_cost / 10000).toFixed(1)} suffix="万元" /></Card></Col>
        <Col xs={6}><Card><Statistic title="成本类别数" value={costData?.by_category?.length || 0} /></Card></Col>
        <Col xs={6}><Card><Statistic title="供应商总数" value={supplierPerf?.length || 0} suffix="家" /></Card></Col>
        <Col xs={6}><Card><Statistic title="物流路线数" value={logisticsData?.routes?.length || 0} /></Card></Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={10}>
          <Card title="成本构成分析">
            <BaseChart option={costPieOption} height={350} />
          </Card>
        </Col>
        <Col span={14}>
          <Card title="月度成本趋势">
            <BaseChart option={costTrendOption} height={350} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="部门成本对比">
            <BaseChart option={deptBarOption} height={350} />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="供应商绩效散点图">
            <BaseChart option={supplierScatterOption} height={350} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="成本类别明细">
            <Table
              dataSource={costData?.by_category || []}
              rowKey="category"
              size="small"
              pagination={false}
              columns={[
                { title: '类别', dataIndex: 'category', render: (v: string) => <Tag>{categoryLabel(v)}</Tag> },
                { title: '金额(元)', dataIndex: 'amount', render: (v: number) => v?.toLocaleString(), sorter: (a: any, b: any) => a.amount - b.amount },
                { title: '占比', dataIndex: 'percentage', render: (v: number) => `${v}%` },
              ]}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="供应商绩效排名" style={{ maxHeight: 400, overflow: 'auto' }}>
            <Table
              dataSource={(supplierPerf || []).slice(0, 10)}
              rowKey="id"
              size="small"
              pagination={false}
              columns={[
                { title: '排名', dataIndex: 'rank', width: 50 },
                { title: '名称', dataIndex: 'name', width: 120 },
                {
                  title: '综合评分', dataIndex: 'score', width: 80,
                  render: (v: number) => <span style={{ fontWeight: 700, color: v >= 90 ? '#52c41a' : v >= 80 ? '#faad14' : '#ff4d4f' }}>{v}</span>,
                },
                { title: '准时率', dataIndex: 'delivery_rate', render: (v: number) => `${v}%` },
                { title: '订单数', dataIndex: 'total_orders' },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
