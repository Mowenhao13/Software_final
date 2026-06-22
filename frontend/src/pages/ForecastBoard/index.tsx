import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Select, Spin, Tag, Table, Empty, Progress, Statistic, Tooltip, Segmented } from 'antd';
import {
  ArrowUpOutlined, ArrowDownOutlined, MinusOutlined,
  InfoCircleOutlined, ThunderboltOutlined, ExperimentOutlined,
  RiseOutlined, FallOutlined,
} from '@ant-design/icons';
import BaseChart from '../../components/Charts/BaseChart';
import { getForecastItems, getForecastModels, getDemandForecast, getDemandHistory } from '../../api';

const catColors: Record<string, string> = {
  electronics: '#1890ff', apparel: '#722ed1', automotive: '#fa8c16',
  food: '#52c41a', pharma: '#eb2f96',
};

export default function ForecastBoard() {
  const [items, setItems] = useState<any[]>([]);
  const [selectedItem, setSelectedItem] = useState<string>('');
  const [model, setModel] = useState<string>('auto');
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  const [forecast, setForecast] = useState<any>(null);
  const [historyData, setHistoryData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      getForecastItems(),
      getForecastModels(),
    ]).then(([itemsRes, modelsRes]) => {
      setItems(itemsRes as any[]);
      setAvailableModels(modelsRes as any[]);
    });
  }, []);

  const fetchForecast = () => {
    if (!selectedItem) return;
    setLoading(true);
    Promise.all([
      getDemandForecast(selectedItem, 12, model),
      getDemandHistory(selectedItem, 52),
    ])
      .then(([fc, hd]) => {
        setForecast(fc);
        setHistoryData(hd);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchForecast(); }, [selectedItem, model]);

  const trendIcon = (t: string) => {
    if (t === 'up') return <Tag icon={<RiseOutlined />} color="red"><ArrowUpOutlined /> 上升</Tag>;
    if (t === 'down') return <Tag icon={<FallOutlined />} color="green"><ArrowDownOutlined /> 下降</Tag>;
    return <Tag icon={<MinusOutlined />} color="blue">平稳</Tag>;
  };

  // ====== 品类颜色 ======
  const category = forecast?.category || '';
  const catColor = catColors[category] || '#999';

  // ====== 预测主图表 ======
  const forecastChartOption = forecast ? (() => {
    const histLen = forecast.history?.length || 0;
    const labels = [
      ...(forecast.history || []).map((_: any, i: number) => `W${i - histLen + 1}`),
      ...forecast.forecast.map((_: any, i: number) => `+${i + 1}w`),
    ];
    return {
      title: { text: '需求预测曲线 (历史+预测)', left: 'center', textStyle: { fontSize: 14 } },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          const p = params[0];
          const i = p.dataIndex;
          const isFc = i >= histLen;
          if (isFc) {
            const fIdx = i - histLen;
            const d = forecast.forecast[fIdx];
            return `<b>第+${d.week}周</b><br/>预测值: <b>${d.predicted}</b><br/>90%区间: [${d.p10}, ${d.p90}]<br/>区间宽度: ${(d.p90 - d.p10).toFixed(1)}`;
          }
          return `<b>W${i - histLen + 1}</b><br/>历史需求: <b>${forecast.history[i]}</b>`;
        },
      },
      legend: { data: ['历史需求', '预测值', '90%置信区间'], bottom: 0, textStyle: { fontSize: 11 } },
      grid: { left: 60, right: 30, top: 40, bottom: 40 },
      xAxis: { type: 'category', data: labels, axisLabel: { rotate: 45, fontSize: 10 } },
      yAxis: { type: 'value', name: '需求量', nameTextStyle: { fontSize: 11 } },
      series: [
        {
          name: '90%置信区间',
          type: 'line',
          data: [...forecast.history.map(() => null), ...forecast.forecast.map((f: any) => f.p90)],
          lineStyle: { opacity: 0 }, symbol: 'none',
          areaStyle: { color: 'rgba(24, 144, 255, 0.08)' },
        },
        {
          name: '90%置信区间',
          type: 'line',
          data: [...forecast.history.map(() => null), ...forecast.forecast.map((f: any) => f.p10)],
          lineStyle: { opacity: 0 }, symbol: 'none',
          areaStyle: { color: 'rgba(24, 144, 255, 0.08)' },
        },
        {
          name: '历史需求',
          type: 'line', data: forecast.history,
          smooth: true, symbol: 'none',
          lineStyle: { color: '#1890ff', width: 2 },
          areaStyle: { color: 'rgba(24, 144, 255, 0.04)' },
        },
        {
          name: '预测值',
          type: 'line',
          data: [...forecast.history.map(() => null), ...forecast.forecast.map((f: any) => f.predicted)],
          smooth: true,
          lineStyle: { color: '#ff4d4f', width: 2, type: 'dashed' },
          itemStyle: { color: '#ff4d4f' },
          symbol: 'diamond', symbolSize: 8,
        },
      ],
    };
  })() : null;

  // ====== 52周历史概览 ======
  const historyOverviewOption = historyData ? {
    title: { text: `近 ${historyData.history.length} 周需求概览`, left: 'center', textStyle: { fontSize: 13 } },
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 35, bottom: 30 },
    xAxis: { type: 'category', data: historyData.labels, axisLabel: { fontSize: 9, interval: 'auto' as const } },
    yAxis: { type: 'value', name: '需求量', nameTextStyle: { fontSize: 10 } },
    visualMap: {
      show: false,
      pieces: [
        { lt: historyData.history.reduce((a: number, b: number) => a + b, 0) / historyData.history.length, color: '#91d5ff' },
        { gte: historyData.history.reduce((a: number, b: number) => a + b, 0) / historyData.history.length, color: '#ff4d4f' },
      ],
    },
    series: [{
      type: 'bar',
      data: historyData.history,
      itemStyle: {
        color: (p: any) => {
          const avg = historyData.history.reduce((a: number, b: number) => a + b, 0) / historyData.history.length;
          return p.value >= avg ? '#ff4d4f' : '#91d5ff';
        },
        borderRadius: [2, 2, 0, 0],
      },
    }],
  } : null;

  // ====== 历史分布直方图 ======
  const distOption = forecast ? (() => {
    const hist = forecast.history || [];
    if (hist.length === 0) return null;
    const min = Math.min(...hist);
    const max = Math.max(...hist);
    const binCount = 8;
    const binWidth = (max - min) / binCount || 1;
    const bins = Array.from({ length: binCount }, (_, i) => {
      const lo = min + i * binWidth;
      const hi = lo + binWidth;
      return { range: `${lo.toFixed(0)}-${hi.toFixed(0)}`, count: hist.filter((v: number) => v >= lo && v < hi).length };
    });
    // 预测均值位置
    const fcAvg = forecast.forecast.reduce((s: number, f: any) => s + f.predicted, 0) / forecast.forecast.length;
    return {
      title: { text: '历史需求分布', left: 'center', textStyle: { fontSize: 13 } },
      tooltip: { trigger: 'axis' },
      grid: { left: 50, right: 40, top: 35, bottom: 30 },
      xAxis: { type: 'category', data: bins.map((b: any) => b.range), axisLabel: { fontSize: 9 } },
      yAxis: { type: 'value', name: '频次', nameTextStyle: { fontSize: 10 } },
      series: [
        {
          type: 'bar', data: bins.map((b: any) => b.count),
          itemStyle: { color: '#1890ff', borderRadius: [4, 4, 0, 0] },
        },
        {
          type: 'line',
          data: bins.map((b: any) => {
            const lo = parseFloat(b.range.split('-')[0]);
            const hi = parseFloat(b.range.split('-')[1]);
            return (fcAvg >= lo && fcAvg <= hi) ? max * 0.1 : null;
          }),
          symbol: 'diamond', symbolSize: 16,
          lineStyle: { opacity: 0 },
          itemStyle: { color: '#ff4d4f' },
          name: '预测均值位置',
        },
      ],
    };
  })() : null;

  // ====== 品类对比 ======
  const categoryCard = forecast ? (() => {
    const avgs = items.filter((i: any) => i.category === category).map((i: any) => i.avg_weekly);
    const catAvg = avgs.length > 0 ? avgs.reduce((a: number, b: number) => a + b, 0) / avgs.length : 0;
    return { catAvg, itemAvg: forecast?.hist_stats?.mean || 0 };
  })() : null;

  // ====== 预测周分解表格 ======
  const fcColumns = [
    { title: '预测周', dataIndex: 'week', key: 'w', width: 70, render: (v: number) => `+${v}周` },
    { title: '预测值', dataIndex: 'predicted', key: 'p', width: 90, sorter: (a: any, b: any) => a.predicted - b.predicted,
      render: (v: number) => <span style={{ fontWeight: 600, color: v > (forecast?.hist_stats?.mean || 0) ? '#ff4d4f' : '#52c41a' }}>{v.toFixed(1)}</span> },
    { title: 'p10(下限)', dataIndex: 'p10', key: 'p10', width: 90, render: (v: number) => <span style={{ color: '#999' }}>{v.toFixed(1)}</span> },
    { title: 'p90(上限)', dataIndex: 'p90', key: 'p90', width: 90, render: (v: number) => <span style={{ color: '#999' }}>{v.toFixed(1)}</span> },
    { title: '区间宽度', key: 'width', width: 90,
      render: (_: any, r: any) => (r.p90 - r.p10).toFixed(1) },
    { title: '置信区间可视化', key: 'bar', render: (_: any, r: any) => {
      const itemAvg = forecast?.hist_stats?.mean || 100;
      const minVal = Math.min(r.p10, 0);
      const maxVal = Math.max(r.p90, itemAvg * 1.5);
      const range = maxVal - minVal || 1;
      const leftPct = ((r.p10 - minVal) / range) * 100;
      const widthPct = ((r.p90 - r.p10) / range) * 100;
      return (
        <div style={{ position: 'relative', width: '100%', height: 20, background: '#f5f5f5', borderRadius: 4 }}>
          <div style={{ position: 'absolute', left: `${leftPct}%`, width: `${widthPct}%`, height: '100%',
            background: 'rgba(24, 144, 255, 0.3)', borderRadius: 4 }}/>
          <div style={{ position: 'absolute', left: `${((r.predicted - minVal) / range) * 100}%`, top: 0,
            width: 2, height: '100%', background: '#ff4d4f' }}/>
        </div>
      );
    }},
  ];

  const histStats = forecast?.hist_stats;

  return (
    <div>
      {/* ===== 顶部选择区 ===== */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card bodyStyle={{ padding: '16px 24px' }}>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center' }}>
              <Select
                placeholder="选择要预测的物品"
                style={{ width: 260 }}
                value={selectedItem || undefined}
                onChange={setSelectedItem}
                showSearch
                filterOption={(input: string, opt: any) => (opt?.label as string)?.toLowerCase().includes(input.toLowerCase())}
                options={items.map((i: any) => ({
                  value: i.item_id,
                  label: `${i.name && i.name !== i.item_id ? i.name : i.item_id} | ${i.category} (${(i.weeks / 52).toFixed(0)}年数据)`,
                }))}
              />
              {category && <Tag color={catColor} style={{ fontSize: 13, padding: '2px 12px' }}>{category}</Tag>}
              <Segmented
                value={model}
                onChange={(v) => setModel(v as string)}
                options={[
                  { value: 'auto', label: <><ThunderboltOutlined /> 自动</> },
                  ...availableModels.filter(m => m.status === 'ready').map(m => ({
                    value: m.name,
                    label: <><ExperimentOutlined /> {m.name === 'chronos-2' ? 'Chronos-2' : m.name}</>,
                  })),
                ]}
              />
              {forecast && (
                <span style={{ color: '#999', fontSize: 12 }}>
                  <InfoCircleOutlined /> 方法: {forecast.method === 'chronos-2' ? 'Chronos-2' : forecast.method}
                  {' | '}上下文: {forecast.context_length || '?'} 周
                </span>
              )}
            </div>
          </Card>
        </Col>
      </Row>

      {loading && <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>}
      {!selectedItem && !loading && <Card style={{ marginTop: 16 }}><Empty description="请选择物品查看详细需求预测分析" /></Card>}

      {/* ===== KPI 卡片区 ===== */}
      {forecast && !loading && (
        <>
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col xs={12} sm={8} md={4}>
              <Card size="small" hoverable>
                <Statistic
                  title={<Tooltip title="近4周平均需求量 vs 未来4周预测均值">近4周平均 vs 预测</Tooltip>}
                  value={histStats?.recent_4w_avg || 0}
                  suffix={
                    <span style={{ fontSize: 14, marginLeft: 4 }}>
                      → {(forecast.forecast.slice(0, 4).reduce((s: number, f: any) => s + f.predicted, 0) / 4).toFixed(1)}
                    </span>
                  }
                  precision={1}
                  valueStyle={{ fontSize: 18, fontWeight: 700 }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={4}>
              <Card size="small" hoverable>
                <Statistic
                  title={<Tooltip title="Chronos-2 模型预测置信度">预测置信度</Tooltip>}
                  value={(forecast.confidence || 0) * 100}
                  suffix="%"
                  precision={1}
                  valueStyle={{ fontSize: 18, fontWeight: 700, color: (forecast.confidence || 0) > 0.7 ? '#52c41a' : '#faad14' }}
                />
                <Progress
                  percent={Math.round((forecast.confidence || 0) * 100)}
                  showInfo={false}
                  strokeColor={(forecast.confidence || 0) > 0.7 ? '#52c41a' : '#faad14'}
                  size="small"
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={4}>
              <Card size="small" hoverable>
                <Statistic
                  title={<Tooltip title="变异系数 (CV)=标准差/均值，衡量波动性">波动率 (CV)</Tooltip>}
                  value={histStats?.cv || 0}
                  precision={2}
                  valueStyle={{ fontSize: 18, fontWeight: 700, color: (histStats?.cv || 0) > 0.5 ? '#ff4d4f' : '#1890ff' }}
                  suffix={<span style={{ fontSize: 12, color: '#999' }}>{(histStats?.cv || 0) > 0.5 ? '高波动' : '低波动'}</span>}
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={4}>
              <Card size="small" hoverable>
                <Statistic
                  title={<Tooltip title="该品类所有物品的平均周需求 vs 当前物品">品类均值 vs 本物品</Tooltip>}
                  value={categoryCard?.itemAvg || 0}
                  suffix={
                    <span style={{ fontSize: 14, marginLeft: 4 }}>
                      / {(categoryCard?.catAvg || 0).toFixed(1)}
                    </span>
                  }
                  precision={1}
                  valueStyle={{ fontSize: 18, fontWeight: 700, color: (categoryCard?.itemAvg || 0) > (categoryCard?.catAvg || 0) ? '#ff4d4f' : '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={4}>
              <Card size="small" hoverable>
                <Statistic
                  title={<Tooltip title="未来4周均值 vs 近8周均值的变化率">增长趋势</Tooltip>}
                  value={(() => {
                    const fc4 = forecast.forecast.slice(0, 4).reduce((s: number, f: any) => s + f.predicted, 0) / 4;
                    const recent = histStats?.recent_8w_avg || 1;
                    return ((fc4 - recent) / recent * 100).toFixed(1);
                  })()}
                  suffix="%"
                  precision={1}
                  valueStyle={{ fontSize: 18, fontWeight: 700, color: forecast.trend === 'up' ? '#ff4d4f' : forecast.trend === 'down' ? '#52c41a' : '#1890ff' }}
                />
                {trendIcon(forecast.trend)}
              </Card>
            </Col>
            <Col xs={12} sm={8} md={4}>
              <Card size="small" hoverable>
                <Statistic
                  title={<Tooltip title="近2年历史最大值 vs 最小值">历史极值 (近2年)</Tooltip>}
                  value={histStats?.max || 0}
                  suffix={<span style={{ fontSize: 14, color: '#999' }}> / {histStats?.min || 0}</span>}
                  valueStyle={{ fontSize: 18, fontWeight: 700 }}
                />
              </Card>
            </Col>
          </Row>

          {/* ===== 图表区 ===== */}
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col span={24}>
              <Card>
                <div style={{ width: '100%', height: 450 }}>
                  <BaseChart option={forecastChartOption} height={450} />
                </div>
              </Card>
            </Col>
          </Row>

          {/* ===== 分布 + 历史 + 对比 ===== */}
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col xs={24} md={8}>
              <Card size="small" style={{ height: 300 }}>
                <div style={{ width: '100%', height: 270 }}>
                  <BaseChart option={distOption} height={270} />
                </div>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card size="small" style={{ height: 300 }}>
                <div style={{ width: '100%', height: 270 }}>
                  <BaseChart option={historyOverviewOption} height={270} />
                </div>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card size="small" title="品类对比 & 详细统计" style={{ height: 300 }}>
                <div style={{ padding: '4px 0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                    <span style={{ color: '#666' }}>品类</span>
                    <Tag color={catColor}>{forecast.category}</Tag>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                    <span style={{ color: '#666' }}>品类周均</span>
                    <strong>{(categoryCard?.catAvg || 0).toFixed(1)}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                    <span style={{ color: '#666' }}>物品周均</span>
                    <strong>{histStats?.mean || 0}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                    <span style={{ color: '#666' }}>近4周均值</span>
                    <strong>{histStats?.recent_4w_avg || 0}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                    <span style={{ color: '#666' }}>标准差</span>
                    <strong>{histStats?.std || 0}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
                    <span style={{ color: '#666' }}>总需求</span>
                    <strong>{(histStats?.total || 0).toLocaleString()}</strong>
                  </div>
                </div>
              </Card>
            </Col>
          </Row>

          {/* ===== 预测明细表 ===== */}
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col span={24}>
              <Card title={
                <span>
                  逐周预测明细
                  <Tag style={{ marginLeft: 12 }} color="blue">未来12周</Tag>
                  <span style={{ fontSize: 12, color: '#999', marginLeft: 8 }}>
                    均值: {(forecast.forecast.reduce((s: number, f: any) => s + f.predicted, 0) / forecast.forecast.length).toFixed(1)}
                    {' | '}合计: {forecast.forecast.reduce((s: number, f: any) => s + f.predicted, 0).toFixed(0)}
                  </span>
                </span>
              }>
                <Table
                  dataSource={forecast.forecast}
                  rowKey="week"
                  columns={fcColumns}
                  pagination={false}
                  size="small"
                  scroll={{ x: 650 }}
                />
              </Card>
            </Col>
          </Row>
        </>
      )}
    </div>
  );
}