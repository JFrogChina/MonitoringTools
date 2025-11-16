# Project Storage Monitor

## 功能特性
- <strong>Artifactory 项目存储使用率监控工具</strong> - 用于监控 Artifactory 中各个项目的存储使用情况

## 使用方法
### 依赖安装
```bash
pip3 install -r requirements.txt
```
### 基本使用
```bash
python3 project_storage_monitor.py --url ARTIFACTORY_URL --token <YOUR_TOKEN>
```

## 命令行参数

## 输出示例
```
$ python3 project_storage_monitor.py --url http://localhost:8082 --token xxx --details
连接至: http://localhost:8082
测试认证连接... 成功!
获取项目信息... 找到 2 个项目
获取存储信息... 完成

Artifactory 项目存储使用率监控 - http://localhost:8082
======================================================================
项目列表:


======================================================================
项目名称: project2 (project2)
存储限制: 2.00 GB
已用空间: 1.76 GB
仓库数量: 3
使用比例: 87.89%
使用情况: [██████████████████████████░░░░] 87.9%
🟡 注意: 存储使用率超过80%

仓库详情:
仓库名称                  类型         使用空间           占比        
----------------------------------------------------------------------
project2-generic-local2   LOCAL        0 B                0.00%       
project2-generic-local1   LOCAL        1.76 GB            87.89%      
project2-build-info       LOCAL        0 B                0.00%       

======================================================================
项目名称: project1 (project1)
存储限制: 1.00 GB
已用空间: 479.68 MB
仓库数量: 3
使用比例: 46.84%
使用情况: [██████████████░░░░░░░░░░░░░░░░] 46.8%

仓库详情:
仓库名称                  类型         使用空间           占比        
----------------------------------------------------------------------
project1-test             LOCAL        206.64 MB          20.18%      
project1-build-info       LOCAL        0 B                0.00%       
project1-test2            LOCAL        273.04 MB          26.66%      

======================================================================
汇总信息:
总项目数: 2
有限制项目: 2个
无限制项目: 0个
总存储限制: 3.00 GB
```
