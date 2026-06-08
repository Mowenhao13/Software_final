import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Statistic, Row, Col, Spin, Select, Switch, Space } from 'antd';
import { WarningOutlined, InboxOutlined } from '@ant-design/icons';
import BaseChart from '../../components/Charts/BaseChart';
import { getInventory, getInventorySummary, getWarehouses } from '../../api';

export default function InventoryPage() {
  const [inventory, setInventory] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [warehouses, setWarehouses] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [warehouse, setWarehouse] = useState('');
  const [lowStockOnly, setLowStockOnly] = useState(false);

  useEffect(() => {
    Promise.all([getInventorySummary(), getWarehouses()]).then(([s, w]) => {
      setSummary(s);
      setWarehouses((w as any[]).map((wh: any) => wh.warehouse));
    });
  }, []);

  useEffect(() => {
    setLoading(true);
    getInventory({ warehouse, low_stock_only: lowStockOnly }).then((data: any) => {
      setInventory(data.items || []);
    }).finally(() => setLoading(false));
  }, [warehouse, lowStockOnly]);

  const turnoverOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 30, top: 10, bottom: 60 },
    xAxis: { type: 'category', data: inventory.map((i: any) => i.product_name?.slice(0, 6)),
      axisLabel: { rotate: 45, fontSize: 10 } },
    yAxis: { type: 'value', name: '周转率' },
    series: [{
      type: 'bar', data: inventory.map((i: any) => i.turnover_rate),
      itemStyle: {
        color: (p: any) => p.value < 2 ? '#ff4d4f' : p.value > 6 ? '#52c41a' : '#1890ff',
        borderRadius: [4, 4, 0, 0],
      },
    }],
  };

  const statusPieOption = {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie', radius: ['50%', '75%'],
      data: [
        { name: '正常', value: inventory.filter((i: any) => i.status === 'normal').length, itemStyle: { color: '#52c41a' } },
        { name: '库存不足', value: inventory.filter((i: any) => i.status === 'low').length, itemStyle: { color: '#ff4d4f' } },
        { name: '库存过高', value: inventory.filter((i: any) => i.status === 'excess').length, itemStyle: { color: '#faad14' } },
      ],
      label: { formatter: '{b}: {c}' },
    }],
  };

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={6}><Card><Statistic title="SKU总数" value={summary?.total_skus || 0} prefix={<InboxOutlined />} /></Card></Col>
        <Col xs={6}><Card><Statistic title="库存不足" value={summary?.low_stock_count || 0} prefix={<WarningOutlined />} valueStyle={{ color: summary?.low_stock_count > 0 ? '#ff4d4f' : undefined }} /></Card></Col>
        <Col xs={6}><Card><Statistic title="库存总价值" value={(summary?.total_inventory_value / 10000).toFixed(1)} suffix="万元" /></Card></Col>
        <Col xs={6}><Card><Statistic title="平均周转率" value={summary?.avg_turnover_rate || 0} suffix="次/年" /></Card></Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={14}>
          <Card title="库存周转率对比">
            <BaseChart option={turnoverOption} height={350} />
          </Card>
        </Col>
        <Col span={10}>
          <Card title="库存状态分布">
            <BaseChart option={statusPieOption} height={350} />
          </Card>
        </Col>
      </Row>

      <Card title="库存明细" style={{ marginTop: 16 }}>
        <Space style={{ marginBottom: 16 }}>
          <Select placeholder="仓库筛选" allowClear style={{ width: 150 }} onChange={(v) => setWarehouse(v || '')}
            options={warehouses.map((w) => ({ value: w, label: w }))} />
          <Space><Switch checked={lowStockOnly} onChange={setLowStockOnly} /> 仅显示库存不足</Space>
        </Space>
        <Table
          dataSource={inventory}
          rowKey="id"
          loading={loading}
          columns={[
            { title: '产品名称', dataIndex: 'product_name', key: 'product_name', width: 150 },
            { title: '产品编码', dataIndex: 'product_code', key: 'code', width: 100 },
            { title: '类别', dataIndex: 'category', key: 'category', render: (v: string) => <Tag>{v}</Tag> },
            { title: '仓库', dataIndex: 'warehouse', key: 'warehouse', render: (v: string) => <Tag color="purple">{v}</Tag> },
            { title: '库存量', dataIndex: 'quantity', key: 'qty', sorter: (a: any, b: any) => a.quantity - b.quantity },
            { title: '安全库存', dataIndex: 'safety_stock', key: 'safety' },
            { title: '最大库存', dataIndex: 'max_stock', key: 'max' },
            { title: '周转率', dataIndex: 'turnover_rate', key: 'turnover',
              render: (v: number) => <span style={{ color: v < 2 ? '#ff4d4f' : v > 5 ? '#52c41a' : '#1890ff', fontWeight: 600 }}>{v}</span> },
            {
              title: '状态', dataIndex: 'status', key: 'status',
              render: (v: string) => (
                <Tag color={v === 'normal' ? 'green' : v === 'low' ? 'red' : 'orange'}>
                  {v === 'normal' ? '正常' : v === 'low' ? '不足' : '过高'}
                </Tag>
              ),
            },
            { title: '最近补货', dataIndex: 'last_restock', key: 'restock' },
          ]}
          scroll={{ x: 1000 }}
        />
      </Card>
    </div>
  );
}
