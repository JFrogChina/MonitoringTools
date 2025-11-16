
#!/usr/bin/env python3

"""

Artifactory 项目存储使用率监控工具
用于监控 Artifactory 中各个项目的存储使用情况

1. 安装依赖:
pip3 install requests (或 pip3 install -r requirements.txt)
2. 执行:
python3 artifactory_project_monitor.py --url ARTIFACTORY_URL --token <YOUR_TOKEN> (如: python3 artifactory_project_monitor.py project1 --url http://artifactory.example.com --token xxx)

"""

import requests
import json
import sys
import argparse
from typing import Dict, List, Optional


class ArtifactoryStorageMonitor:
    """Artifactory 存储监控类"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def test_authentication(self) -> bool:
        """测试认证是否有效"""
        test_url = f"{self.base_url}/artifactory/api/system/version"
        try:
            response = requests.get(test_url, headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_projects(self) -> List[Dict]:
        """获取所有项目列表"""
        url = f"{self.base_url}/access/api/v1/projects"
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 401:
                print("认证失败: 令牌无效或已过期")
                print("请检查您的认证信息并重新运行脚本")
                sys.exit(1)
            elif response.status_code == 403:
                print("权限不足: 当前用户没有访问项目的权限")
                sys.exit(1)
            elif response.status_code == 404:
                print("API端点不存在: 请检查Artifactory版本是否支持项目功能")
                sys.exit(1)
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"获取项目列表失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"HTTP状态码: {e.response.status_code}")
                print(f"响应内容: {e.response.text}")
            sys.exit(1)
    
    def get_repositories(self, project_key: str) -> List[Dict]:
        """获取指定项目下的仓库列表"""
        url = f"{self.base_url}/artifactory/api/repositories?type=local&project={project_key}"
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"获取项目 {project_key} 的仓库列表失败: {e}")
            return []
    
    def get_storage_info(self) -> Dict:
        """获取存储信息"""
        url = f"{self.base_url}/artifactory/api/storageinfo"
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"获取存储信息失败: {e}")
            sys.exit(1)
    
    def calculate_project_usage(self, project_key: str, storage_info: Dict) -> Dict:
        """计算项目的存储使用情况"""
        # 从存储信息中筛选出属于该项目的仓库
        project_repos = [
            repo for repo in storage_info.get('repositoriesSummaryList', [])
            if repo.get('projectKey') == project_key and repo.get('repoKey') != 'TOTAL'
        ]
        
        # 计算总使用空间（字节）
        total_used_bytes = sum(repo.get('usedSpaceInBytes', 0) for repo in project_repos)
        
        return {
            'repositories': project_repos,
            'total_used_bytes': total_used_bytes,
            'repo_count': len(project_repos)
        }
    
    def format_size(self, bytes_size: int) -> str:
        """格式化字节大小为易读格式"""
        if bytes_size == 0:
            return "0 B"
            
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"
    
    def get_project_name_color(self, usage_percent: float) -> str:
        """根据使用率返回对应的颜色代码"""
        if usage_percent > 90:
            return "\033[1;31m"  # 红色粗体 (>90%)
        elif usage_percent > 80:
            return "\033[1;33m"  # 黄色粗体 (>80%)
        else:
            return "\033[1;32m"  # 绿色粗体 (<=80%)
    
    def get_display_width(self, text: str) -> int:
        """计算字符串的显示宽度（中文字符算2个宽度，英文字符算1个宽度）"""
        width = 0
        for char in text:
            # 中文字符的Unicode范围
            if '\u4e00' <= char <= '\u9fff':
                width += 2
            else:
                width += 1
        return width
    
    def pad_string(self, text: str, width: int, align: str = '<') -> str:
        """填充字符串到指定显示宽度"""
        current_width = self.get_display_width(text)
        if current_width >= width:
            return text
        
        padding = width - current_width
        if align == '<':
            return text + ' ' * padding
        elif align == '>':
            return ' ' * padding + text
        else:  # '^'
            left_padding = padding // 2
            right_padding = padding - left_padding
            return ' ' * left_padding + text + ' ' * right_padding
    
    def print_project_usage(self, project: Dict, storage_info: Dict, show_details: bool = False):
        """打印项目使用情况"""
        project_key = project['project_key']
        project_name = project['display_name']
        storage_quota = project['storage_quota_bytes']
        
        usage_info = self.calculate_project_usage(project_key, storage_info)
        total_used = usage_info['total_used_bytes']
        repo_count = usage_info['repo_count']
        
        # 计算使用百分比
        if storage_quota > 0:
            usage_percent = (total_used / storage_quota) * 100
            quota_display = self.format_size(storage_quota)
        else:
            usage_percent = 0
            quota_display = "无限制"
        
        # 根据使用率获取颜色
        color_code = self.get_project_name_color(usage_percent)
        reset_code = "\033[0m"
        
        # 统一分隔线长度
        separator_length = 70
        separator_line = '=' * separator_length
        dash_line = '-' * separator_length
        
        print(f"\n{separator_line}")
        # 项目名称根据使用率动态改变颜色
        print(f"项目名称: {color_code}{project_name}{reset_code} ({project_key})")
        print(f"存储限制: {quota_display}")
        print(f"已用空间: {self.format_size(total_used)}")
        print(f"仓库数量: {repo_count}")
        
        if storage_quota > 0:
            print(f"使用比例: {usage_percent:.2f}%")
            # 添加使用情况可视化
            bar_length = 30
            filled_length = int(bar_length * usage_percent / 100)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            print(f"使用情况: [{bar}] {usage_percent:.1f}%")
            
            # 添加预警信息
            if usage_percent > 90:
                print("🔴 警告: 存储使用率超过90%! 请立即处理")
            elif usage_percent > 80:
                print("🟡 注意: 存储使用率超过80%")
        else:
            print(f"使用比例: 无限制")
        
        # 显示详细仓库信息
        if show_details and usage_info['repositories']:
            print(f"\n仓库详情:")
            # 使用自定义宽度计算来对齐中英文混合文本
            header1 = self.pad_string("仓库名称", 25)
            header2 = self.pad_string("类型", 12)
            header3 = self.pad_string("使用空间", 18)
            header4 = self.pad_string("占比", 12)
            print(f"{header1} {header2} {header3} {header4}")
            print(f"{dash_line}")
            
            for repo in usage_info['repositories']:
                repo_used = repo.get('usedSpaceInBytes', 0)
                if storage_quota > 0:
                    repo_percent = (repo_used / storage_quota) * 100
                    percent_display = f"{repo_percent:.2f}%"
                else:
                    percent_display = "N/A"
                
                # 使用自定义宽度填充
                repo_name = self.pad_string(repo['repoKey'], 25)
                repo_type = self.pad_string(repo.get('repoType', 'N/A'), 12)
                repo_size = self.pad_string(self.format_size(repo_used), 18)
                repo_percent_display = self.pad_string(percent_display, 12)
                
                print(f"{repo_name} {repo_type} {repo_size} {repo_percent_display}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Artifactory 项目存储使用率监控工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 查看所有项目
  python3 artifactory_monitor.py --url http://artifactory.example.com --token YOUR_TOKEN

  # 查看特定项目详情
  python3 artifactory_monitor.py project1 --url http://artifactory.example.com --token YOUR_TOKEN --details

  # 查看所有项目并显示详细信息
  python3 artifactory_monitor.py --url http://artifactory.example.com --token YOUR_TOKEN --details

颜色说明:
  🟢 绿色: 使用率 <= 80% (正常)
  🟡 黄色: 使用率 > 80% (警告)
  🔴 红色: 使用率 > 90% (危险)
        """
    )
    
    parser.add_argument('project_name', nargs='?', help='指定项目名称（不指定则显示所有项目）')
    parser.add_argument('--details', '-d', action='store_true', help='显示详细仓库信息')
    
    # 必需参数
    parser.add_argument('--url', required=True, help='Artifactory 地址 (例如: http://artifactory.example.com)')
    parser.add_argument('--token', required=True, help='Bearer Token 认证')
    
    args = parser.parse_args()
    
    # 创建监控实例
    monitor = ArtifactoryStorageMonitor(
        base_url=args.url,
        token=args.token
    )
    
    # 显示连接信息
    print(f"连接至: {args.url}")
    
    # 测试认证
    print("测试认证连接...", end=' ')
    if not monitor.test_authentication():
        print("失败!")
        print("认证失败: 无法连接到Artifactory或认证信息无效")
        print("请检查:")
        print("  1. Artifactory地址是否正确")
        print("  2. Token是否有效")
        print("  3. 网络连接是否正常")
        sys.exit(1)
    print("成功!")
    
    # 获取数据
    print("获取项目信息...", end=' ')
    projects = monitor.get_projects()
    print(f"找到 {len(projects)} 个项目")
    
    print("获取存储信息...", end=' ')
    storage_info = monitor.get_storage_info()
    print("完成")
    
    # 统一分隔线长度
    separator_length = 70
    separator_line = '=' * separator_length
    
    print(f"\nArtifactory 项目存储使用率监控 - {args.url}")
    print(f"{separator_line}")
    
    # 根据参数显示相应项目信息
    if args.project_name:
        # 查找指定项目
        target_project = None
        for project in projects:
            if project['project_key'] == args.project_name or project['display_name'] == args.project_name:
                target_project = project
                break
        
        if target_project:
            monitor.print_project_usage(target_project, storage_info, show_details=True)
        else:
            print(f"错误: 未找到项目 '{args.project_name}'")
            print(f"可用项目: {[p['project_key'] for p in projects]}")
            sys.exit(1)
    else:
        # 显示所有项目
        print(f"项目列表:\n")
        
        for project in projects:
            monitor.print_project_usage(project, storage_info, show_details=args.details)
        
        # 显示汇总信息
        total_quota = sum(p['storage_quota_bytes'] for p in projects if p['storage_quota_bytes'] > 0)
        unlimited_projects = [p for p in projects if p['storage_quota_bytes'] <= 0]
        limited_projects = [p for p in projects if p['storage_quota_bytes'] > 0]
        
        print(f"\n{separator_line}")
        print(f"汇总信息:")
        print(f"总项目数: {len(projects)}")
        print(f"有限制项目: {len(limited_projects)}个")
        print(f"无限制项目: {len(unlimited_projects)}个")
        if total_quota > 0:
            print(f"总存储限制: {monitor.format_size(total_quota)}")


if __name__ == "__main__":
    main()
