# GeoSpyder: 地理逆编码库 | Reverse Geocoding Library

## 概述 | Overview

GeoSpyder是一个灵活的 Python 地理逆编码库，支持多种地理编码服务的可扩展 API。目前实现了百度地图地理编码服务，支持批量处理坐标位置信息。

GeoSpyder is a flexible Python library for reverse geocoding that supports multiple geocoding services with an extensible API. Currently implemented with Baidu Maps geocoding service.

## 特性 | Features

- 🌍 地理逆编码 | Reverse Geocoding
- 📊 批量处理支持 | Batch Processing
- 🔌 可扩展的服务架构 | Extensible Service Architecture
- 📝 JSON 配置支持 | Configurable via JSON
- 🚨 健壮的错误处理 | Robust Error Handling
- 📋 Excel 导入导出支持 | Excel Input/Output Support

## 系统要求 | Requirements

- Python 3.6+
- 依赖包 | Dependencies:

  ```
  requests>=2.25.0,<3.0.0
  pandas>=0.25.0,<1.2.0
  openpyxl>=2.6.0,<3.1.0
  typing>=3.7.4.3
  ```

## 安装 | Installation

```bash
pip install -r requirements.txt
```

## 配置 | Configuration

创建 `config.json` 配置文件，结构如下 | Create a `config.json` file with the following structure:

```json
{
  "api_key": "YOUR_BAIDU_MAPS_API_KEY",
  "input_path": "locations.xlsx",
  "output_path": "geocoding_results.xls",
  "column": 1,
  "request_delay": 0.5
}
```

## 使用方法 | Usage

### 命令行使用 | Command Line Usage

```bash
python geospyder_r.py -c config.json -k YOUR_API_KEY -i input.xlsx -o output.xlsx --column 1 --delay 0.5
```

参数说明 | Parameters:

- `-c, --config`: 配置文件路径 | Config file path
- `-k, --api_key`: 百度地图 API 密钥 | Baidu Maps API key
- `-i, --input`: 输入文件路径 | Input file path
- `-o, --output`: 输出文件路径 | Output file path
- `--column`: 处理的列索引 | Column index to process
- `--delay`: API 请求延迟 (秒) | API request delay in seconds

### 代码调用 | Code Usage

```python
from geospyder_r import GeocodingConfig, BaiduGeocodingService, GeocodingProcessor

# 初始化配置
config = GeocodingConfig('config.json')

# 创建百度地图服务实例
baidu_service = BaiduGeocodingService(config)

# 处理数据
processor = GeocodingProcessor()
for locations_chunk in processor.process_in_chunks('input.xlsx', column=1):
    results = baidu_service.batch_geocode(locations_chunk)
    processor.output_results(results, 'input.xlsx', 'output.xlsx')
```

## 主要类说明 | Core Classes

- `GeocodingConfig`: 配置管理类 | Configuration management
- `AbstractGeocodingService`: 地理编码服务基类 | Base class for geocoding services
- `BaiduGeocodingService`: 百度地图实现 | Baidu Maps implementation
- `GeocodingProcessor`: 文件处理类 | File processing handler

## 日志记录 | Logging

系统使用 Python 的 `logging` 模块，日志文件默认保存在程序目录下的 `log.txt`。

The system uses Python's `logging` module. Logs are saved in `log.txt` in the program directory.

## 错误处理 | Error Handling

- API 错误优雅处理 | Graceful API error handling
- 可配置的请求延迟 | Configurable request delays
- 详细的处理步骤日志 | Detailed processing logs

## 扩展支持 | Extending

添加新的地理编码服务 | To add a new geocoding service:

1. 继承 `AbstractGeocodingService` | Subclass `AbstractGeocodingService`
2. 实现 `get_location_info()` 方法 | Implement `get_location_info()` method
3. 添加服务特定的 API 逻辑 | Add service-specific API logic

## 限制 | Limitations

- 当前仅支持百度地图 API | Currently supports only Baidu Maps API
- 需要有效的 API 密钥 | Requires valid API key
- Excel 文件输入输出 | Excel file I/O only

## 贡献 | Contributing

欢迎提交 Pull Requests 或提出 Issues。

Contributions are welcome! Please submit pull requests or open issues.

## 许可证 | License

MIT License

## 免责声明 | Disclaimer

本库与百度地图官方无关。

This library is not officially affiliated with Baidu Maps.
