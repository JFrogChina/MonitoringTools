# Project Storage Monitor

## 功能特性
- <strong>Artifactory 项目存储使用率监控工具</strong> - 用于监控 Artifactory 中各个项目的存储使用情况

## 使用方法
1. pip3 install requests (或 pip3 install -r requirements.txt)
2. 执行:
python3 artifactory_project_monitor.py --url ARTIFACTORY_URL --token <YOUR_TOKEN> (如: python3 artifactory_project_monitor.py project1 --url http://artifactory.example.com --token xxx)
