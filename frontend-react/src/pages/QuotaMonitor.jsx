import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, Progress, Space, Statistic, Row, Col, Modal, Form, InputNumber, message, DatePicker, List } from 'antd';
import { SyncOutlined, EditOutlined, ReloadOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { quotaApi, configApi, statsApi } from '../services/api';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

const QuotaMonitor = () => {
  const [quotaList, setQuotaList] = useState([]);
  const [historyData, setHistoryData] = useState([]);
  const [usageTrend, setUsageTrend] = useState([]);
  const [modelRanking, setModelRanking] = useState([]);
  const [switchThreshold, setSwitchThreshold] = useState(99);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editForm] = Form.useForm();
  const [editingRow, setEditingRow] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState([dayjs().subtract(30, 'days'), dayjs()]);

  useEffect(() => {
    fetchQuotaData();
    fetchHistoryData();
    fetchUsageTrend();
    fetchModelRanking();
    fetchSwitchThreshold();
  }, [dateRange]);

  const fetchQuotaData = async () => {
    try {
      const response = await statsApi.quota();
      if (response.code === 200) {
        setQuotaList(response.data?.models || []);
      }
    } catch (error) {
      console.error('获取额度数据失败:', error);
    }
  };

  const fetchHistoryData = async () => {
    try {
      const response = await quotaApi.history({ days: 30 });
      if (response.code === 200) {
        setHistoryData(response.data || []);
      }
    } catch (error) {
      console.error('获取历史数据失败:', error);
    }
  };

  const fetchUsageTrend = async () => {
    try {
      const [start, end] = dateRange;
      const days = end.diff(start, 'day') + 1;
      const response = await statsApi.trends({ days });
      if (response.code === 200) {
        setUsageTrend(response.data?.trend || []);
      }
    } catch (error) {
      console.error('获取使用趋势失败:', error);
    }
  };

  const fetchModelRanking = async () => {
    try {
      const response = await statsApi.models();
      if (response.code === 200) {
        setModelRanking(response.data?.rankings || []);
      }
    } catch (error) {
      console.error('获取模型排行失败:', error);
    }
  };

  const fetchSwitchThreshold = async () => {
    try {
      const response = await configApi.get('switch_threshold');
      if (response.code === 200) {
        setSwitchThreshold(parseInt(response.data?.config_value) || 99);
      }
    } catch (error) {
      console.error('获取切换阈值失败:', error);
    }
  };

  const handleSync = async (modelId) => {
    try {
      setLoading(true);
      const response = await quotaApi.sync(modelId);
      if (response.code === 200) {
        message.success('额度同步成功');
        fetchQuotaData();
      } else {
        message.error(response.msg || '额度同步失败');
      }
    } catch (error) {
      message.error('额度同步失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSyncAll = async () => {
    try {
      setLoading(true);
      for (const item of quotaList) {
        await quotaApi.sync(item.model_id);
      }
      message.success('全部额度同步完成');
      fetchQuotaData();
    } catch (error) {
      message.error('同步失败');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (record) => {
    setEditingRow(record);
    editForm.setFieldsValue({
      total_quota: record.total,
      used_quota: record.used
    });
    setEditModalVisible(true);
  };

  const handleSave = async () => {
    try {
      const values = await editForm.validateFields();
      await quotaApi.update(editingRow.model_id, values);
      message.success('额度更新成功');
      setEditModalVisible(false);
      fetchQuotaData();
    } catch (error) {
      console.error('更新失败:', error);
    }
  };

  const total = quotaList.reduce((sum, item) => sum + (item.total || 0), 0);
  const used = quotaList.reduce((sum, item) => sum + (item.used || 0), 0);
  const remain = total - used;
  const usageRate = total > 0 ? ((used / total) * 100).toFixed(1) : 0;

  const sufficientCount = quotaList.filter(item => (item.usage_rate || 0) < 70).length;
  const warningCount = quotaList.filter(item => (item.usage_rate || 0) >= 70 && (item.usage_rate || 0) < 90).length;
  const alertCount = quotaList.filter(item => (item.usage_rate || 0) >= 90).length;

  const usageChartOption = {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: Array.isArray(usageTrend) ? usageTrend.map(item => item.date) : []
    },
    yAxis: { type: 'value' },
    series: [{
      data: Array.isArray(usageTrend) ? usageTrend.map(item => item.requests) : [],
      type: 'line',
      smooth: false,
      areaStyle: { opacity: 0.3 },
      itemStyle: { color: '#1890ff' }
    }]
  };

  const rankingChartOption = {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: Array.isArray(modelRanking) ? modelRanking.slice(0, 5).map(item => ({
        value: item.requests || 0,
        name: item.model || '未知'
      })) : []
    }]
  };

  const statusColors = {
    success: { bg: '#f6ffed', border: '#52c41a', text: '#135200' },
    warning: { bg: '#fffbe6', border: '#faad14', text: '#ad6800' },
    danger: { bg: '#fff2f0', border: '#ff4d4f', text: '#cf1322' }
  };

  const columns = [
    {
      title: '模型',
      key: 'model',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Tag color="blue">{record.vendor}</Tag>
          <span style={{ fontWeight: 500 }}>{record.model_name}</span>
        </Space>
      )
    },
    {
      title: '总额度',
      dataIndex: 'total',
      render: (val) => val >= 1000000 ? `${(val / 1000000).toFixed(2)}M` : val?.toLocaleString() || '0'
    },
    {
      title: '已用额度',
      dataIndex: 'used',
      render: (val) => val >= 1000000 ? `${(val / 1000000).toFixed(2)}M` : val?.toLocaleString() || '0'
    },
    {
      title: '剩余额度',
      dataIndex: 'remain',
      render: (val) => val >= 1000000 ? `${(val / 1000000).toFixed(2)}M` : val?.toLocaleString() || '0'
    },
    {
      title: '使用率',
      dataIndex: 'usage_rate',
      render: (val) => {
        const status = val >= 90 ? 'exception' : val >= 70 ? 'warning' : 'success';
        const color = status === 'exception' ? '#cf1322' : status === 'warning' ? '#d46b08' : '#389e0d';
        return (
          <div style={{ minWidth: 120 }}>
            <Progress
              percent={val}
              size="small"
              status={status}
              strokeColor={color}
              format={(p) => `${p?.toFixed(1)}%`}
            />
          </div>
        );
      }
    },
    {
      title: '同步时间',
      dataIndex: 'last_sync_time',
      render: (val) => val || '未同步'
    },
    {
      title: '操作',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<SyncOutlined spin={loading} />}
            onClick={() => handleSync(record.model_id)}
            loading={loading}
          >
            同步
          </Button>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div>
      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col span={6}>
          <Card>
            <Statistic title="总额度" value={total / 1000000} suffix="M Tokens" precision={2} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="已用额度" value={used / 1000000} suffix="M" precision={2} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="剩余额度" value={remain / 1000000} suffix="M" precision={2} valueStyle={{ color: '#389e0d' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div style={{ marginBottom: 8 }}>总体使用率</div>
            <Progress
              percent={usageRate}
              size="small"
              status={usageRate >= 90 ? 'exception' : usageRate >= 70 ? 'warning' : 'success'}
              strokeColor={usageRate >= 90 ? '#cf1322' : usageRate >= 70 ? '#faad14' : '#52c41a'}
              format={(p) => `${p}%`}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col span={16}>
          <Card
            title="📈 使用趋势"
            extra={
              <Space>
                <RangePicker
                  value={dateRange}
                  onChange={(dates) => dates && setDateRange(dates)}
                />
                <Button icon={<ReloadOutlined />} onClick={() => fetchUsageTrend()}>刷新</Button>
              </Space>
            }
          >
            <ReactECharts option={usageChartOption} style={{ height: 280 }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="🚨 额度状态分布">
            <div style={{ padding: '10px 0' }}>
              <div style={{
                marginBottom: 16,
                padding: 16,
                borderRadius: 8,
                background: statusColors.success.bg,
                border: `1px solid ${statusColors.success.border}`,
                color: statusColors.success.text
              }}>
                <div style={{ fontSize: 24, fontWeight: 600 }}>{sufficientCount}</div>
                <div>充足 (使用率 &lt; 70%)</div>
              </div>
              <div style={{
                marginBottom: 16,
                padding: 16,
                borderRadius: 8,
                background: statusColors.warning.bg,
                border: `1px solid ${statusColors.warning.border}`,
                color: statusColors.warning.text
              }}>
                <div style={{ fontSize: 24, fontWeight: 600 }}>{warningCount}</div>
                <div>预警 (70% ≤ 使用率 &lt; 90%)</div>
              </div>
              <div style={{
                padding: 16,
                borderRadius: 8,
                background: statusColors.danger.bg,
                border: `1px solid ${statusColors.danger.border}`,
                color: statusColors.danger.text
              }}>
                <div style={{ fontSize: 24, fontWeight: 600 }}>{alertCount}</div>
                <div>告警 (使用率 ≥ 90%)</div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col span={12}>
          <Card title="🏆 模型使用排行 (Top 5)">
            <List
              size="small"
              dataSource={modelRanking.slice(0, 5)}
              renderItem={(item, index) => (
                <List.Item>
                  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Space>
                      <Tag color={index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : 'default'}>{index + 1}</Tag>
                      <span>{item.model}</span>
                    </Space>
                    <Space>
                      <span style={{ color: '#1890ff' }}>{item.requests?.toLocaleString()}</span>
                      <span style={{ color: '#999' }}>({item.percentage}%)</span>
                    </Space>
                  </Space>
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="📊 模型使用占比">
            <ReactECharts option={rankingChartOption} style={{ height: 250 }} />
          </Card>
        </Col>
      </Row>

      <Card
        title="📋 模型额度列表"
        extra={
          <Button type="primary" icon={<SyncOutlined />} onClick={handleSyncAll} loading={loading}>
            全部同步
          </Button>
        }
      >
        <Table
          dataSource={quotaList}
          columns={columns}
          rowKey="model_id"
          pagination={{ pageSize: 10 }}
          loading={loading}
        />
      </Card>

      <Modal
        title="编辑额度"
        open={editModalVisible}
        onOk={handleSave}
        onCancel={() => setEditModalVisible(false)}
      >
        <Form form={editForm} layout="vertical">
          <Form.Item name="total_quota" label="总额度 (Tokens)">
            <InputNumber min={0} style={{ width: '100%' }} placeholder="请输入总额度" />
          </Form.Item>
          <Form.Item name="used_quota" label="已用额度 (Tokens)">
            <InputNumber min={0} style={{ width: '100%' }} placeholder="请输入已用额度" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default QuotaMonitor;
