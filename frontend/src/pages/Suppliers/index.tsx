import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Space, Modal, Descriptions, Spin, message, Input, Select } from 'antd';
import { PlusOutlined, EyeOutlined, DeleteOutlined } from '@ant-design/icons';
import BaseChart from '../../components/Charts/BaseChart';
import { getSuppliers, getSupplierRanking, getSupplierScore, deleteSupplier } from '../../api';

export default function Suppliers() {
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [ranking, setRanking] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState<any>(null);
  const [scoreDetail, setScoreDetail] = useState<any>(null);
  const [search, setSearch] = useState('');
  const [region, setRegion] = useState('');

  const fetchData = () => {
    setLoading(true);
    Promise.all([
      getSuppliers({ search, region, limit: 50 }),
      getSupplierRanking(),
    ]).then(([s, r]) => {
      setSuppliers((s as any).items || []);
      setTotal((s as any).total || 0);
      setRanking(r as any[]);
    }).finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [search, region]);

  const showDetail = async (supplier: any) => {
    setSelectedSupplier(supplier);
    try {
      const score = await getSupplierScore(supplier.id);
      setScoreDetail(score);
    } catch { setScoreDetail(null); }
    setDetailVisible(true);
  };

  const handleDelete = async (id: number) => {
    Modal.confirm({
      title: '确认删除', content: '删除后数据不可恢复，确定要继续吗？',
      onOk: async () => { await deleteSupplier(id); message.success('已删除'); fetchData(); },
    });
  };

  const radarOption = scoreDetail ? {
    radar: {
      indicator: Object.keys(scoreDetail.dimensions || {}).map((k) => ({ name: k, max: 100 })),
      shape: 'circle',
    },
    series: [{ type: 'radar', data: [{ value: Object.values(scoreDetail.dimensions || {}), name: '评分' }],
      areaStyle: { color: 'rgba(24,144,255,0.2)' }, lineStyle: { color: '#1890ff' }, itemStyle: { color: '#1890ff' } }],
  } : {};

  const barOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 80, right: 30, top: 10, bottom: 20 },
    xAxis: { type: 'value', max: 100 },
    yAxis: { type: 'category', data: (ranking || []).slice(0, 10).map((r: any) => r.name).reverse(),
      axisLabel: { fontSize: 11 } },
    series: [{
      type: 'bar', data: (ranking || []).slice(0, 10).map((r: any) => r.score).reverse(),
      itemStyle: { color: '#1890ff', borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: 'right', fontSize: 11 },
    }],
  };

  return (
    <div>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Input.Search placeholder="搜索供应商" onSearch={setSearch} style={{ width: 250 }} allowClear />
          <Select placeholder="地区筛选" allowClear style={{ width: 120 }} onChange={(v) => setRegion(v || '')}
            options={['华南','华东','华北','西南','华中','西北'].map((r) => ({ value: r, label: r }))} />
          <Button type="primary" icon={<PlusOutlined />}>新增供应商</Button>
        </Space>
        <Table
          dataSource={suppliers}
          rowKey="id"
          loading={loading}
          columns={[
            { title: '供应商名称', dataIndex: 'name', key: 'name', width: 180 },
            { title: '类别', dataIndex: 'category', key: 'category', render: (v: string) => <Tag>{v}</Tag> },
            { title: '地区', dataIndex: 'region', key: 'region', render: (v: string) => <Tag color="blue">{v}</Tag> },
            {
              title: '综合评分', dataIndex: 'score', key: 'score', sorter: (a: any, b: any) => a.score - b.score,
              render: (v: number) => <span style={{ fontWeight: 700, color: v >= 90 ? '#52c41a' : v >= 80 ? '#faad14' : '#ff4d4f' }}>{v}</span>,
            },
            { title: '准时交付率', dataIndex: 'delivery_rate', key: 'delivery_rate', render: (v: number) => `${(v * 100).toFixed(1)}%` },
            { title: '质量合格率', dataIndex: 'quality_rate', key: 'quality_rate', render: (v: number) => `${(v * 100).toFixed(1)}%` },
            { title: '响应时间', dataIndex: 'response_time', key: 'response_time', render: (v: number) => `${v}h` },
            {
              title: '状态', dataIndex: 'status', key: 'status',
              render: (v: string) => <Tag color={v === 'active' ? 'green' : 'red'}>{v === 'active' ? '活跃' : '暂停'}</Tag>,
            },
            {
              title: '操作', key: 'actions',
              render: (_: any, record: any) => (
                <Space>
                  <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => showDetail(record)}>详情</Button>
                  <Button type="link" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>删除</Button>
                </Space>
              ),
            },
          ]}
        />
      </Card>

      {/* 排名 + 评分雷达 */}
      <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <Card title="供应商绩效排名 TOP10">
          <BaseChart option={barOption} height={400} />
        </Card>
        <Card title={selectedSupplier ? `${selectedSupplier.name} — 多维度评分` : '供应商评分雷达图'}>
          {selectedSupplier ? (
            <BaseChart option={radarOption} height={400} />
          ) : (
            <div style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
              点击供应商“详情”查看评分雷达图
            </div>
          )}
        </Card>
      </div>

      <Modal title="供应商详情" open={detailVisible} onCancel={() => setDetailVisible(false)} footer={null} width={700}>
        {selectedSupplier && (
          <>
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="名称">{selectedSupplier.name}</Descriptions.Item>
              <Descriptions.Item label="类别">{selectedSupplier.category}</Descriptions.Item>
              <Descriptions.Item label="地区">{selectedSupplier.region}</Descriptions.Item>
              <Descriptions.Item label="联系人">{selectedSupplier.contact}</Descriptions.Item>
              <Descriptions.Item label="综合评分">
                <span style={{ fontWeight: 700, fontSize: 18, color: selectedSupplier.score >= 85 ? '#52c41a' : '#faad14' }}>
                  {selectedSupplier.score}
                </span>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={selectedSupplier.status === 'active' ? 'green' : 'red'}>{selectedSupplier.status}</Tag>
              </Descriptions.Item>
            </Descriptions>
            {scoreDetail && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontWeight: 600, marginBottom: 8 }}>多维度评分详情</div>
                <BaseChart option={radarOption} height={300} />
              </div>
            )}
          </>
        )}
      </Modal>
    </div>
  );
}
