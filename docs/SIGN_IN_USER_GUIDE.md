# 签到系统使用指南

## 功能介绍

签到系统用于绑定 DST 玩家账号并完成每日签到，系统将根据连续签到天数与特殊规则发放奖励。
若玩家不在线，奖励会进入待发放状态，并在玩家上线后自动补发。

## 绑定教程

1. 获取自己的 KU_ID（游戏内玩家 ID，一般以 `KU_` 开头）。
2. 执行绑定命令：

```bash
/dst sign bind <KU_ID> [房间ID]
```

示例：

```bash
/dst sign bind KU_ABCDEFG 2
```

说明：
- 若设置了默认房间，可省略房间 ID。
- 同一 QQ 号在同一房间只能绑定一次。

## 签到命令说明

```bash
/dst sign [房间ID]
```

- 签到成功会返回奖励详情、连续签到天数与累计签到天数。
- 当天重复签到会提示已签到。
- 若玩家不在线，奖励会暂存，待上线时补发。

## 奖励规则

奖励由以下部分组成：

1. 等级奖励（根据连续签到天数）
2. 连续签到额外奖励（3/7/30 天）
3. 特殊奖励（首次签到、满月签到）

默认奖励配置（若未配置自定义奖励）：

- 连续 0 天：
  - goldnugget x10
  - cookedmeat x5
- 连续 3 天：
  - goldnugget x20
  - cookedmeat x10
  - cutgrass x20
- 连续 7 天：
  - goldnugget x30
  - nightmare_timepiece x2
  - gears x1
- 连续 14 天：
  - goldnugget x50
  - nightmare_timepiece x5
  - redgem x1
- 连续 30 天：
  - goldnugget x100
  - nightmare_timepiece x10
  - redgem x2

连续签到额外奖励：
- 连续 3 天：goldnugget x20
- 连续 7 天：nightmare_timepiece x1
- 连续 30 天：redgem x1

特殊奖励：
- 首次签到：hammer x1
- 满月签到：blueprint x3

## 常见问题

**Q: 签到后提示奖励未发放怎么办？**

A: 玩家不在线或发放失败时会进入待发放状态。请确保上线后再次触发检查（如执行 `/dst sign`、`/dst info`、`/dst mod list` 或 `/dst players`）。

**Q: 连续签到怎么算中断？**

A: 连续签到以自然日为单位，若当天未签到则重新从 1 天计算。

**Q: 奖励可以自定义吗？**

A: 可以，通过后台配置奖励表（如果已启用相应管理功能）。未配置时使用默认奖励。
