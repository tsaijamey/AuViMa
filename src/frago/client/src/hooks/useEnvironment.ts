/**
 * useEnvironment —— 环境仪表盘那张表。
 *
 * **进页面就问一次，问的是服务端的缓存。** 侧边栏那颗按钮上要显示「几项该看一眼」，
 * 那个数字得先有表才算得出来；而服务端把外面的版本号缓存了六小时，所以这一次请求
 * 落到网络上的概率很低。人点了刷新才是真的重问一遍。
 *
 * 问不到就当空表：这台机器可能根本没联网，那不是错误状态，不该在侧边栏上挂一个红点。
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  getEnvironment,
  getEnvironmentUpgradeStatus,
  startEnvironmentUpgrade,
} from '@/api';
import type { EnvironmentResponse, EnvironmentUpgradeResponse } from '@/types/api';

export interface EnvironmentState {
  data: EnvironmentResponse | null;
  loading: boolean;
  error: string | null;
  /** 重新问一遍。`refresh` 为真时连服务端的缓存一起作废。 */
  reload: (refresh?: boolean) => Promise<void>;
}

export function useEnvironment(): EnvironmentState {
  const [data, setData] = useState<EnvironmentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  const reload = useCallback(async (refresh = false) => {
    setLoading(true);
    setError(null);
    try {
      const result = await getEnvironment(refresh);
      if (alive.current) setData(result);
    } catch (e) {
      if (alive.current) setError(e instanceof Error ? e.message : String(e));
    } finally {
      if (alive.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload(false);
  }, [reload]);

  return { data, loading, error, reload };
}

/**
 * 侧边栏那颗按钮上的数字：缺了的必装项，加上能升的那些。
 *
 * 两件事合成一个数字，是因为按钮上只有一个角落写得下，而人看到它之后的动作是同一个
 * ——点开看看。分成两个数字得先解释哪个是哪个，那句话在 40px 宽的栏上没有地方写。
 */
export function countAttention(data: EnvironmentResponse | null): number {
  if (!data) return 0;
  return data.items.filter((i) => (i.required && !i.installed) || i.outdated).length;
}

/**
 * useEnvironmentUpgrade —— 那颗升级按钮按下去之后的事。
 *
 * **进度靠轮询，不靠推送。** 一样东西升完要花几十秒到几分钟（装包要下载），中间人多半
 * 把浮窗开着等；两秒问一次服务端够跟上，也不必为这一件事再开一条长连接。
 *
 * **跑完自动重新问一次版本号。** 升级的目的就是让表上那个数字变掉；还要人自己去点刷新
 * 才看得到新版本，等于没升完。
 */

/** 进度轮询的节拍。装包是分钟级的事，两秒一次已经比人眨眼快。 */
const UPGRADE_POLL_MS = 2000;

export interface EnvironmentUpgradeState {
  status: EnvironmentUpgradeResponse | null;
  /** 把这几样排进队。已经有一批在跑时服务端不受理，界面据此提示 */
  upgrade: (ids: string[]) => Promise<void>;
  busy: boolean;
}

export function useEnvironmentUpgrade(onFinished: () => void): EnvironmentUpgradeState {
  const [status, setStatus] = useState<EnvironmentUpgradeResponse | null>(null);
  const alive = useRef(true);
  // 回调放进 ref：它每轮渲染都是新函数，直接进依赖会把轮询定时器反复重建。
  const finished = useRef(onFinished);
  finished.current = onFinished;

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  // 一进来先问一次服务端：这一轮升级是谁发起的、界面开着没开着，都不影响它在跑。
  // 不问的话，关掉浮窗再打开就是一张干净的表——事情还在做，人却看不到任何痕迹，只能
  // 猜是不是断了。升级本来就是关了窗还继续的事，界面必须能重新接上它。
  useEffect(() => {
    void (async () => {
      try {
        const current = await getEnvironmentUpgradeStatus();
        if (alive.current && current.order.length > 0) setStatus(current);
      } catch {
        // 问不到就当没有正在跑的升级，界面照常显示版本表。
      }
    })();
  }, []);

  const running = status?.running ?? false;

  useEffect(() => {
    if (!running) return;
    let stop = false;
    const tick = async () => {
      try {
        const next = await getEnvironmentUpgradeStatus();
        if (stop || !alive.current) return;
        setStatus(next);
        if (!next.running) finished.current();
      } catch {
        // 问不到就等下一拍。升级在服务端跑着，界面这一次没问到不影响它。
      }
    };
    const timer = setInterval(tick, UPGRADE_POLL_MS);
    void tick();
    return () => {
      stop = true;
      clearInterval(timer);
    };
  }, [running]);

  const upgrade = useCallback(async (ids: string[]) => {
    if (ids.length === 0) return;
    try {
      const next = await startEnvironmentUpgrade(ids);
      if (alive.current) setStatus(next);
    } catch (e) {
      if (alive.current) {
        setStatus({
          accepted: false,
          running: false,
          order: ids,
          items: Object.fromEntries(
            ids.map((id) => [
              id,
              {
                state: 'failed',
                message: e instanceof Error ? e.message : String(e),
                before: null,
                after: null,
              },
            ])
          ),
          started_at: null,
          finished_at: null,
        });
      }
    }
  }, []);

  return { status, upgrade, busy: running };
}
