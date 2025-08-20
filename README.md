# More-Nametag - MCDR 玩家称号插件

# 

# !https://img.shields.io/badge/MCDR-2.14.7+-blue

# !https://img.shields.io/badge/license-MIT-green

# 

# 一个为 Minecraft 服务器提供自定义玩家称号功能的 MCDR (MCDReforged) 插件

# 

# 🚀 功能特性

# 

# • 支持自定义玩家称号

# 

# • 丰富的颜色代码支持

# 

# • 渐变文字效果

# 

# • 多预设配置

# 

# • 称号长度限制

# 

# • 玩家加入自动加载

# 

# 📦 安装指南

# 

# 基础安装

# 

# 1\. 下载最新版本插件

# 2\. 将插件文件放入 plugins/ 目录

# 3\. 重启 MCDR 服务器

# 

# 配置文件

# 

# 在 config/more\_nametag.json 创建配置文件，内容如下：

# {

# &nbsp; "allowed\_colors": \["red", "blue", "green", "gradient"],

# &nbsp; "max\_length": 16,

# &nbsp; "enable\_gradient": true,

# &nbsp; "gradient\_preset": "rainbow"

# }

# 

# 

# 🎮 使用教程

# 

# 基础命令

# 

# 命令 描述 示例

# 

# !!nametag set <内容> 设置玩家称号 !!nametag set \&g酷炫称号

# 

# !!nametag color <颜色> 设置称号颜色 !!nametag color red

# 

# !!nametag preset <预设> 设置渐变预设 !!nametag preset rainbow

# 

# !!nametag preview 预览称号效果 !!nametag preview

# 

# 特殊语法

# 

# • 使用 \&g 开头自动应用渐变效果

# 

# • 颜色代码支持：red, blue, green 等

# 

# ⚙️ 配置说明

# 

# 配置项 类型 默认值 说明

# 

# allowed\_colors 数组 \["red", "blue", "green", "gradient"] 允许使用的颜色

# 

# max\_length 整数 16 称号最大长度

# 

# enable\_gradient 布尔 true 是否启用渐变效果

# 

# gradient\_preset 字符串 "rainbow" 默认渐变预设

# 🌈 渐变预设

# 预设名 效果示例

# 

# rainbow 彩虹渐变

# 

# fire 火焰效果

# 

# ice 冰霜效果

# 

# nature 自然色系

# 

# 📜 开发计划

# 添加更多渐变预设

# 

# 支持称号粒子效果

# 

# 添加称号权限系统

# 

# 🤝 贡献指南

# 

# 欢迎提交 Issue 或 Pull Request！

# 

# 1\. Fork 项目

# 2\. 创建分支 (git checkout -b feature/AmazingFeature)

# 3\. 提交更改 (git commit -m 'Add some AmazingFeature')

# 4\. 推送分支 (git push origin feature/AmazingFeature)

# 5\. 打开 Pull Request

# 

# 📄 许可证

# 

# 本项目采用 MIT 许可证 - 详情参见 LICENSE 文件

# 

# 📧 如有问题请联系：your.email@example.com  

# 🌐 项目地址：https://github.com/yourname/more-nametag

