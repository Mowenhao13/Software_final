import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Statistic, Row, Col, Space, message, Modal, Descriptions } from 'antd';
import { AlertOutlined, ScanOutlined } from '@ant-design/icons';
import BaseChart from '../../components/Charts/BaseChart';
import { getRisks, getRiskSummary, getAnomalies, detectRisks, updateAlertStatus } from '../../api';

export default function RiskMonitor() {
  const [risks, setRisks] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [anomalies, setAnomalies] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedRisk, setSelectedRisk] = useState<any>(null);

  const fetchData = () => {
    setLoading(true);
    Promise.all([getRisks({ limit: 50 }), getRiskSummary(), getAnomalies()]).then(([r, s, a]) => {
      setRisks((r as any).items || []);
      setSummary(s);
      setAnomalies(a);
    }).finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const handleDetect = async () => {
    const result: any = await detectRisks();
    message.success(result?.message || '检测完成');
    fetchData();
  };

  const handleResolve = async (id: number) => {
    await updateAlertStatus(id, 'resolved');
    message.success('预警已解决');
    fetchData();
  };

  const severityColor = (s: string) => s === 'high' ? 'red' : s === 'medium' ? 'orange' : 'blue';
  const severityLabel = (s: string) => s === 'high' ? '高' : s === 'medium' ? '中' : '低';
  const typeLabel = (t: string) => {
    const map: Record<string, string> = { inventory_shortage: '库存短缺', delivery_delay: '交付延迟',
      cost_spike: '成本异常', quality_issue: '质量问题', supplier_risk: '供应商风险' }; return map[t] || t;
  };

  const severityPieOption = {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie', radius: ['45%', '70%'],
      data: Object.entries(summary?.severity_distribution || {}).map(([k, v]: [string, any]) => ({
        name: severityLabel(k), value: v, itemStyle: { color: k === 'high' ? '#ff4d4f' : k === 'medium' ? '#faad14' : '#1890ff' },
      })),
      label: { formatter: '{b}: {c}' },
    }],
  };

  const typeBarOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 80, right: 20, top: 10, bottom: 20 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: Object.entries(summary?.type_distribution || {}).map(([k]: [string, any]) => typeLabel(k)).reverse() },
    series: [{
      type: 'bar', data: Object.entries(summary?.type_distribution || {}).map(([_, v]: [string, any]) => v).reverse(),
      itemStyle: { color: '#ff7875', borderRadius: [0, 4, 4, 0] },
    }],
  };

  // Anomalies combined
  const allAnomalies = [
    ...(anomalies?.order_anomalies || []).map((a: any) => ({ ...a, source: '订单' })),
    ...(anomalies?.inventory_anomalies || []).map((a: any) => ({ ...a, source: '库存' })),
    ...(anomalies?.cost_anomalies || []).map((a: any) => ({ ...a, source: '成本' })),
  ];

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={5}><Card><Statistic title="总预警" value={summary?.total || 0} prefix={<AlertOutlined />} /></Card></Col>
        <Col xs={5}><Card>
          <Statistic title="活跃预警" value={summary?.active || 0} valueStyle={{ color: summary?.active > 0 ? '#ff4d4f' : undefined }} />
        </Card></Col>
        <Col xs={5}><Card><Statistic title="高风险" value={summary?.high_risk || 0} valueStyle={{ color: summary?.high_risk > 0 ? '#ff4d4f' : undefined }} /></Card></Col>
        <Col xs={5}><Card><Statistic title="异常总数" value={anomalies?.total || 0} /></Card></Col>
        <Col xs={4}><Card style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          <Button type="primary" icon={<ScanOutlined />} onClick={handleDetect} block>
            执行风险检测
          </Button>
        </Card></Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={10}>
          <Card title="预警严重度分布"><BaseChart option={severityPieOption} height={300} /></Card>
        </Col>
        <Col span={14}>
          <Card title="预警类型分布"><BaseChart option={typeBarOption} height={300} /></Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={14}>
          <Card title="预警列表">
            <Table
              dataSource={risks}
              rowKey="id"
              loading={loading}
              size="small"
              columns={[
                {
                  title: '严重度', dataIndex: 'severity', key: 'severity', width: 70,
                  render: (v: string) => <Tag color={severityColor(v)}>{severityLabel(v)}</Tag>,
                },
                { title: '类型', dataIndex: 'alert_type', key: 'type', width: 90, render: (v: string) => typeLabel(v) },
                { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
                { title: '风险评分', dataIndex: 'risk_score', key: 'score', width: 80,
                  render: (v: number) => <span style={{ fontWeight: 700, color: v > 0.8 ? '#ff4d4f' : v > 0.6 ? '#faad14' : '#1890ff' }}>{(v * 100).toFixed(0)}%</span> },
                {
                  title: '状态', dataIndex: 'status', key: 'status', width: 80,
                  render: (v: string) => <Tag color={v === 'active' ? 'red' : v === 'acknowledged' ? 'orange' : 'green'}>{v === 'active' ? '活跃' : v === 'acknowledged' ? '已确认' : '已解决'}</Tag>,
                },
                {
                  title: '操作', key: 'actions', width: 140,
                  render: (_: any, record: any) => (
                    <Space size="small">
                      <Button type="link" size="small" onClick={() => { setSelectedRisk(record); setDetailVisible(true); }}>详情</Button>
                      {record.status !== 'resolved' && (
                        <Button type="link" size="small" onClick={() => handleResolve(record.id)}>解决</Button>
                      )}
                    </Space>
                  ),
                },
              ]}
            />
          </Card>
        </Col>
        <Col span={10}>
          <Card title="异常检测结果" style={{ maxHeight: 500, overflow: 'auto' }}>
            {allAnomalies.length === 0 && <div style={{ color: '#999', textAlign: 'center', padding: 40 }}>暂无异常</div>}
            {allAnomalies.map((a: any, i: number) => (
              <Card key={i} size="small" style={{ marginBottom: 8 }} type="inner">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <Tag color={a.severity === 'high' ? 'red' : a.severity === 'medium' ? 'orange' : 'blue'}>{a.severity === 'high' ? '高' : a.severity === 'medium' ? '中' : '低'}</Tag>
                    <Tag>{a.source}</Tag>
                    <span style={{ fontWeight: 500 }}>{a.type || a.entity}</span>
                  </div>
                </div>
                <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>{a.detail}</div>
                {a.date && <div style={{ fontSize: 11, color: '#999', marginTop: 2 }}>日期: {a.date}</div>}
              </Card>
            ))}
          </Card>
        </Col>
      </Row>

      <Modal title="预警详情" open={detailVisible} onCancel={() => setDetailVisible(false)} footer={null} width={600}>
        {selectedRisk && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="标题" span={2}>{selectedRisk.title}</Descriptions.Item>
            <Descriptions.Item label="严重度"><Tag color={severityColor(selectedRisk.severity)}>{severityLabel(selectedRisk.severity)}</Tag></Descriptions.Item>
            <Descriptions.Item label="类型">{typeLabel(selectedRisk.alert_type)}</Descriptions.Item>
            <Descriptions.Item label="风险评分">{(selectedRisk.risk_score * 100).toFixed(0)}%</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color={selectedRisk.status === 'active' ? 'red' : 'green'}>{selectedRisk.status}</Tag></Descriptions.Item>
            <Descriptions.Item label="描述" span={2}>{selectedRisk.description}</Descriptions.Item>
            <Descriptions.Item label="建议措施" span={2}><span style={{ color: '#1890ff' }}>{selectedRisk.suggested_action}</span></Descriptions.Item>
            <Descriptions.Item label="创建时间">{selectedRisk.created_at}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
}
