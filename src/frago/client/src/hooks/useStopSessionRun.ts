/**
 * useStopSessionRun — 结束当前这场会话在 tmux 里的运行。
 *
 * 走 `POST /api/workbench/sessions/{sid}/stop`。**这一侧不预先探测会话在不在跑**：
 * 打开一场会话是高频动作，为了让按钮亮或灭而每次都去问一趟 tmux，代价摊在每一次点击
 * 上；而这个按钮一天按不了几次。所以按钮恒可按，按下去才知道结果，结果由服务端如实
 * 说出来——没在跑就是没在跑，界面照说，NEVER 假装关掉了。
 *
 * 两段确认，两段问的不是同一件事：
 *
 * 1. 第一下只是「你真要结束吗」，本地问，不出门；
 * 2. 请求出门后若服务端说屏上还在干活，那一下**没有动任何东西**，页面换一句话再问
 *    ——这次问的是「它还在干活，仍要打断吗」。人再按才带 `force` 出门。
 *
 * 状态是一次性的，换会话时整个清空：上一场的「已结束」留在标题栏上，人会以为说的是
 * 眼下这一场。
 */

import { useCallback, useEffect, useRef, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/** 服务端对这一按的答复。三种结局的判读见 `outcome`。 */
export interface StopRunResult {
  sid: string;
  /** 找到了一具活着的 tmux 吗。为 false 时什么都没动。 */
  alive: boolean;
  /** 屏上还在干活。为 true 且 `stopped` 为 false 时，服务端刻意没动它。 */
  busy: boolean;
  stopped: boolean;
  /** 那场 tmux 的名字。没找到时为 null。 */
  name: string | null;
  /** 走的是池的驱逐（`pool`）还是 tmux（`tmux`）。 */
  via: string | null;
  error: string | null;
}

export async function stopSessionRun(sessionId: string, force: boolean): Promise<StopRunResult> {
  const res = await fetch(
    `${API_BASE_URL}/api/workbench/sessions/${encodeURIComponent(sessionId)}/stop`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force }),
    }
  );
  if (!res.ok) {
    let detail = String(res.status);
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === 'string' && body.detail) detail = body.detail;
    } catch {
      /* 响应不是 JSON，退回状态码 */
    }
    throw new Error(detail);
  }
  return (await res.json()) as StopRunResult;
}

/**
 * 按钮此刻处在哪一档。
 *
 * - `idle` 按钮就位，还没人碰它；
 * - `confirming` 人按了一下，等他再按一次坐实；
 * - `busyConfirming` 出门问过了，服务端说它还在干活、什么都没动，等人决定打不打断；
 * - `stopping` 请求在飞；
 * - `stopped` / `absent` / `failed` 三种结局，各说各的话。
 */
export type StopPhase =
  | 'idle'
  | 'confirming'
  | 'busyConfirming'
  | 'stopping'
  | 'stopped'
  | 'absent'
  | 'failed';

/** 结局那几档自己退场的时长。留着不走的话，下一次再看标题栏会以为它在说此刻的事。 */
const SETTLE_MS = 4000;

/** 第一下确认等多久没有下文就当他改主意了。 */
const CONFIRM_MS = 5000;

export interface StopSessionRunState {
  phase: StopPhase;
  /** 失败时服务端的说法，原样转述。 */
  error: string | null;
  /** 按一下。按在哪一档上决定这一下是问、是出门、还是带 force 出门。 */
  press: () => void;
  /** 撤回确认（人点到别处去了）。 */
  cancel: () => void;
}

export interface UseStopSessionRunOptions {
  /** 真关掉之后调它——左栏那一行的状态该跟着变。 */
  onStopped?: () => void;
}

export function useStopSessionRun(
  sessionId: string | null,
  { onStopped }: UseStopSessionRunOptions = {}
): StopSessionRunState {
  const [phase, setPhase] = useState<StopPhase>('idle');
  const [error, setError] = useState<string | null>(null);
  const mounted = useRef(true);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onStoppedRef = useRef(onStopped);
  onStoppedRef.current = onStopped;

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      if (timer.current !== null) clearTimeout(timer.current);
    };
  }, []);

  // 换会话就整个归零：上一场的结局跟这一场没有任何关系。
  useEffect(() => {
    if (timer.current !== null) clearTimeout(timer.current);
    setPhase('idle');
    setError(null);
  }, [sessionId]);

  const settle = useCallback((next: StopPhase) => {
    setPhase(next);
    if (timer.current !== null) clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      if (mounted.current) setPhase('idle');
    }, SETTLE_MS);
  }, []);

  const fire = useCallback(
    async (force: boolean) => {
      if (!sessionId) return;
      if (timer.current !== null) clearTimeout(timer.current);
      setPhase('stopping');
      setError(null);
      try {
        const result = await stopSessionRun(sessionId, force);
        if (!mounted.current) return;
        if (!result.alive) {
          settle('absent');
          return;
        }
        if (!result.stopped && result.busy) {
          // 服务端一个字都没动它，这一档不设自退——人得自己决定打不打断。
          setPhase('busyConfirming');
          return;
        }
        if (!result.stopped) {
          setError(result.error);
          settle('failed');
          return;
        }
        settle('stopped');
        onStoppedRef.current?.();
      } catch (e) {
        if (!mounted.current) return;
        setError(e instanceof Error ? e.message : String(e));
        settle('failed');
      }
    },
    [sessionId, settle]
  );

  const press = useCallback(() => {
    if (!sessionId || phase === 'stopping') return;
    if (phase === 'confirming') {
      void fire(false);
      return;
    }
    if (phase === 'busyConfirming') {
      void fire(true);
      return;
    }
    // 结局那几档上再按，等于重新起一轮：先回到「你真要结束吗」。
    setPhase('confirming');
    setError(null);
    if (timer.current !== null) clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      if (mounted.current) setPhase('idle');
    }, CONFIRM_MS);
  }, [sessionId, phase, fire]);

  const cancel = useCallback(() => {
    if (phase !== 'confirming' && phase !== 'busyConfirming') return;
    if (timer.current !== null) clearTimeout(timer.current);
    setPhase('idle');
  }, [phase]);

  return { phase, error, press, cancel };
}
