/**
 * useClaudeUsage — 本机 Claude Code 订阅额度。
 *
 * **界面不轮询。** 探测本身要跑一次 claude、花三秒钟，那是服务端每十分钟做一次的事；
 * 这边打开时读一次缓存，之后等服务端在数变了时推过来。额度一天变不了几次，让浏览器
 * 反复问同一个答案没有意义。
 *
 * 答不出的机器（没装 Claude Code、或者用 API key 而不是订阅）返回 `available: false`，
 * 界面据此整块不画。
 */

import { useCallback, useEffect, useState } from 'react';
import { getClaudeUsage } from '@/api';
import { MessageType } from '@/api/websocket';
import { useWebSocket } from './useWebSocket';
import type { ClaudeUsage } from '@/types/api';

const USAGE_TYPES = [MessageType.DATA_CLAUDE_USAGE];

export function useClaudeUsage(): ClaudeUsage | null {
  const [usage, setUsage] = useState<ClaudeUsage | null>(null);

  useEffect(() => {
    let alive = true;
    getClaudeUsage()
      .then((data) => {
        if (alive) setUsage(data);
      })
      .catch(() => {
        // 拿不到就当这台机器答不出：栏底少三根条子，不弹错。
        if (alive) setUsage(null);
      });
    return () => {
      alive = false;
    };
  }, []);

  const onMessage = useCallback((message: { data?: Record<string, unknown> }) => {
    const data = message.data?.data as ClaudeUsage | undefined;
    if (data) setUsage(data);
  }, []);

  useWebSocket({ messageTypes: USAGE_TYPES, onMessage });

  return usage;
}
