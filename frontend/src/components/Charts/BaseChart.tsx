import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Spin } from 'antd';

interface BaseChartProps {
  option: any;
  height?: number | string;
  loading?: boolean;
  style?: React.CSSProperties;
}

export default function BaseChart({ option, height = 350, loading = false, style }: BaseChartProps) {
  if (loading) {
    return <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Spin /></div>;
  }
  return (
    <ReactECharts
      option={option}
      style={{ height, width: '100%', ...style }}
      notMerge={true}
      lazyUpdate={true}
    />
  );
}
