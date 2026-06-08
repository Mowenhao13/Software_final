import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Spin, Statistic, Descriptions, Tag } from 'antd';
import BaseChart from '../../components/Charts/BaseChart';
import { getShipmentMap, getShipmentStats, getSupplierDist } from '../../api';

export default function SupplyChain() {
  const [mapData, setMapData] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [supplierDist, setSupplierDist] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getShipmentMap(), getShipmentStats(), getSupplierDist()])
      .then(([m, s, sd]) => {
        setMapData(m);
        setStats(s);
        setSupplierDist(sd as any[]);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ textAlign: 'center', padding: 120 }}><Spin size="large" /></div>;

  // 中国地图物流路线图 (散点模拟)
  const mapOption = {
    backgroundColor: '#f7f9fc',
    tooltip: { trigger: 'item' },
    grid: { top: 10, bottom: 10, left: 10, right: 10 },
    xAxis: { type: 'value', min: 73, max: 136, show: false },
    yAxis: { type: 'value', min: 18, max: 54, show: false },
    series: [
      // 模拟中国边界轮廓点
      {
        type: 'scatter', data: [
          [121.47, 31.23], [116.40, 39.90], [114.07, 22.62], [113.26, 23.13],
          [104.07, 30.57], [114.30, 30.60], [118.78, 32.07], [108.93, 34.27],
          [120.15, 30.28], [106.55, 29.57], [117.20, 39.12], [112.97, 28.23],
          [102.83, 24.88], [113.62, 34.75], [126.53, 45.80],
        ],
        symbolSize: 12,
        itemStyle: { color: '#1890ff', borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: (p: any) => {
          const cities = ['上海','北京','深圳','广州','成都','武汉','南京','西安','杭州','重庆','天津','长沙','昆明','郑州','哈尔滨'];
          return cities[p.dataIndex] || '';
        }, fontSize: 10, position: 'right' },
      } as any,
      // 运输路线
      ...(mapData?.routes || []).slice(0, 15).map((route: any, i: number) => ({
        type: 'lines',
        coordinateSystem: 'cartesian2d',
        polyline: false,
        data: [{ coords: [route.origin_coords, route.dest_coords] }],
        lineStyle: {
          color: route.status === 'delayed' ? '#ff4d4f' : route.status === 'in_transit' ? '#1890ff' : '#52c41a',
          width: 1.5,
          opacity: 0.6,
        },
        effect: {
          show: route.status === 'in_transit',
          period: 4,
          trailLength: 0.2,
          symbolSize: 6,
        },
      } as any)),
    ],
  };

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={6}><Card><Statistic title="在途运输" value={stats?.in_transit || 0} suffix="单" /></Card></Col>
        <Col xs={6}><Card><Statistic title="延迟运输" value={stats?.delayed || 0} suffix="单" valueStyle={{ color: stats?.delayed > 0 ? '#ff4d4f' : undefined }} /></Card></Col>
        <Col xs={6}><Card><Statistic title="已交付" value={stats?.delivered || 0} suffix="单" /></Card></Col>
        <Col xs={6}><Card><Statistic title="准时率" value={stats?.on_time_rate || 95} suffix="%" /></Card></Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={16}>
          <Card title="供应链物流路线图" style={{ height: 500 }}>
            <BaseChart option={mapOption} height={440} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="在途物流详情" style={{ height: 500, overflow: 'auto' }}>
            {(mapData?.routes || []).slice(0, 12).map((r: any, i: number) => (
              <Card key={i} size="small" style={{ marginBottom: 8 }} type="inner">
                <Descriptions column={2} size="small">
                  <Descriptions.Item label="路线" span={2}>{r.origin} → {r.destination}</Descriptions.Item>
                  <Descriptions.Item label="承运商">{r.carrier}</Descriptions.Item>
                  <Descriptions.Item label="方式">
                    <Tag color={r.mode === 'air' ? 'red' : r.mode === 'sea' ? 'blue' : 'green'}>
                      {r.mode === 'air' ? '空运' : r.mode === 'sea' ? '海运' : r.mode === 'rail' ? '铁路' : '公路'}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="状态" span={2}>
                    <Tag color={r.status === 'delayed' ? 'red' : r.status === 'in_transit' ? 'blue' : 'green'}>
                      {r.status === 'delayed' ? '延迟' : r.status === 'in_transit' ? '在途' : '已交付'}
                    </Tag>
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            ))}
          </Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="供应商区域分布">
            <BaseChart option={{
              tooltip: { trigger: 'item' },
              series: [{
                type: 'pie', radius: '65%',
                data: supplierDist.map((s: any) => ({ name: s.region, value: s.count })),
                emphasis: { label: { fontSize: 16, fontWeight: 'bold' } },
              }],
            }} height={300} />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="运输方式统计">
            <BaseChart option={{
              tooltip: { trigger: 'axis' },
              grid: { left: 60, right: 20, top: 10, bottom: 30 },
              xAxis: { type: 'category', data: ['公路', '铁路', '空运', '海运'] },
              yAxis: { type: 'value' },
              series: [{
                type: 'bar', data: [
                  mapData?.routes?.filter((r: any) => r.mode === 'road').length || 0,
                  mapData?.routes?.filter((r: any) => r.mode === 'rail').length || 0,
                  mapData?.routes?.filter((r: any) => r.mode === 'air').length || 0,
                  mapData?.routes?.filter((r: any) => r.mode === 'sea').length || 0,
                ],
                itemStyle: { color: '#52c41a', borderRadius: [4, 4, 0, 0] },
              }],
            }} height={300} />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
