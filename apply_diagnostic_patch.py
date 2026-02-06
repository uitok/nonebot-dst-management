#!/usr/bin/env python3
"""
应用 AI 诊断模式增强补丁

这个脚本会自动修改 mod_parser.py 和测试文件，实现诊断模式。
"""

import re


def patch_mod_parser():
    """补丁 mod_parser.py 文件"""
    file_path = "nonebot_plugin_dst_management/ai/mod_parser.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 修改 _build_ai_report 方法签名
    old_build_ai_report = """    def _build_ai_report(self, response: str, parsed: ParsedModConfig) -> Tuple[str, str]:
        data = self._extract_json(response)
        if not isinstance(data, dict):
            raise ValueError("AI 响应格式错误")

        status = data.get("status") or "warn"
        warnings = data.get("warnings") or []
        suggestions = data.get("suggestions") or []
        optimized = data.get("optimized_config")
        if not isinstance(optimized, str):
            optimized = self._build_optimized_config(parsed.mods)

        report = self._render_report(
            status=str(status),
            parsed=parsed,
            warnings=warnings,
            suggestions=suggestions,
            optimized=optimized,
            ai_error=None,
        )
        return report, optimized"""

    new_build_ai_report = """    def _build_ai_report(
        self,
        response: str,
        parsed: ParsedModConfig,
    ) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]], str, str]:
        data = self._extract_json(response)
        if not isinstance(data, dict):
            raise ValueError("AI 响应格式错误")

        status = self._normalize_status(data.get("status"))
        optimized = data.get("optimized_config")
        if not isinstance(optimized, str):
            optimized = self._build_optimized_config(parsed.mods)

        if "issues" in data or "summary" in data:
            issues = self._normalize_issues(data.get("issues"))
            summary = self._build_summary(parsed, issues, data.get("summary"))
        else:
            warnings = data.get("warnings") or []
            suggestions = data.get("suggestions") or []
            issues = self._convert_legacy_issues(warnings, suggestions)
            summary = self._build_summary(parsed, issues, None)

        report = self._render_report(
            status=status,
            parsed=parsed,
            summary=summary,
            issues=issues,
            optimized=optimized,
            ai_error=None,
        )
        return status, summary, issues, report, optimized"""
    
    content = content.replace(old_build_ai_report, new_build_ai_report)
    
    # 2. 修改 _build_fallback_report 方法签名
    old_build_fallback = """    def _build_fallback_report(
        self,
        room_id: int,
        world_id: str,
        parsed: ParsedModConfig,
        error: Exception,
    ) -> Tuple[str, str]:
        suggestions = [
            "检查配置是否包含无效字段",
            "减少不必要的模组选项以提升稳定性",
            "保持配置文件格式统一",
        ]
        optimized = self._build_optimized_config(parsed.mods)
        report = self._render_report(
            status="warn" if parsed.warnings else "valid",
            parsed=parsed,
            warnings=[],
            suggestions=suggestions,
            optimized=optimized,
            ai_error=error,
        )
        return report, optimized"""

    new_build_fallback = """    def _build_fallback_report(
        self,
        room_id: int,
        world_id: str,
        parsed: ParsedModConfig,
        error: Exception,
    ) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]], str, str]:
        suggestions = [
            "检查配置是否包含无效字段",
            "减少不必要的模组选项以提升稳定性",
            "保持配置文件格式统一",
        ]
        issues = self._convert_legacy_issues([], suggestions)
        optimized = self._build_optimized_config(parsed.mods)
        status = "warn" if parsed.warnings else "valid"
        summary = self._build_summary(parsed, issues, None)
        report = self._render_report(
            status=status,
            parsed=parsed,
            summary=summary,
            issues=issues,
            optimized=optimized,
            ai_error=error,
        )
        return status, summary, issues, report, optimized"""
    
    content = content.replace(old_build_fallback, new_build_fallback)
    
    # 3. 修改 _render_report 方法
    old_render_report = """    def _render_report(
        self,
        status: str,
        parsed: ParsedModConfig,
        warnings: List[Dict[str, Any]],
        suggestions: List[Any],
        optimized: str,
        ai_error: Optional[Exception],
    ) -> str:
        status_label = {
            "valid": "✅ 有效",
            "warn": "⚠️ 警告",
            "error": "❌ 错误",
        }.get(status, "⚠️ 警告")

        lines = ["📄 模组配置解析报告", "", "🔍 解析结果："]
        lines.append(f"- 状态：{status_label}")
        lines.append(f"- 已配置模组：{parsed.mod_count} 个")
        lines.append(f"- 总配置项：{parsed.option_count} 个")

        if parsed.warnings:
            lines.append("")
            lines.append("⚠️ 解析警告：")
            for item in parsed.warnings:
                lines.append(f"- {item}")

        if warnings:
            lines.append("")
            lines.append("⚠️ 配置警告：")
            for idx, warn in enumerate(warnings, 1):
                mod_id = warn.get("mod_id") if isinstance(warn, dict) else "未知模组"
                issue = warn.get("issue") if isinstance(warn, dict) else str(warn)
                suggestion = warn.get("suggestion") if isinstance(warn, dict) else ""
                lines.append(f"{idx}. [{mod_id}] {issue}")
                if suggestion:
                    lines.append(f"   💡 {suggestion}")

        if suggestions:
            lines.append("")
            lines.append("💡 优化建议：")
            for idx, item in enumerate(suggestions, 1):
                lines.append(f"{idx}. {item}")

        lines.append("")
        lines.append("📋 优化后的配置：")
        lines.append("```lua")
        lines.append(optimized)
        lines.append("```")

        if ai_error is not None:
            lines.append("")
            if isinstance(ai_error, AIError):
                lines.append(f"⚠️ AI 分析失败：{format_ai_error(ai_error)}")
            else:
                lines.append(f"⚠️ AI 分析失败：{ai_error}")

        return "\\n".join(lines)"""

    new_render_report = """    def _render_report(
        self,
        status: str,
        parsed: ParsedModConfig,
        summary: Dict[str, Any],
        issues: List[Dict[str, Any]],
        optimized: str,
        ai_error: Optional[Exception],
    ) -> str:
        status_label = {
            "valid": "✅ 有效",
            "warn": "⚠️ 有问题需关注",
            "error": "❌ 错误",
        }.get(status, "⚠️ 警告")

        lines = ["📄 模组配置诊断报告", "", "🔍 配置概览："]
        lines.append(f"- 状态：{status_label}")
        lines.append(f"- 已配置模组：{summary.get('mod_count', parsed.mod_count)} 个")
        lines.append(f"- 总配置项：{parsed.option_count} 个")
        lines.append(f"- 问题数量：{summary.get('issue_count', len(issues))} 个")
        lines.append(f"- 严重问题：{summary.get('critical_count', 0)} 个")
        lines.append(f"- 建议项：{summary.get('suggestion_count', 0)} 个")

        if parsed.warnings:
            lines.append("")
            lines.append("⚠️ 解析警告：")
            for item in parsed.warnings:
                lines.append(f"- {item}")

        grouped = {"critical": [], "warning": [], "info": []}
        for issue in issues:
            level = self._normalize_issue_level(issue.get("level"))
            issue["level"] = level
            grouped[level].append(issue)

        if any(grouped.values()):
            lines.append("")
            lines.append("❌ 发现的问题：")
            level_titles = {
                "critical": "❌ 严重问题",
                "warning": "⚠️ 警告问题",
                "info": "ℹ️ 建议优化",
            }
            for level in ("critical", "warning", "info"):
                items = grouped[level]
                if not items:
                    continue
                lines.append("")
                lines.append(level_titles[level])
                for idx, issue in enumerate(items, 1):
                    mod_name = issue.get("mod_name") or issue.get("mod_id") or "未知模组"
                    title = issue.get("title") or issue.get("issue_type") or "配置问题"
                    description = issue.get("description") or "未提供"
                    impact = issue.get("impact") or "未提供"
                    current_value = self._format_issue_value(issue.get("current_value"))
                    suggested_value = self._format_issue_value(issue.get("suggested_value"))
                    reason = issue.get("reason") or "未提供"
                    config_path = issue.get("config_path") or ""
                    lines.append(f"{idx}. 【{mod_name}】{title}")
                    lines.append(f"   - 描述：{description}")
                    lines.append(f"   - 影响：{impact}")
                    lines.append(f"   - 当前值：{current_value}")
                    lines.append(f"   - 建议值：{suggested_value}")
                    lines.append(f"   - 修改理由：{reason}")
                    if config_path:
                        lines.append(f"   - 配置路径：{config_path}")
        else:
            lines.append("")
            lines.append("✅ 未发现明显问题")

        lines.append("")
        lines.append("📋 优化后的配置：")
        lines.append("```lua")
        lines.append(optimized)
        lines.append("```")

        lines.append("")
        lines.append("🚀 如何应用配置：")
        lines.append("- 使用 /dst mod config save <房间ID> <世界ID> --optimized 保存优化配置")
        lines.append("- 应用后请重启房间以生效")

        if ai_error is not None:
            lines.append("")
            if isinstance(ai_error, AIError):
                lines.append(f"⚠️ AI 分析失败：{format_ai_error(ai_error)}")
            else:
                lines.append(f"⚠️ AI 分析失败：{ai_error}")

        return "\\n".join(lines)"""
    
    content = content.replace(old_render_report, new_render_report)
    
    # 4. 添加新的辅助方法到文件末尾（在最后一个方法之后）
    new_methods = '''
    def _normalize_status(self, value: Any) -> str:
        text = str(value or "").strip().lower()
        if text in ("valid", "ok", "success"):
            return "valid"
        if text in ("error", "fail", "failed", "critical"):
            return "error"
        if text in ("warn", "warning", "warnings"):
            return "warn"
        return "warn"

    def _normalize_issue_level(self, value: Any) -> str:
        text = str(value or "").strip().lower()
        if text in ("critical", "error", "high", "severe"):
            return "critical"
        if text in ("warn", "warning", "medium"):
            return "warning"
        if text in ("info", "low", "suggestion", "hint"):
            return "info"
        return "warning"

    def _normalize_issues(self, value: Any) -> List[Dict[str, Any]]:
        if not isinstance(value, list):
            return []
        issues: List[Dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                issues.append(
                    {
                        "level": "warning",
                        "mod_id": "",
                        "mod_name": "",
                        "issue_type": "other",
                        "title": str(item),
                        "description": "",
                        "impact": "",
                        "current_value": None,
                        "suggested_value": None,
                        "reason": "",
                        "config_path": "",
                    }
                )
                continue
            issues.append(
                {
                    "level": item.get("level") or "warning",
                    "mod_id": str(item.get("mod_id") or ""),
                    "mod_name": str(item.get("mod_name") or ""),
                    "issue_type": str(item.get("issue_type") or "other"),
                    "title": str(item.get("title") or ""),
                    "description": str(item.get("description") or ""),
                    "impact": str(item.get("impact") or ""),
                    "current_value": item.get("current_value"),
                    "suggested_value": item.get("suggested_value"),
                    "reason": str(item.get("reason") or ""),
                    "config_path": str(item.get("config_path") or ""),
                }
            )
        return issues

    def _build_summary(
        self,
        parsed: ParsedModConfig,
        issues: List[Dict[str, Any]],
        summary: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        critical_count = sum(
            1 for issue in issues if self._normalize_issue_level(issue.get("level")) == "critical"
        )
        suggestion_count = sum(
            1
            for issue in issues
            if issue.get("suggested_value") not in (None, "")
            or self._normalize_issue_level(issue.get("level")) == "info"
        )
        result = {
            "mod_count": parsed.mod_count,
            "issue_count": len(issues),
            "critical_count": critical_count,
            "suggestion_count": suggestion_count,
        }
        if isinstance(summary, dict):
            for key in result:
                value = summary.get(key)
                if isinstance(value, int):
                    result[key] = value
        return result

    def _convert_legacy_issues(
        self,
        warnings: List[Any],
        suggestions: List[Any],
    ) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        for warn in warnings:
            if isinstance(warn, dict):
                mod_id = warn.get("mod_id") or ""
                title = warn.get("issue") or warn.get("title") or "配置问题"
                suggestion = warn.get("suggestion") or ""
            else:
                mod_id = ""
                title = str(warn)
                suggestion = ""
            issues.append(
                {
                    "level": "warning",
                    "mod_id": str(mod_id),
                    "mod_name": "",
                    "issue_type": "other",
                    "title": str(title),
                    "description": "",
                    "impact": "",
                    "current_value": None,
                    "suggested_value": suggestion or None,
                    "reason": "",
                    "config_path": "",
                }
            )
        for suggestion in suggestions:
            issues.append(
                {
                    "level": "info",
                    "mod_id": "",
                    "mod_name": "",
                    "issue_type": "suggestion",
                    "title": str(suggestion),
                    "description": "",
                    "impact": "",
                    "current_value": None,
                    "suggested_value": None,
                    "reason": "",
                    "config_path": "",
                }
            )
        return issues

    def _format_issue_value(self, value: Any) -> str:
        if value is None:
            return "未提供"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        return str(value)
'''
    
    # 在文件末尾添加新方法（在最后一个 } 之后）
    content = content.rstrip() + '\n' + new_methods + '\n'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ mod_parser.py 补丁应用成功")


def patch_tests():
    """补丁测试文件"""
    file_path = "tests/test_ai_mod_parser.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改测试断言
    content = content.replace(
        'assert "模组配置解析报告" in result["report"]',
        'assert "模组配置诊断报告" in result["report"]'
    )
    
    content = content.replace(
        """    response = json.dumps(
        {
            "status": "valid",
            "warnings": [],
            "suggestions": ["ok"],
            "optimized_config": mod_content.strip(),
        }
    )""",
        """    response = json.dumps(
        {
            "status": "warn",
            "summary": {
                "mod_count": 1,
                "issue_count": 1,
                "critical_count": 0,
                "suggestion_count": 1,
            },
            "issues": [
                {
                    "level": "warning",
                    "mod_id": "workshop-123",
                    "mod_name": "测试模组",
                    "issue_type": "missing",
                    "title": "缺少关键配置项",
                    "description": "缺少 show_max",
                    "impact": "血量显示不完整",
                    "current_value": None,
                    "suggested_value": True,
                    "reason": "需要显示最大血量",
                    "config_path": "configuration_options.show_max",
                }
            ],
            "optimized_config": mod_content.strip(),
        }
    )"""
    )
    
    # 添加新的测试断言
    old_assertions = '''    assert "workshop-123" in result["report"]
    assert "optimized_config" in result'''
    
    new_assertions = '''    assert "workshop-123" in result["report"]
    assert "optimized_config" in result
    assert result["status"] in ("warn", "valid", "error")
    assert "summary" in result
    assert "issues" in result'''
    
    content = content.replace(old_assertions, new_assertions)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ test_ai_mod_parser.py 补丁应用成功")


if __name__ == "__main__":
    print("开始应用 AI 诊断模式增强补丁...")
    patch_mod_parser()
    patch_tests()
    print("\n🎉 所有补丁应用完成！")
    print("\n运行测试：pytest -v tests/test_ai_mod_parser.py")
