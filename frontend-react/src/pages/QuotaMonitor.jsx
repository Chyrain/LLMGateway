import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, Progress, Space, Statistic, Row, Col, Modal, Form, InputNumber, message } from 'antd';
import { SyncOutlined, EditOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { quotaApi, configApi } from '../services/api';

const QuotaMonitor = () => {
  const [quotaList, setQuotaList] = useState([]);
  const [historyData, setHistoryData] = useState([]);
  const [switchThreshold, setSwitchThreshold] = useState(99);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editForm] = Form.useForm();
  const [editingRow, setEditingRow] = useState(null);

  useEffect(() => {
    fetchQuotaData();
    fetchHistoryData();
    fetchSwitchThreshold();
  }, []);

  const fetchQuotaData = async () => {
    try {
      const response = await quotaApi.stat();
      if (response.code === 200) {
        setQuotaList(response.data || []);
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
      const response = await quotaApi.sync(modelId);
      message.success('额度同步成功');
      fetchQuotaData();
    } catch (error) {
      message.error('额度同步失败');
    }
  };

  const handleEdit = (record) => {
    setEditingRow(record);
    editForm.setFieldsValue({
      total_quota: record.total_quota,
      used_quota: record.used_quota
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

  const total = quotaList.reduce((sum, item) => sum + (item.total_quota || 0), 0);
  const used = quotaList.reduce((sum, item) => sum + (item.used_quota || 0), 0);
  const remain = total - used;
  const usageRate = total > 0 ? ((used / total) * 100).toFixed(1) : 0;
  const alertCount = quotaList.filter(item => item.used_ratio >= switchThreshold).length;

  const historyChartOption = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['已用额度', '剩余额度'] },
    xAxis: {
      type: 'category',
      data: historyData.map(item => item.date)
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '已用额度',
        type: 'bar',
        stack: 'total',
        data: historyData.map(item => item.used_quota),
        itemStyle: { color: '#f5576c' }
      },
      {
        name: '剩余额度',
        type: 'bar',
        stack: 'total',
        data: historyData.map(item => item.remain_quota),
        itemStyle: { color: '#67C23A' }
      }
    ]
  };

  const columns = [
    {
      title: '模型ID',
      dataIndex: 'model_id'
    },
    {
      title: '总额度',
      dataIndex: 'total_quota',
      render: (val) => `${(val / 1000000).toFixed(2)}M`
    },
    {
      title: '已用额度',
      dataIndex: 'used_quota',
      render: (val) => `${(val / 1000000).toFixed(2)}M`
    },
    {
      title: '剩余额度',
      dataIndex: 'remain_quota',
      render: (val) => `${(val / 1000000).toFixed(2)}M`
    },
    {
      title: '使用率',
      dataIndex: 'used_ratio',
      render: (val, record) => (
        <Progress
          percent={val}
          size="small"
          status={val >= 90 ? 'exception' : val >= 70 ? 'warning' : 'success'}
        />
      )
    },
    {
      title: '同步类型',
      dataIndex: 'sync_type'
    },
    {
      title: '最后同步',
      dataIndex: 'last_sync_time'
    },
    {
      title: '操作',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<SyncOutlined />}
            onClick={() => handleSync(record.model_id)}
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
            <Statistic title="总额度" value={total / 1000000} suffix="M Tokens" />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="已用额度" value={used / 1000000} suffix="M" />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="剩余额度" value={remain / 1000000} suffix="M" />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div style={{ marginBottom: 8 }}>总体使用率</div>
            <Progress percent={usageRate} size="small" />
          </Card>
        </Col>
      </Row>

      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col span={16}>
          <Card title="近30天额度使用趋势">
            <ReactECharts option={historyChartOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="额度状态分布">
            <div style={{ textAlign: 'center', padding: 20 }}>
              <Tag color="success" style={{ margin: 4 }}>
                充足: {quotaList.filter(item => item.used_ratio < 70).length}
              </Tag>
              <Tag color="warning" style={{ margin: 4 }}>
                预警: {quotaList.filter(item => item.used_ratio >= 70 && item.used_ratio < 90).length}
              </Tag>
              <Tag color="danger" style={{ margin: 4 }}>
                告警: {quotaList.filter(item => item.used_ratio >= 90).length}
              </Tag>
            </div>
          </Card>
        </Col>
      </Row>

      <Card title="模型额度列表">
        <Table
          dataSource={quotaList}
          columns={columns}
          rowKey="model_id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="编辑额度"
        open={editModalVisible}
        onOk={handleSave}
        onCancel={() => setEditModalVisible(false)}
      >
        <Form form={editForm} layout="vertical">
          <Form.Item name="total_quota" label="总额度">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="used_quota" label="已用额度">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default QuotaMonitor;
