"""
爬虫使用示例
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from crawlers import CrawlerManager, CrawlerConfig


def main():
    """主函数"""
    # 初始化配置和管理器
    config = CrawlerConfig()
    manager = CrawlerManager(config)
    
    print("=" * 50)
    print("爬虫管理系统")
    print("=" * 50)
    print()
    
    while True:
        print("\n请选择操作：")
        print("1. 运行所有爬虫")
        print("2. 运行AI技术信息爬虫")
        print("3. 运行股市信息爬虫")
        print("4. 运行指定爬虫")
        print("5. 查看爬虫状态")
        print("6. 启动定时调度器")
        print("0. 退出")
        
        choice = input("\n请输入选项: ").strip()
        
        if choice == '1':
            print("\n开始运行所有爬虫...")
            results = manager.run_all()
            print(f"\n完成！共获取 {sum(len(items) for items in results.values())} 条数据")
            for name, items in results.items():
                print(f"  {name}: {len(items)} 条")
        
        elif choice == '2':
            print("\n开始运行AI技术信息爬虫...")
            results = manager.run_ai_crawlers()
            print(f"\n完成！共获取 {sum(len(items) for items in results.values())} 条数据")
            for name, items in results.items():
                print(f"  {name}: {len(items)} 条")
        
        elif choice == '3':
            print("\n开始运行股市信息爬虫...")
            results = manager.run_stock_crawlers()
            print(f"\n完成！共获取 {sum(len(items) for items in results.values())} 条数据")
            for name, items in results.items():
                print(f"  {name}: {len(items)} 条")
        
        elif choice == '4':
            print("\n可用爬虫列表：")
            for i, name in enumerate(manager.crawlers.keys(), 1):
                print(f"  {i}. {name}")
            
            crawler_name = input("\n请输入爬虫名称: ").strip()
            if crawler_name in manager.crawlers:
                print(f"\n开始运行爬虫: {crawler_name}")
                items = manager.run_crawler(crawler_name)
                print(f"完成！获取 {len(items)} 条数据")
            else:
                print("爬虫不存在！")
        
        elif choice == '5':
            print("\n爬虫状态：")
            status = manager.get_status()
            for name, info in status.items():
                print(f"\n{name}:")
                print(f"  启用: {info['enabled']}")
                print(f"  频率: {info['frequency']}")
                print(f"  上次运行: {info['last_run']}")
                print(f"  统计: {info['stats']}")
        
        elif choice == '6':
            print("\n启动定时调度器...")
            print("按 Ctrl+C 停止")
            try:
                manager.start_scheduler(interval=60)  # 每分钟检查一次
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n停止调度器...")
                manager.stop()
        
        elif choice == '0':
            print("\n退出程序")
            manager.stop()
            break
        
        else:
            print("无效选项！")


if __name__ == '__main__':
    main()
