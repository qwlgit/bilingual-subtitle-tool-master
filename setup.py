"""
智能语音识别翻译系统安装脚本
Setup script for Intelligent Speech Recognition and Translation System
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# 读取requirements文件
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# 读取版本信息
def get_version():
    version_file = os.path.join("src", "__init__.py")
    with open(version_file, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "2.0.0"

setup(
    name="bilingual-subtitle-tool",
    version=get_version(),
    author="Bilingual Subtitle Tool Team",
    author_email="support@bilingual-subtitle-tool.com",
    description="智能语音识别翻译系统 - 实时双语字幕显示工具",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/bilingual-subtitle-tool/bilingual-subtitle-tool",
    project_urls={
        "Bug Tracker": "https://github.com/bilingual-subtitle-tool/bilingual-subtitle-tool/issues",
        "Documentation": "https://github.com/bilingual-subtitle-tool/bilingual-subtitle-tool/wiki",
        "Source Code": "https://github.com/bilingual-subtitle-tool/bilingual-subtitle-tool",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
        "Natural Language :: Chinese (Simplified)",
        "Natural Language :: English",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.900",
            "pre-commit>=2.0",
        ],
        "audio": [
            "PyAudioWPatch>=0.2.12",
            "resampy>=0.4.0",
            "numpy>=1.21.0",
        ],
        "gui": [
            "PyQt5>=5.15.0",
        ],
        "translation": [
            "requests>=2.25.0",
        ],
        "websocket": [
            "websockets>=10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bilingual-subtitle=src.main:main",
            "subtitle-tool=src.main:main",
        ],
        "gui_scripts": [
            "bilingual-subtitle-gui=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src": [
            "config/*.json",
            "ui/assets/*",
            "utils/templates/*",
        ],
    },
    data_files=[
        ("docs", [
            "docs/ARCHITECTURE.md",
            "docs/API.md", 
            "docs/USER_GUIDE.md",
            "docs/REFACTOR_GUIDE.md"
        ]),
    ],
    keywords=[
        "speech recognition",
        "translation", 
        "subtitle",
        "bilingual",
        "real-time",
        "PyQt5",
        "audio processing",
        "Chinese",
        "English",
        "GUI application"
    ],
    license="MIT",
    zip_safe=False,
    platforms=["Windows", "macOS", "Linux"],
    
    # 元数据
    maintainer="Bilingual Subtitle Tool Team",
    maintainer_email="maintainer@bilingual-subtitle-tool.com",
    download_url="https://github.com/bilingual-subtitle-tool/bilingual-subtitle-tool/releases",
    
    # 项目状态
    options={
        "bdist_wheel": {
            "universal": False,
        }
    },
)

# 安装后钩子
def post_install():
    """安装后执行的操作"""
    print("=" * 60)
    print("🎉 智能语音识别翻译系统安装完成！")
    print("=" * 60)
    print()
    print("📖 快速开始:")
    print("   bilingual-subtitle --help")
    print("   或")
    print("   python -m src.main")
    print()
    print("📚 文档:")
    print("   - 用户指南: docs/USER_GUIDE.md")
    print("   - API文档: docs/API.md")
    print("   - 架构文档: docs/ARCHITECTURE.md")
    print()
    print("🔧 依赖检查:")
    print("   - PyQt5: GUI界面支持")
    print("   - PyAudio: 音频处理支持")
    print("   - websockets: WebSocket通信支持")
    print("   - requests: HTTP请求支持")
    print()
    print("💡 提示:")
    print("   如果遇到音频设备问题，请参考用户指南的故障排除部分")
    print("   如果需要系统音频录制，建议安装 PyAudioWPatch")
    print()
    print("🎯 示例:")
    print("   # 基本使用")
    print("   bilingual-subtitle")
    print()
    print("   # 指定音频源")
    print("   bilingual-subtitle --audio_source system_audio")
    print()
    print("   # 指定翻译API")
    print("   bilingual-subtitle --translate_api http://localhost:8000/translate")
    print()
    print("📞 获取帮助:")
    print("   - GitHub: https://github.com/bilingual-subtitle-tool/bilingual-subtitle-tool")
    print("   - Issues: https://github.com/bilingual-subtitle-tool/bilingual-subtitle-tool/issues")
    print()
    print("谢谢使用！🚀")
    print("=" * 60)

if __name__ == "__main__":
    post_install()