# -*- coding: utf-8 -*-
"""
Reverse Geocoding Library with Extensible API Support
"""
import os
import json
import logging
import time
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import argparse

import requests
import pandas as pd

def parse_arguments():
    """命令行参数解析"""
    parser = argparse.ArgumentParser(description='地理编码处理工具')
    
    parser.add_argument('-c', '--config', 
                       type=str, 
                       default='config.json',
                       help='配置文件路径 (默认：config.json)')
    
    parser.add_argument('-k', '--api_key', 
                       type=str,
                       help='Baidu Maps API 密钥 (如配置文件中已设置则忽略)')

    parser.add_argument('-i', '--input', 
                       type=str,
                       help='输入 Excel 文件路径 (如配置文件中已设置则忽略)')
    
    parser.add_argument('-o', '--output',
                       type=str,
                       help='输出 Excel 文件路径 (如配置文件中已设置则忽略)')
    
    parser.add_argument('--column',
                       type=int,
                       help='要处理的列索引，从 0 开始 (如配置文件中已设置则忽略)')
    
    parser.add_argument('--delay',
                       type=float,
                       help='API 请求间隔时间 (秒) (如配置文件中已设置则忽略)')
    
    return parser.parse_args()

class GeocodingConfig:
    """Configuration management for geocoding services"""
    def __init__(self, config_path: str = 'config.json'):
        self.dir_path: str = os.path.dirname(__file__)
         # 支持相对路径和绝对路径
        if not os.path.isabs(config_path):
            config_path = os.path.join(self.dir_path, config_path)
        # 添加配置初始化
        self.config: Dict[str, Any] = {}  # 添加类型提示
        # 先加载配置文件
        self.config = self._load_config(config_path)
        # 然后用命令行参数更新
        args = parse_arguments()
        self.update_from_args(args)
        
        # 添加日志文件路径初始化
        log_filename = 'geocoding.log'
        self.log_file_path = os.path.join(self.dir_path, log_filename)

    def update_from_args(self, args):
        """从命令行参数更新配置（仅当配置文件中未设置时）"""
        # 只在配置文件中没有相应设置时，才使用命令行参数
        if args.api_key and ('api_key' not in self.config or self.config['api_key'] in (None, '')):
            self.config['api_key'] = args.api_key
            logging.info("使用命令行参数设置的 API 密钥")
        
        if args.input and ('input_path' not in self.config or self.config['input_path'] in (None, '')):
            self.config['input_path'] = args.input
            logging.info("使用命令行参数设置的输入路径")
            
        if args.output and ('output_path' not in self.config or self.config['output_path'] in (None, '')):
            self.config['output_path'] = args.output
            logging.info("使用命令行参数设置的输出路径")
            
        if args.column is not None and ('column' not in self.config or self.config['column'] in (None, '')):
            self.config['column'] = args.column
            logging.info("使用命令行参数设置的列索引")
            
        if args.delay is not None and 'request_delay' not in self.config:
            self.config['request_delay'] = args.delay
            logging.info("使用命令行参数设置的请求延迟")
        else:
            # 如果既没有配置文件也没有命令行参数设置延迟，则使用默认值
            if ('request_delay' not in self.config or self.config['request_delay'] in (None, '')):
                self.config['request_delay'] = 0.5

    def _load_config(self, config_path):
        # 如果配置文件不存在，返回空配置，后续由命令行参数填充
        if not config_path or not os.path.exists(config_path):
            logging.warning(f"Warning: Config file {config_path} not found.")
            return {}
        
        try:
            # 使用标准 json 读取
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.warning(f"Error decoding JSON from {config_path}.")
            return {}

class AbstractGeocodingService(ABC):
    """Abstract base class for geocoding services"""
    
    def __init__(self, config: GeocodingConfig):
        self.config = config
        self.dir_path = config.dir_path
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_location_info(self, location: str) -> Dict[str, str]:
        """Abstract method to get location information"""
        pass

    def batch_geocode(self, locations: List[str]) -> List[Dict[str, str]]:
        """Batch geocoding with error handling and logging"""
        results = []
        for location in locations:
            try:
                result = self.get_location_info(location)
                results.append(result)
                self.logger.info(f"Successfully processed {location}")
            except Exception as e:
                self.logger.error(f"Error processing {location}: {e}")
                results.append(self._get_error_result(location))
            time.sleep(self.config.config.get('request_delay', 0.5))
        return results

    def _get_error_result(self, location: str) -> Dict[str, str]:
        """Generate a default error result"""
        return {
            'origin': location,
            'formatted_address': '',
            'town': '',
            'street': '',
            'status': 'error'
        }

class BaiduGeocodingService(AbstractGeocodingService):
    """Baidu Maps Geocoding Service Implementation"""

    def get_location_info(self, location: str) -> Dict[str, str]:
        """Get location information from Baidu Maps API"""
        url = (f"https://api.map.baidu.com/reverse_geocoding/v3/"
               f"?location={location}&output=json&ak={self.config.config['api_key']}")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # 检查 HTTP 错误
            
            data = response.json()
            if data["status"] == 0:
                result = data.get("result", {})
                address_component = result.get("addressComponent", {})
                return {
                    'origin': location,
                    'formatted_address': result.get("formatted_address", ''),
                    'town': address_component.get("town", ''),
                    'street': address_component.get("street", ''),
                    'status': 'success'
                }
            else:
                self.logger.warning(f"百度 API 返回错误状态码：{data['status']}, 错误信息：{data.get('message', 'unknown')}")
                
        except requests.Timeout:
            self.logger.error(f"请求超时：{location}")
            
        except requests.RequestException as e:
            self.logger.error(f"网络请求错误：{location}, 错误：{str(e)}")
            
        except (KeyError, TypeError, json.JSONDecodeError) as e:
            self.logger.error(f"解析响应数据错误：{location}, 错误：{str(e)}")
            
        except Exception as e:
            self.logger.error(f"未预期的错误：{location}, 错误：{str(e)}")
    
class GeocodingProcessor:
    """Main processing class for geocoding operations"""

    @staticmethod
    def process_in_chunks(file_path: str, column: int = 1, chunk_size: int = 1000):
        """Generator function to process data in chunks"""
        try:
            # 一次性读取 Excel 文件
            if '.xlsx' in file_path:    
                df = pd.read_excel(file_path, usecols=[column], engine='openpyxl')
            else:
                df = pd.read_excel(file_path, usecols=[column])
            
            # 手动分块处理
            total_rows = len(df)
            for start_idx in range(0, total_rows, chunk_size):
                end_idx = min(start_idx + chunk_size, total_rows)
                yield df.iloc[start_idx:end_idx, 0].tolist()
                
        except Exception as e:
            logging.error(f"读取文件错误：{e}")
            yield []

    @staticmethod
    def output_results(results: List[Dict[str, str]], input_path: str, output_path: str):
        """Output results to Excel"""
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logging.info(f"创建输出目录：{output_dir}")

            # 读取原始文件
            if '.xlsx' in input_path:
                df_input = pd.read_excel(input_path, engine='openpyxl')
            else:
                df_input = pd.read_excel(input_path)

            # 创建结果 DataFrame
            df_results = pd.DataFrame(results)

            # 合并原始数据和地理编码结果
            df_combined = pd.concat([
                df_input.reset_index(drop=True), 
                df_results.reset_index(drop=True)
            ], axis=1)

            # 保存结果
            if '.xlsx' in output_path:
                df_combined.to_excel(output_path, index=False, engine='openpyxl')
            else:
                df_combined.to_excel(output_path, index=False)

            logging.info(f"结果已保存到 {output_path}")

        except Exception as e:
            logging.error(f"保存结果时发生错误：{e}")

def main():
    # 1. 创建配置对象
    config = GeocodingConfig('config.json')  # 可以传入自定义配置文件路径

    # 重置之前的日志处理器
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # 配置日志记录，使用 config.log_file_path
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.log_file_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # 创建 logger 实例
    logger = logging.getLogger(__name__)
    # 记录启动信息
    logger.info("地址逆编码处理程序启动")

    # 验证必要的配置
    if not config.config.get('api_key'):
        logger.error("未设置 API 密钥。请在配置文件中设置 api_key")
        return
    
    if not config.config.get('input_path'):
        logger.error("未指定输入文件路径。使用 -i 或在配置文件中设置 input_path")
        return
    
    if config.config.get('column') is None:
        logger.error("未指定处理列索引。使用 --column 或在配置文件中设置 column")
        return


    # 2. 创建百度地理编码服务实例
    baidu_service = BaiduGeocodingService(config)

    # 3. 读取位置数据
    file_path = config.config.get("input_path")
    column = config.config.get("column")
    if not file_path or not os.path.exists(file_path):
       logger.error("Input file path is invalid or does not exist.")
       return
    if column is None:
       logger.error("Column index is not specified in the configuration.")
       return
    # 4. 分块处理数据
    chunk_size = 1000  # 可以通过配置文件设置
    all_results = []
    for locations_chunk in GeocodingProcessor.process_in_chunks(
        file_path,
        column,
        chunk_size
    ):
        # 处理每个数据块，批量地理编码
        chunk_results = baidu_service.batch_geocode(locations_chunk)
        all_results.extend(chunk_results)
        
        # 输出进度
        logger.info(f"Processed {len(all_results)} locations so far...")

    # 5. 输出结果
    output_path = config.config.get('output_path', 'reverse_geocoding_result.xls')
    GeocodingProcessor.output_results(results = all_results, 
                                    input_path = file_path, 
                                    output_path = output_path)

    # 6. 记录处理摘要
    print(f"Total locations processed: {len(all_results)}")
    print(f"Successful geocoding: {sum(1 for r in all_results if r['formatted_address'])}")
    logger.info(f"Total locations processed: {len(all_results)}")
    logger.info(f"Successful geocoding: {sum(1 for r in all_results if r['formatted_address'])}")

if __name__ == '__main__':
    main()
