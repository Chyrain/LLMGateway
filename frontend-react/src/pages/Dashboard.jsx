import React, { useState, useEffect, useRef } from 'react';
import { Row, Col, Card, Statistic, Progress, Tag, Button, Empty, Alert, Timeline } from 'antd';
import {
  MessageOutlined,
  AppstoreOutlined,
  DollarOutlined,
  SwapOutlined,
  ApiOutlined,
  BellOutlined
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { statsApi, modelApi } from '../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalRequests: 0,
    activeModels: 0,
    totalQuota: 0,
    switchCount: 0
  });
  const [currentModel, setCurrentModel] = useState(null);
  const [switchLogs, setSwitchLogs] = useState([]);
  const [alertModels, setAlertModels] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [modelRankings, setModelRankings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    fetchTrendData();
    fetchModelRankings();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await statsApi.dashboard();
      if (response.code === 200 && response.data) {
        const data = response.data;
        setStats(data.stats || stats);
        setCurrentModel(data.currentModel || null);
        setSwitchLogs(data.switchLogs || []);
        setAlertModels(data.alertModels || []);
      }
    } catch (error) {
      console.error('获取仪表盘数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTrendData = async () => {
    try {
      const response = await statsApi.trends({ days: 7 });
      if (response.code === 200 && response.data) {
        setTrendData(response.data.trend || []);
      } else {
        setTrendData(generateMockTrendData(7));
      }
    } catch (error) {
      console.error('获取趋势数据失败:', error);
      setTrendData(generateMockTrendData(7));
    }
  };

  const fetchModelRankings = async () => {
    try {
      const response = await statsApi.models();
      if (response.code === 200 && response.data) {
        const rankings = response.data.rankings || [];
        setModelRankings(rankings.map(item => ({
          value: item.requests,
          name: item.model
        })));
      } else {
        setModelRankings(generateMockRankingData());
      }
    } catch (error) {
      console.error('获取模型排行失败:', error);
      setModelRankings(generateMockRankingData());
    }
  };

  const generateMockTrendData = (days) => {
    const data = [];
    const now = new Date();
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      data.push({
        date: date.toISOString().split('T')[0],
        requests: Math.floor(Math.random() * 200) + 50
      });
    }
    return data;
  };

  const generateMockRankingData = () => {
    return [
      { value: 1048, name: 'GPT-4' },
      { value: 735, name: 'Claude-3' },
      { value: 580, name: '通义千问' },
      { value: 484, name: '智谱清言' },
      { value: 300, name: '其他' }
    ];
  };

  const getQuotaStatus = (ratio) => {
    if (ratio >= 90) return 'exception';
    if (ratio >= 70) return 'warning';
    return 'success';
  };

  const handleTestModel = async (id) => {
    try {
      await modelApi.test(id);
    } catch (error) {
      console.error('测试失败:', error);
    }
  };

  const handleSwitchModel = async (id) => {
    try {
      // 重新获取数据
      fetchDashboardData();
    } catch (error) {
      console.error('切换失败:', error);
    }
  };

  const trendChartOption = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['请求量'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: trendData.map(item => item.date)
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '请求量',
        type: 'line',
        smooth: true,
        data: trendData.map(item => item.requests),
        areaStyle: { opacity: 0.1 },
        itemStyle: { color: '#667eea' }
      }
    ]
  };

  const pieChartOption = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', left: 'left' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 16 } },
        data: modelRankings
      }
    ]
  };

  return (
    <div>
      {alertModels.length > 0 && (
        <Alert
          message={`${alertModels.length}个模型额度即将耗尽`}
          type="warning"
          showIcon
          style={{ marginBottom: 20 }}
          action={
            <Button size="small" type="text" onClick={() => window.location.href = '/quota'}>
              立即处理
            </Button>
          }
        />
      )}

      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col span={6}>
          <Card className="stat-card">
            <Statistic
              title="今日请求量"
              value={stats.totalRequests}
              prefix={<MessageOutlined style={{ color: '#667eea' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="stat-card">
            <Statistic
              title="活跃模型"
              value={stats.activeModels}
              prefix={<AppstoreOutlined style={{ color: '#f5576c' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="stat-card">
            <Statistic
              title="剩余额度(Tokens)"
              value={stats.totalQuota}
              suffix="M"
              prefix={<DollarOutlined style={{ color: '#00f2fe' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="stat-card">
            <Statistic
              title="今日切换次数"
              value={stats.switchCount}
              prefix={<SwapOutlined style={{ color: '#43e97b' }} />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col span={16}>
          <Card title="近7天请求量趋势">
            <ReactECharts option={trendChartOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="模型使用占比">
            <ReactECharts option={pieChartOption} style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[20, 20]}>
        <Col span={12}>
          <Card
            title={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>当前使用模型</span>
                <Tag color="success">运行中</Tag>
              </div>
            }
            className="model-status-card"
          >
            {currentModel ? (
              <div className="current-model">
                <div className="model-header">
                  <div style={{
                    width: 48,
                    height: 48,
                    borderRadius: 8,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 24
                  }}>
                    🤖
                  </div>
                  <div>
                    <div className="model-name">{currentModel.vendor} - {currentModel.model_name}</div>
                    <div className="model-meta">
                      <Tag>{currentModel.priority}号优先级</Tag>
                      <span>剩余额度: {currentModel.remain_quota}M Tokens</span>
                    </div>
                  </div>
                </div>
                <Progress
                  percent={currentModel.used_ratio}
                  status={getQuotaStatus(currentModel.used_ratio)}
                  strokeWidth={10}
                />
                <div className="model-actions">
                  <Button type="primary" icon={<ApiOutlined />} onClick={() => handleTestModel(currentModel.id)}>
                    测试连通
                  </Button>
                  <Button onClick={() => handleSwitchModel(currentModel.id)}>
                    立即切换
                  </Button>
                </div>
              </div>
            ) : (
              <Empty description="暂无可用模型，请先添加模型配置" />
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card
            title={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>最近切换日志</span>
                <Button type="link" onClick={() => window.location.href = '/logs'}>
                  查看全部
                </Button>
              </div>
            }
            className="switch-log-card"
          >
            {switchLogs.length > 0 ? (
              <Timeline
                items={switchLogs.map(log => ({
                  color: log.status === 1 ? 'green' : 'red',
                  children: (
                    <div className="log-item">
                      <div className="log-action">
                        {log.from_model} → {log.to_model}
                      </div>
                      <div className="log-reason">{log.reason}</div>
                      <div style={{ fontSize: 12, color: '#999' }}>
                        {log.create_time}
                      </div>
                    </div>
                  )
                }))}
              />
            ) : (
              <Empty description="暂无切换日志" />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
