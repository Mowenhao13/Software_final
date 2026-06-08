import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Statistic, Row, Col, Spin, Space, Select } from 'antd';
import BaseChart from '../../components/Charts/BaseChart';
import { getShipments, getShipmentStats, getLogisticsAnalysis } from '../../api';

export default function Logistics() {
  const [shipments, setShipments] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    Promise.all([getShipmentStats(), getLogisticsAnalysis()]).then(([s, a]) => {
      setStats(s);
      setAnalysis(a);
    });
  }, []);

  useEffect(() => {
    setLoading(true);
    getShipments({ status: statusFilter || undefined, limit: 100 }).then((data: any) => {
      setShipments(data.items || []);
    }).finally(() => setLoading(false));
  }, [statusFilter]);

  const modeLabel = (m: string) => {
    const map: Record<string, string> = { road: '公路', rail: '铁路', air: '空运', sea: '海运' }; return map[m] || m;
  };
  const statusLabel = (s: string) => {
    const map: Record<string, string> = { in_transit: '在途', delivered: '已交付', delayed: '延迟', pending: '待发运' };
    return map[s] || s;
  };

  const costCompareOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 10, bottom: 30 },
    xAxis: { type: 'category', data: Object.keys(analysis?.summary || {}).map(modeLabel) },
    yAxis: [{ type: 'value', name: '平均成本(元)' }, { type: 'value', name: '准时率(%)', max: 100 }],
    series: [
      { name: '平均成本', type: 'bar', data: Object.values(analysis?.summary || {}).map((s: any) => s.avg_cost),
        itemStyle: { color: '#1890ff', borderRadius: [4, 4, 0, 0] } },
      { name: '准时率', type: 'line', yAxisIndex: 1, data: Object.values(analysis?.summary || {}).map((s: any) => s.on_time_rate),
        symbol: 'circle', symbolSize: 8, lineStyle: { color: '#52c41a' }, itemStyle: { color: '#52c41a' } },
    ],
    legend: { bottom: 0 },
  };

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={6}><Card><Statistic title="总运单" value={stats?.total || 0} /></Card></Col>
        <Col xs={6}><Card><Statistic title="在途" value={stats?.in_transit || 0} valueStyle={{ color: '#1890ff' }} /></Card></Col>
        <Col xs={6}><Card><Statistic title="延迟" value={stats?.delayed || 0} valueStyle={{ color: stats?.delayed > 0 ? '#ff4d4f' : undefined }} /></Card></Col>
        <Col xs={6}><Card><Statistic title="准时率" value={stats?.on_time_rate || 95} suffix="%" /></Card></Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={14}>
          <Card title="运输方式成本与时效对比">
            <BaseChart option={costCompareOption} height={350} />
          </Card>
        </Col>
        <Col span={10}>
          <Card title="运输方式分布">
            <BaseChart option={{
              tooltip: { trigger: 'item' },
              series: [{
                type: 'pie', radius: '65%',
                data: Object.entries(analysis?.summary || {}).map(([mode, s]: [string, any]) => ({
                  name: modeLabel(mode), value: s.count,
                })),
                label: { formatter: '{b}\n{d}%' },
              }],
            }} height={350} />
          </Card>
        </Col>
      </Row>
      <Card title="运单列表" style={{ marginTop: 16 }}>
        <Space style={{ marginBottom: 16 }}>
          <Select placeholder="状态筛选" allowClear style={{ width: 140 }} onChange={(v) => setStatusFilter(v || '')}
            options={['in_transit','delivered','delayed','pending'].map((s) => ({ value: s, label: statusLabel(s) }))} />
        </Space>
        <Table
          dataSource={shipments}
          rowKey="id"
          loading={loading}
          columns={[
            { title: '运单号', dataIndex: 'tracking_no', key: 'no', width: 150 },
            { title: '始发地', dataIndex: 'origin', key: 'origin', width: 80 },
            { title: '目的地', dataIndex: 'destination', key: 'dest', width: 80 },
            { title: '承运商', dataIndex: 'carrier', key: 'carrier', width: 100 },
            {
              title: '运输方式', dataIndex: 'transport_mode', key: 'mode',
              render: (v: string) => <Tag color={v === 'air' ? 'red' : v === 'sea' ? 'blue' : v === 'rail' ? 'purple' : 'green'}>{modeLabel(v)}</Tag>,
            },
            { title: '成本(元)', dataIndex: 'cost', key: 'cost', render: (v: number) => v?.toLocaleString() },
            {
              title: '状态', dataIndex: 'status', key: 'status',
              render: (v: string) => <Tag color={v === 'delayed' ? 'red' : v === 'in_transit' ? 'blue' : 'green'}>{statusLabel(v)}</Tag>,
            },
            { title: '出发时间', dataIndex: 'departure_time', key: 'dept', width: 100,
              render: (v: string) => v ? new Date(v).toLocaleDateString('zh-CN') : '-' },
            { title: '预计到达', dataIndex: 'arrival_time', key: 'eta', width: 100,
              render: (v: string) => v ? new Date(v).toLocaleDateString('zh-CN') : '-' },
          ]}
          scroll={{ x: 1000 }}
        />
      </Card>
    </div>
  );
}
