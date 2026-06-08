import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Space, Statistic, Row, Col, Select, Modal, Form, InputNumber, message, Spin } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import BaseChart from '../../components/Charts/BaseChart';
import { getOrders, getProducts, getSuppliers, createOrder, updateOrderStatus, getTrends } from '../../api';

export default function Orders() {
  const [orders, setOrders] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [trends, setTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [createVisible, setCreateVisible] = useState(false);
  const [products, setProducts] = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [form] = Form.useForm();

  const fetchOrders = () => {
    setLoading(true);
    getOrders({ status: statusFilter || undefined, limit: 100 }).then((data: any) => {
      setOrders(data.items || []);
      setTotal(data.total || 0);
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchOrders();
    getTrends().then((t: any) => setTrends(t.trends || []));
  }, [statusFilter]);

  const showCreate = async () => {
    const [p, s] = await Promise.all([getProducts(), getSuppliers()]);
    setProducts((p as any).items || []);
    setSuppliers((s as any).items || []);
    setCreateVisible(true);
  };

  const handleCreate = async (values: any) => {
    const prod = products.find((p) => p.id === values.product_id);
    await createOrder({ ...values, amount: prod ? values.quantity * prod.unit_price : 0 });
    message.success('订单已创建');
    setCreateVisible(false);
    form.resetFields();
    fetchOrders();
  };

  const handleStatusChange = async (id: number, status: string) => {
    await updateOrderStatus(id, status);
    message.success('状态已更新');
    fetchOrders();
  };

  const statusColor = (s: string) => {
    const map: Record<string, string> = { pending: 'default', confirmed: 'blue', shipping: 'orange', delivered: 'green', cancelled: 'red' };
    return map[s] || 'default';
  };
  const statusLabel = (s: string) => {
    const map: Record<string, string> = { pending: '待确认', confirmed: '已确认', shipping: '运输中', delivered: '已交付', cancelled: '已取消' };
    return map[s] || s;
  };

  const amountTrendOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 10, bottom: 40 },
    xAxis: { type: 'category', data: trends.map((t: any) => t.date?.slice(5)), axisLabel: { rotate: 45, fontSize: 10 } },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar', data: trends.map((t: any) => t.amount),
      itemStyle: { color: '#1890ff', borderRadius: [4, 4, 0, 0] },
    }],
  };

  const dailyOrdersOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 10, bottom: 40 },
    xAxis: { type: 'category', data: trends.map((t: any) => t.date?.slice(5)), axisLabel: { rotate: 45, fontSize: 10 } },
    yAxis: { type: 'value', name: '订单数' },
    series: [{
      type: 'line', data: trends.map((t: any) => t.orders),
      smooth: true, symbol: 'none', lineStyle: { color: '#52c41a' },
    }],
  };

  const totalAmount = orders.filter((o) => o.status !== 'cancelled').reduce((s: number, o: any) => s + (o.amount || 0), 0);

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={6}><Card><Statistic title="总订单数" value={total} /></Card></Col>
        <Col xs={6}><Card><Statistic title="总金额" value={(totalAmount / 10000).toFixed(1)} suffix="万元" /></Card></Col>
        <Col xs={6}><Card><Statistic title="已交付" value={orders.filter((o) => o.status === 'delivered').length} suffix="单" /></Card></Col>
        <Col xs={6}><Card><Statistic title="运输中" value={orders.filter((o) => o.status === 'shipping').length} suffix="单" /></Card></Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}><Card title="每日订单金额"><BaseChart option={amountTrendOption} height={300} /></Card></Col>
        <Col span={12}><Card title="每日订单量"><BaseChart option={dailyOrdersOption} height={300} /></Card></Col>
      </Row>
      <Card title="订单列表" style={{ marginTop: 16 }}>
        <Space style={{ marginBottom: 16 }}>
          <Select placeholder="状态筛选" allowClear style={{ width: 140 }} onChange={(v) => setStatusFilter(v || '')}
            options={['pending','confirmed','shipping','delivered','cancelled'].map((s) => ({ value: s, label: statusLabel(s) }))} />
          <Button type="primary" icon={<PlusOutlined />} onClick={showCreate}>新建订单</Button>
        </Space>
        <Table
          dataSource={orders}
          rowKey="id"
          loading={loading}
          columns={[
            { title: '订单号', dataIndex: 'order_no', key: 'no', width: 160 },
            { title: '产品', dataIndex: 'product_name', key: 'product', width: 130 },
            { title: '供应商', dataIndex: 'supplier_name', key: 'supplier', width: 130 },
            { title: '数量', dataIndex: 'quantity', key: 'qty' },
            { title: '金额(元)', dataIndex: 'amount', key: 'amount', render: (v: number) => v?.toLocaleString() },
            { title: '下单日期', dataIndex: 'order_date', key: 'date', width: 100 },
            { title: '预计交付', dataIndex: 'expected_delivery', key: 'expected', width: 100 },
            {
              title: '状态', dataIndex: 'status', key: 'status',
              render: (v: string, record: any) => (
                <Select value={v} size="small" style={{ width: 100 }}
                  onChange={(newStatus) => handleStatusChange(record.id, newStatus)}
                  options={['pending','confirmed','shipping','delivered','cancelled'].map((s) => ({
                    value: s, label: <Tag color={statusColor(s)}>{statusLabel(s)}</Tag>,
                  }))}
                />
              ),
            },
          ]}
          scroll={{ x: 1000 }}
        />
      </Card>

      <Modal title="新建采购订单" open={createVisible} onCancel={() => setCreateVisible(false)} onOk={() => form.submit()} width={500}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="product_id" label="产品" rules={[{ required: true }]}>
            <Select options={products.map((p) => ({ value: p.id, label: `${p.name} (¥${p.unit_price})` }))} />
          </Form.Item>
          <Form.Item name="supplier_id" label="供应商" rules={[{ required: true }]}>
            <Select options={suppliers.filter((s) => s.status === 'active').map((s) => ({ value: s.id, label: s.name }))} />
          </Form.Item>
          <Form.Item name="quantity" label="数量" rules={[{ required: true }]}>
            <InputNumber min={1} max={100000} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="status" label="状态" initialValue="pending">
            <Select options={['pending','confirmed'].map((s) => ({ value: s, label: statusLabel(s) }))} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
