/**
 * SessionLaunchPanel — 中栏在「会话还没起来」这段时间里摆的那块东西。
 *
 * 人点完创建，对话框就关了。从那一刻到左栏长出新的一行，中间将近十秒界面上什么都没有——
 * 这块就是那十秒的去处：他刚打的那句话在这儿摆着，旁边写清楚此刻在等什么。
 *
 * 视觉上接着输入区那套信封的说法：**已经发出去、还没落进会话的东西，都装在信封里。**
 * 区别只在信封上写的是哪一句——输入区那两档说的是"这句话在哪"，这里说的是"这场会话
 * 起到哪一步了"。
 *
 * 两档各自的样子：
 *
 * | 档 | 在等什么 | 样子 |
 * |---|---|---|
 * | 正在认领编号 | 会话进程刚起，还没报出编号 | 第一步在转，第二步是灰的 |
 * | 正在启动 | 编号有了，还没写下第一笔 | 第一步打勾，第二步在转 |
 *
 * 没起来那一档不自己消失：原因和那句话都留在人眼前，由他自己收掉——一关了之，人连
 * 刚才打的字都找不回来。
 */

import { useTranslation } from 'react-i18next';
import { Check, Loader2, Mail, X } from 'lucide-react';
import type { SessionLaunch } from '@/hooks/useSessionLaunch';

export interface SessionLaunchPanelProps {
  launch: SessionLaunch;
  /** 人把没起来的那张卡收掉。 */
  onDismiss: () => void;
}

/** 一步走到哪了：还没轮到、正在走、已经过去。 */
type StepState = 'waiting' | 'active' | 'done';

function Step({ state, label }: { state: StepState; label: string }) {
  return (
    <div
      data-testid="launch-step"
      data-state={state}
      className={`flex items-center gap-2 text-[12px] ${
        state === 'waiting' ? 'text-text-muted' : 'text-text-secondary'
      }`}
    >
      <span className="flex h-4 w-4 shrink-0 items-center justify-center">
        {state === 'done' ? (
          <Check size={13} className="text-accent-primary" />
        ) : state === 'active' ? (
          <Loader2 size={13} className="animate-spin text-accent-primary" />
        ) : (
          <span className="h-1.5 w-1.5 rounded-full bg-text-muted" />
        )}
      </span>
      <span>{label}</span>
    </div>
  );
}

export default function SessionLaunchPanel({ launch, onDismiss }: SessionLaunchPanelProps) {
  const { t } = useTranslation();
  const failed = launch.phase === 'failed';
  const claiming = launch.phase === 'claiming';

  return (
    <div className="flex h-full min-h-0 items-center justify-center overflow-y-auto px-5 py-6">
      <div
        data-testid="session-launch"
        data-phase={launch.phase}
        className={`flex w-full max-w-[520px] flex-col gap-3.5 rounded-[14px] border px-5 py-5 ${
          failed
            ? 'border-accent-error bg-accent-error-10'
            : 'border-border-accent bg-accent-primary-10'
        }`}
      >
        <div className="flex items-center gap-2.5">
          <span
            className={`flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-[10px] ${
              failed
                ? 'bg-accent-error text-[var(--text-on-accent)]'
                : 'bg-accent-primary text-[var(--text-on-accent)]'
            }`}
          >
            <Mail size={17} strokeWidth={2} />
          </span>
          <div className="flex min-w-0 flex-1 flex-col">
            <span
              className={`truncate text-[13px] font-semibold ${
                failed ? 'text-accent-error' : 'text-text-primary'
              }`}
            >
              {failed
                ? t('workbench.launch.failedTitle')
                : t('workbench.launch.title', { name: launch.agentName })}
            </span>
            <span className="truncate font-mono text-[11px] text-text-muted">{launch.cwd}</span>
          </div>
          {failed ? (
            <button
              type="button"
              data-testid="launch-dismiss"
              onClick={onDismiss}
              aria-label={t('workbench.launch.dismiss')}
              className="shrink-0 rounded-[6px] p-1 text-text-muted hover:bg-bg-hover hover:text-text-primary"
            >
              <X size={14} />
            </button>
          ) : null}
        </div>

        {/* 他刚打的那句话。等待期间界面上只有这一样东西是他自己的，摆出来才知道等的是什么。 */}
        {launch.text ? (
          <div className="rounded-[10px] border border-border-color bg-bg-card px-3 py-2">
            <p className="mb-1 text-[11px] text-text-muted">
              {t('workbench.launch.firstMessage')}
            </p>
            <p
              data-testid="launch-first-message"
              className="max-h-[120px] overflow-y-auto whitespace-pre-wrap break-words text-[12px] leading-5 text-text-secondary"
            >
              {launch.text}
            </p>
          </div>
        ) : null}

        {failed ? (
          <p data-testid="launch-error" className="text-[12px] leading-5 text-accent-error">
            {t('workbench.launch.failed', { reason: launch.error ?? '' })}
          </p>
        ) : (
          <div className="flex flex-col gap-1.5">
            <Step
              state={claiming ? 'active' : 'done'}
              label={t('workbench.launch.stepClaim', { name: launch.agentName })}
            />
            <Step
              state={claiming ? 'waiting' : 'active'}
              label={t('workbench.launch.stepFirstRecord')}
            />
          </div>
        )}

        {!failed ? (
          <p className="text-[11px] leading-5 text-text-muted">{t('workbench.launch.hint')}</p>
        ) : null}
      </div>
    </div>
  );
}
