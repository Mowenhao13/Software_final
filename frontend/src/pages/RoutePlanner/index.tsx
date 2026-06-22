import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Select, Spin, Tag, Table, Switch, Empty, Alert, Statistic, Radio, Space } from 'antd';
import BaseChart from '../../components/Charts/BaseChart';
import { getOptimizationGraph, findRoute, findRouteWithForecast, getForecastItems, getItemCatalog } from '../../api';

const catColorMap: Record<string, string> = {
  electronics: '#1890ff', apparel: '#722ed1', automotive: '#fa8c16',
  food: '#52c41a', pharma: '#eb2f96',
};

export default function RoutePlanner() {
  const [graph, setGraph] = useState<any>(null);
  const [items, setItems] = useState<any[]>([]);
  const [catalog, setCatalog] = useState<Record<string, string[]>>({});
  const [startNode, setStartNode] = useState<string>('');
  const [endNode, setEndNode] = useState<string>('');
  const [selectedItem, setSelectedItem] = useState<string>('');
  const [useForecast, setUseForecast] = useState(false);
  const [transportMode, setTransportMode] = useState<string>('');
  const [routes, setRoutes] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  // 物品品类信息
  const [categoryMap, setCategoryMap] = useState<Record<string, string>>({});

  useEffect(() => {
    Promise.all([
      getOptimizationGraph(),
      getForecastItems(),
      getItemCatalog(),
    ]).then(([g, i, cat]) => {
      setGraph(g);
      setItems(i as any[]);
      setCatalog(cat as Record<string, string[]>);
      // 构建物品->品类反向映射
      const cmap: Record<string, string> = {};
      if (cat && typeof cat === 'object') {
        Object.entries(cat).forEach(([c, ids]) => {
          (ids as string[]).forEach((id) => { cmap[id] = c; });
        });
      }
      setCategoryMap(cmap);
    });
  }, []);

  const searchRoutes = () => {
    if (!startNode || !endNode) return;
    setLoading(true);

    const commonParams = { start: startNode, end: endNode, top_k: 5 };
    const modeParams = transportMode ? { mode: transportMode } : {};

    const promise = useForecast && selectedItem
      ? findRouteWithForecast({ ...commonParams, ...modeParams, item_id: selectedItem })
      : findRoute({ ...commonParams, ...modeParams, demand_volume: 100 });

    promise.then(setRoutes).finally(() => setLoading(false));
  };

  useEffect(() => { searchRoutes(); }, [startNode, endNode, selectedItem, useForecast, transportMode]);

  // 节点选项，区分类型
  const factoryNodes = (graph?.nodes || []).filter((n: any) => n.type === 'factory');
  const destNodes = (graph?.nodes || []).filter((n: any) => n.type === 'destination');
  const warehouseNodes = (graph?.nodes || []).filter((n: any) => n.type === 'warehouse');

  const factoryOptions = factoryNodes.map((n: any) => ({
    value: n.id,
    label: `🏭 ${n.name || n.id} (${n.region || ''})`,
  }));
  const destOptions = destNodes.map((n: any) => ({
    value: n.id,
    label: `📍 ${n.name || n.id} (${n.region || ''})`,
  }));
  const warehouseOptions = warehouseNodes.map((n: any) => ({
    value: n.id,
    label: `📦 ${n.name || n.id} (${n.region || ''})`,
  }));

  // 物品下拉选项，含品类标签
  const itemOptions = items.map((i: any) => {
    const cat = categoryMap[i.item_id] || '';
    return {
      value: i.item_id,
      label: `${i.item_id} ${cat ? `(${cat})` : ''}`,
    };
  });

  // 选中物品的品类
  const selectedItemCategory = selectedItem ? categoryMap[selectedItem] : '';

  // 运输方式选项
  const modeOptions = [
    { value: '', label: '全部方式' },
    { value: 'road', label: '🚛 公路运输' },
    { value: 'rail', label: '🚂 铁路运输' },
    { value: 'air', label: '✈️ 航空运输' },
  ];

  // 图拓扑可视化
  const allNodes = graph?.nodes || [];
  const graphOption = routes?.paths?.length > 0 ? {
    tooltip: { trigger: 'item' as const, formatter: (p: any) => p.name },
    series: [{
      type: 'graph',
      layout: 'force' as const,
      roam: true,
      draggable: true,
      data: (routes.nodes || allNodes).map((n: any) => ({
        id: n.id,
        name: n.name || n.id,
        category: n.type === 'factory' ? 0 : n.type === 'destination' ? 2 : 1,
        symbolSize: n.type === 'factory' ? 40 : n.type === 'destination' ? 50 : 30,
        itemStyle: {
          color: n.type === 'factory' ? '#fa8c16' : n.type === 'destination' ? '#52c41a' : '#1890ff',
        },
      })),
      edges: (routes?.paths?.[0]?.path || []).slice(0, -1).map((fromId: string, i: number) => {
        const toId = routes.paths[0].path[i + 1];
        const seg = routes.paths[0].segments?.[i];
        return {
          source: fromId,
          target: toId,
          lineStyle: {
            color: seg?.mode === 'rail' ? '#fa8c16' : seg?.mode === 'air' ? '#f5222d' : '#1890ff',
            width: seg?.mode === 'rail' ? 3 : 2,
            curveness: seg?.mode === 'rail' ? 0.3 : 0.15,
            type: seg?.mode === 'rail' ? 'dotted' : 'solid' as const,
          },
          label: { show: true, formatter: seg?.mode || 'road', fontSize: 9, color: '#666' },
        };
      }),
      categories: [
        { name: '工厂', itemStyle: { color: '#fa8c16' } },
        { name: '仓储', itemStyle: { color: '#1890ff' } },
        { name: '目的地', itemStyle: { color: '#52c41a' } },
      ],
      force: { repulsion: 500, edgeLength: 200 },
      label: { show: true, position: 'right', fontSize: 10 },
      lineStyle: { color: '#1890ff', width: 2, curveness: 0.2 },
    }],
  } : null;

  const columns = [
    { title: '排名', key: 'rank', width: 60, render: (_: any, __: any, i: number) => i + 1 },
    { title: '路径', dataIndex: 'path', key: 'path', render: (p: string[]) => p.join(' → ') },
    { title: '天数', dataIndex: 'total_time_days', key: 'time', width: 80, sorter: (a: any, b: any) => a.total_time_days - b.total_time_days },
    { title: '成本', dataIndex: 'total_cost', key: 'cost', width: 100, sorter: (a: any, b: any) => a.total_cost - b.total_cost, render: (v: number) => v.toLocaleString() },
    { title: '需求适配度', dataIndex: 'demand_fitness', key: 'fitness', width: 110,
      render: (v: number) => <Tag color={v > 80 ? 'green' : v > 50 ? 'orange' : 'red'}>{v}%</Tag> },
    { title: '综合得分', dataIndex: 'score', key: 'score', width: 100, sorter: (a: any, b: any) => a.score - b.score },
  ];

  const bestPath = routes?.paths?.[0];
  const modeFilter = routes?.mode_filter;

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="路径规划参数">
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center' }}>
              <Select
                placeholder="起点 (工厂)"
                style={{ width: 220 }}
                value={startNode || undefined}
                onChange={(v) => { setStartNode(v); }}
                options={factoryOptions}
              />
              <Select
                placeholder="终点 (目的地)"
                style={{ width: 220 }}
                value={endNode || undefined}
                onChange={(v) => { setEndNode(v); }}
                options={destOptions}
              />
              <Select
                placeholder="运输方式"
                style={{ width: 160 }}
                value={transportMode}
                onChange={setTransportMode}
                options={modeOptions}
              />
              <Select
                placeholder="关联物品 (可选)"
                style={{ width: 200 }}
                value={selectedItem || undefined}
                onChange={setSelectedItem}
                allowClear
                showSearch
                filterOption={(input: string, option: any) =>
                  (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
                }
                options={itemOptions}
              />
              <Space>
                <span style={{ lineHeight: '32px' }}>需求联动</span>
                <Switch checked={useForecast} onChange={setUseForecast} />
              </Space>
            </div>
            {/* 物品品类信息 */}
            {selectedItemCategory && (
              <div style={{ marginTop: 12, padding: '8px 12px', background: '#f6f8fa', borderRadius: 6 }}>
                <Space size="large">
                  <span>物品 <strong>{selectedItem}</strong></span>
                  <span>品类: <Tag color={catColorMap[selectedItemCategory]}>{selectedItemCategory}</Tag></span>
                  <span>该品类共 <strong>{(catalog[selectedItemCategory] || []).length}</strong> 种物品</span>
                </Space>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 可选的中间节点 (仓储) 展示 */}
      <Row gutter={[16, 16]} style={{ marginTop: 8 }}>
        <Col span={24}>
          <Card size="small" title="可选中转仓储节点" style={{ fontSize: 12 }}>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {warehouseNodes.map((n: any) => (
                <Tag key={n.id} color="blue" style={{ cursor: 'pointer', padding: '2px 8px' }}
                  onClick={() => {
                    // 如果start和end都已选，点击仓储节点可查看所有经过该节点的路径
                  }}>
                  {n.name || n.id}
                </Tag>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      {loading && <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>}

      {routes?.forecast && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={24}>
            <Alert
              type={routes.forecast.growth_rate > 0.3 ? 'warning' : 'info'}
              message={
                `需求联动: 物品 ${routes.forecast.item_id} 预测趋势 ${routes.forecast.trend} ` +
                `(增长率 ${(routes.forecast.growth_rate * 100).toFixed(1)}%), 置信度 ${(routes.forecast.confidence * 100).toFixed(0)}%, ` +
                `路径权重已调整 (权重=${routes.forecast.forecast_weight.toFixed(1)})`
              }
              showIcon
            />
          </Col>
        </Row>
      )}

      {modeFilter && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={24}>
            <Alert
              type={routes?.mode_relaxed ? 'warning' : 'info'}
              message={
                routes?.mode_relaxed
                  ? `已放宽过滤: 未找到纯 ${modeFilter} 路径，已恢复到混合运输模式。您选择的运输方式将作为偏好参考。`
                  : `当前过滤: 运输方式 = ${modeFilter}`
              }
              showIcon
            />
          </Col>
        </Row>
      )}

      {bestPath && !loading && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={6}><Card><Statistic title="推荐路径天数" value={bestPath.total_time_days} suffix="天" /></Card></Col>
          <Col span={6}><Card><Statistic title="推荐路径成本" value={bestPath.total_cost} suffix="元" /></Card></Col>
          <Col span={6}><Card><Statistic title="需求适配度" value={bestPath.demand_fitness} suffix="%" valueStyle={{ color: bestPath.demand_fitness > 80 ? '#52c41a' : '#faad14' }} /></Card></Col>
          <Col span={6}><Card><Statistic title="推荐路径" value={bestPath.path.length} suffix="节点" /></Card></Col>
        </Row>
      )}

      {bestPath?.segments && !loading && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={24}>
            <Card title="路径分段详情" size="small">
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {bestPath.segments.map((seg: any, i: number) => (
                  <Tag key={i} color={seg.mode === 'rail' ? 'orange' : seg.mode === 'air' ? 'red' : 'blue'}
                    style={{ padding: '4px 12px', fontSize: 13 }}>
                    {seg.from} → {seg.to}
                    <span style={{ marginLeft: 6, fontWeight: 600 }}>[{seg.mode}]</span>
                    <span style={{ marginLeft: 6 }}>{seg.days}天</span>
                  </Tag>
                ))}
              </div>
            </Card>
          </Col>
        </Row>
      )}

      {routes?.paths?.length > 0 && !loading && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={14}>
            <Card title="供应链网络拓扑 (最优路径高亮)">
              <div style={{ width: '100%', height: 450 }}>
                <BaseChart option={graphOption} height={450} />
              </div>
            </Card>
          </Col>
          <Col span={10}>
            <Card title="Top-K 路径对比">
              <Table dataSource={routes.paths} rowKey="score" columns={columns}
                pagination={false} size="small" />
            </Card>
          </Col>
        </Row>
      )}

      {!startNode && !endNode && !loading && (
        <Card style={{ marginTop: 16 }}>
          <Empty description="请选择起点 (工厂) 和终点 (目的地) 进行路径规划" />
        </Card>
      )}
    </div>
  );
}