import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, Space, Select, DatePicker, Input, Radio, Drawer, message, Popconfirm } from 'antd';
import { SearchOutlined, DeleteOutlined, DownloadOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons';
import { logApi, modelApi } from '../services/api';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

const Logs = () => {
  const [tableData, setTableData] = useState([]);
  const [modelList, setModelList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  const [filters, setFilters] = useState({});
  const [detailVisible, setDetailVisible] = useState(false);
  const [currentLog, setCurrentLog] = useState(null);

  useEffect(() => {
    fetchData();
    fetchModels();
  }, [pagination.current, filters]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {
        page: pagination.current,
        size: pagination.pageSize,
        ...filters
      };
      const response = await logApi.list(params);
      if (response.code === 200) {
        setTableData(response.data || []);
        setPagination({ ...pagination, total: response.total || response.data?.length || 0 });
      }
    } catch (error) {
      message.error('获取日志失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchModels = async () => {
    try {
      const response = await modelApi.list();
      if (response.code === 200) {
        setModelList(response.data || []);
      }
    } catch (error) {
      console.error('获取模型列表失败:', error);
    }
  };

  const handleSearch = () => {
    setPagination({ ...pagination, current: 1 });
    fetchData();
  };

  const handleReset = () => {
    setFilters({});
    setPagination({ ...pagination, current: 1 });
    setTimeout(fetchData, 0);
  };

  const handleClear = async (logType) => {
    try {
      await logApi.clear(logType);
      message.success('日志已清空');
      fetchData();
    } catch (error) {
      message.error('清空失败');
    }
  };

  const handleExport = async () => {
    try {
      const response = await logApi.export(filters);
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'logs.csv';
      link.click();
      message.success('导出成功');
    } catch (error) {
      message.error('导出失败');
    }
  };

  const handleViewDetail = (record) => {
    setCurrentLog(record);
    setDetailVisible(true);
  };

  const getLogTypeName = (type) => {
    const map = { 1: '访问日志', 2: '切换日志', 3: '错误日志', 4: '测试日志' };
    return map[type] || '未知';
  };

  const getLogTypeColor = (type) => {
    const map = { 1: 'blue', 2: 'green', 3: 'red', 4: 'orange' };
    return map[type] || 'default';
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80
    },
    {
      title: '时间',
      dataIndex: 'create_time',
      width: 180
    },
    {
      title: '类型',
      dataIndex: 'log_type',
      render: (type) => <Tag color={getLogTypeColor(type)}>{getLogTypeName(type)}</Tag>
    },
    {
      title: '模型',
      dataIndex: 'model_id',
      render: (id) => {
        const model = modelList.find(m => m.id === id);
        return model ? `${model.vendor}/${model.model_name}` : `ID: ${id}`;
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      render: (status) => (
        status === 1 ?
          <Tag color="success">成功</Tag> :
          <Tag color="error">失败</Tag>
      )
    },
    {
      title: '内容',
      dataIndex: 'log_content',
      ellipsis: true
    },
    {
      title: '操作',
      render: (_, record) => (
        <Space>
          <Button type="text" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>
            详情
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div>
      <Card className="filter-card">
        <Space wrap>
          <Select
            placeholder="日志类型"
            allowClear
            style={{ width: 130 }}
            options={[
              { label: '访问日志', value: 1 },
              { label: '切换日志', value: 2 },
              { label: '错误日志', value: 3 },
              { label: '测试日志', value: 4 }
            ]}
            value={filters.log_type}
            onChange={(value) => setFilters({ ...filters, log_type: value })}
          />
          <Select
            placeholder="模型"
            allowClear
            style={{ width: 180 }}
            options={modelList.map(m => ({
              label: `${m.vendor}/${m.model_name}`,
              value: m.id
            }))}
            value={filters.model_id}
            onChange={(value) => setFilters({ ...filters, model_id: value })}
          />
          <Select
            placeholder="状态"
            allowClear
            style={{ width: 100 }}
            options={[
              { label: '成功', value: 1 },
              { label: '失败', value: 0 }
            ]}
            value={filters.status}
            onChange={(value) => setFilters({ ...filters, status: value })}
          />
          <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
            搜索
          </Button>
          <Button onClick={handleReset}>重置</Button>
        </Space>
      </Card>

      <Card
        title="日志列表"
        extra={
          <Space>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>
              导出
            </Button>
            <Popconfirm
              title="确定清空所有日志?"
              onConfirm={() => handleClear()}
            >
              <Button danger icon={<DeleteOutlined />}>
                清空
              </Button>
            </Popconfirm>
            <Button icon={<ReloadOutlined />} onClick={fetchData}>
              刷新
            </Button>
          </Space>
        }
        className="table-card"
      >
        <Table
          dataSource={tableData}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`
          }}
          onChange={(paginationInfo) => {
            setPagination({
              ...pagination,
              current: paginationInfo.current,
              pageSize: paginationInfo.pageSize
            });
          }}
        />
      </Card>

      <Drawer
        title="日志详情"
        open={detailVisible}
        onClose={() => setDetailVisible(false)}
        width={600}
      >
        {currentLog && (
          <div>
            <div className="detail-row">
              <span className="label">日志ID:</span>
              <span className="content">{currentLog.id}</span>
            </div>
            <div className="detail-row">
              <span className="label">时间:</span>
              <span className="content">{currentLog.create_time}</span>
            </div>
            <div className="detail-row">
              <span className="label">类型:</span>
              <span className="content">
                <Tag color={getLogTypeColor(currentLog.log_type)}>
                  {getLogTypeName(currentLog.log_type)}
                </Tag>
              </span>
            </div>
            <div className="detail-row">
              <span className="label">状态:</span>
              <span className="content">
                {currentLog.status === 1 ?
                  <Tag color="success">成功</Tag> :
                  <Tag color="error">失败</Tag>
                }
              </span>
            </div>
            <div className="detail-row">
              <span className="label">模型ID:</span>
              <span className="content">{currentLog.model_id}</span>
            </div>
            <div className="detail-row">
              <span className="label">内容:</span>
              <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                {currentLog.log_content}
              </pre>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default Logs;
