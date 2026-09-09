/**
 * StopRunButton — 标题栏最右那个「结束运行」。
 *
 * 它结束的是这场会话此刻在 tmux 里的运行，不是把会话删掉：记录还在，还能翻，只是
 * 不能再往里发话。人认为这一场已经谈完了，按它把那具还占着几百兆内存的壳收掉。
 *
 * **按钮恒可按，不预先探测会话在不在跑。** 打开一场会话是高频动作，为了让按钮亮或灭
 * 而每次都去问一趟 tmux，代价摊在每一次点击上；这个按钮一天按不了几次。代价是按下去
 * 才知道有没有关到，那句话由服务端如实说出来（「这一场没在跑」照说，NEVER 装作关掉了）。
 *
 * 两段确认问的不是同一件事：第一下问「你真要结束吗」，本地问，不出门；出门后若服务端
 * 说屏上还在干活——那一下什么都没动——换成问「它还在干活，仍要打断吗」。
 *
 * 手机上只留图标：那一行还挤着返回、标题和目录，一个按钮把标题挤没了得不偿失。
 */

import { useTranslation } from 'react-i18next';
import { Loader2, Power } from 'lucide-react';
import { useStopSessionRun, type StopPhase } from '@/hooks/useStopSessionRun';

interface StopRunButtonProps {
  sessionId: string;
  /** 真关掉之后调它——左栏那一行的状态该跟着变。 */
  onStopped?: () => void;
}

/** 每一档在按钮上写什么。结局那三档写的是刚发生的事，几秒后自己退回起始档。 */
const LABEL_KEY: Record<StopPhase, string> = {
  idle: 'workbench.stopRun.action',
  confirming: 'workbench.stopRun.confirm',
  busyConfirming: 'workbench.stopRun.forceConfirm',
  stopping: 'workbench.stopRun.stopping',
  stopped: 'workbench.stopRun.stopped',
  absent: 'workbench.stopRun.absent',
  failed: 'workbench.stopRun.failed',
};

/** 要人再按一次的两档才染色——那两档按下去会有后果，其余只是在陈述。 */
const ASKING: StopPhase[] = ['confirming', 'busyConfirming'];

export default function StopRunButton({ sessionId, onStopped }: StopRunButtonProps) {
  const { t } = useTranslation();
  const { phase, error, press, cancel } = useStopSessionRun(sessionId, { onStopped });

  const asking = ASKING.includes(phase);
  const tone = asking
    ? 'border-accent-warning/40 bg-accent-warning-10 text-accent-warning'
    : 'border-border-color text-text-muted hover:text-text-primary';

  return (
    <button
      type="button"
      onClick={press}
      onBlur={cancel}
      disabled={phase === 'stopping'}
      // 失败那一档把服务端的说法挂在悬停上：标题栏这一行放不下一句完整的报错，
      // 但那句话不能丢——人得知道是没找到会话还是 tmux 拒了。
      title={error || t('workbench.stopRun.hint')}
      aria-label={t('workbench.stopRun.action')}
      className={`flex shrink-0 items-center gap-1.5 rounded border px-2 py-1 text-[12px] transition-colors disabled:opacity-60 ${tone}`}
    >
      {phase === 'stopping' ? (
        <Loader2 size={13} className="animate-spin" />
      ) : (
        <Power size={13} />
      )}
      <span className="phone:hidden">{t(LABEL_KEY[phase])}</span>
    </button>
  );
}
