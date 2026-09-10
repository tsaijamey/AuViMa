/**
 * EnvironmentModal —— 跑 frago 需要的那一整套东西，各自装的是哪一版、外面出到哪一版，
 * 以及把它升上去。
 *
 * **这张清单照装机向导抄，不是这里现编的。** 装机时探测脚本查哪几样，这张表就报哪
 * 几样，再加上 frago 自己。两处对不上，用户装完看到的和事后查到的就成了两台机器。
 *
 * **升级是点一下就走的动作，不是一段说明。** 落后的那一格上直接挂按钮，头上还有一颗
 * 把所有落后的一次排进队。至于每样东西该怎么升——它现在是从哪儿装的、这台机器有哪些
 * 包管理器——由服务端派出去的 agent 按本机事实自己判断，界面不替它猜。
 *
 * **只有关闭按钮能关掉它。** 点周围收窗对一张要来回对照着读的表是个陷阱：人的视线在
 * 十几格之间移动，鼠标跟着落到格与格的空隙上，一点就没了。升级跑着的时候更是如此。
 *
 * **默认每行四格。** 四格是一屏能横着扫完、又不至于让每格窄到版本号折行的那个数；
 * 屏幕窄下去依次退到三格、两格、一格。
 */

import { useTranslation } from 'react-i18next';
import { ArrowUp, Check, Loader2, RefreshCw, X } from 'lucide-react';
import type { EnvironmentState, EnvironmentUpgradeState } from '@/hooks/useEnvironment';
import type { EnvironmentItem, EnvironmentUpgradeItemState } from '@/types/api';

interface Props {
  /** 版本表与升级进度都由左栏那颗按钮持有——它比这扇窗活得久，关窗不丢状态 */
  environment: EnvironmentState;
  upgrade: EnvironmentUpgradeState;
  onClose: () => void;
}

/** 分组的出场顺序：frago 自己、必装、选装、agent 命令行。 */
const GROUP_ORDER: Array<EnvironmentItem['group']> = ['frago', 'required', 'optional', 'agent'];

/**
 * 一格的状态。四档各自对应一句人话，颜色只给需要人动手的那两档——全都标上颜色，
 * 等于哪一档都没被标出来。
 */
type Tone = 'missing-required' | 'missing' | 'outdated' | 'current';

function toneOf(item: EnvironmentItem): Tone {
  if (!item.installed) return item.required ? 'missing-required' : 'missing';
  return item.outdated ? 'outdated' : 'current';
}

/**
 * 这一格能不能点升级。
 *
 * 落后的能升，没装的能装。frago 自己在本地构建的机器上不给按钮——那一格的两个数字
 * 比出来本来就是反的，按下去只会把本地构建覆盖成更旧的线上版。没有公开版本源的
 * （WorkBuddy）也不给：升到哪儿去都说不出来。
 */
function isUpgradable(item: EnvironmentItem, fragoSource: string): boolean {
  if (item.id === 'frago' && fragoSource === 'local') return false;
  if (!item.latest) return false;
  return item.outdated || !item.installed;
}

function formatCheckedAt(seconds: number | null): string {
  if (!seconds) return '';
  return new Date(seconds * 1000).toLocaleString(undefined, {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function EnvironmentModal({ environment, upgrade: job, onClose }: Props) {
  const { t } = useTranslation();
  const { data, loading, error, reload } = environment;
  const { status, upgrade, busy } = job;

  const items = data?.items ?? [];
  const fragoSource = data?.frago_source ?? 'unknown';
  const pending = items.filter((i) => isUpgradable(i, fragoSource));

  const groups = GROUP_ORDER.map((group) => ({
    group,
    rows: items.filter((i) => i.group === group),
  })).filter((g) => g.rows.length > 0);

  const stateOf = (id: string): EnvironmentUpgradeItemState | undefined => status?.items?.[id];

  /* 上一轮升级的下场，摆在最上面。
     升级关了窗还在跑，人回头再打开时最想知道的第一件事是「刚才那下成了没有」——
     那句话不该藏在某一格里等人自己去找。 */
  const done = status && !status.running && status.order.length > 0;
  const tally = done
    ? status.order.reduce(
        (acc, id) => {
          const state = status.items[id]?.state;
          if (state === 'ok') acc.ok += 1;
          else if (state === 'failed') acc.failed += 1;
          else acc.skipped += 1;
          return acc;
        },
        { ok: 0, failed: 0, skipped: 0 }
      )
    : null;

  return (
    // 遮罩不接点击：这扇窗只认关闭按钮，理由见文件开头。
    <div className="envc-overlay">
      <div className="envc-card" role="dialog" aria-modal="true" aria-label={t('envCheck.title')}>
        <div className="envc-header">
          <div className="envc-title">
            {t('envCheck.title')}
            <span className="envc-subtitle">
              {data?.checked_at
                ? t('envCheck.checkedAt', { time: formatCheckedAt(data.checked_at) })
                : t('envCheck.neverChecked')}
            </span>
          </div>
          <div className="envc-header-actions">
            {pending.length > 0 ? (
              <button
                type="button"
                className="envc-upgrade-all"
                onClick={() => void upgrade(pending.map((i) => i.id))}
                disabled={busy}
              >
                {busy ? <Loader2 size={13} className="cs-spin" /> : <ArrowUp size={13} />}
                {busy
                  ? t('envCheck.upgradingAll')
                  : t('envCheck.upgradeAll', { n: pending.length })}
              </button>
            ) : null}
            <button
              type="button"
              className="envc-icon-btn"
              onClick={() => void reload(true)}
              disabled={loading || busy}
              title={t('envCheck.refresh')}
              aria-label={t('envCheck.refresh')}
            >
              <RefreshCw size={14} className={loading ? 'cs-spin' : ''} />
            </button>
            <button
              type="button"
              className="envc-icon-btn"
              onClick={onClose}
              title={t('envCheck.close')}
              aria-label={t('envCheck.close')}
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {error ? <div className="envc-error">{error}</div> : null}

        {/* 升级是派 agent 去这台机器上真的装东西，不是界面里改个数字。说清楚它在干什么，
            人才知道为什么要等，以及等的时候机器上正在发生什么。 */}
        {busy ? <div className="envc-note envc-note--busy">{t('envCheck.busyNote')}</div> : null}

        {/* 跑完那一轮的总账。失败的那几样底下各自写着卡在哪，这里只说数目和去哪看。 */}
        {tally ? (
          <div
            className={`envc-note ${tally.failed > 0 ? 'envc-note--failed' : 'envc-note--done'}`}
          >
            {t('envCheck.doneNote', {
              ok: tally.ok,
              failed: tally.failed,
              skipped: tally.skipped,
            })}
          </div>
        ) : null}

        {/* 开发机上的 frago 是自己构建装上去的，版本号通常比线上大。不说明这一句，
            那一格写着「本机 1.2.242 · 外面 1.2.0」会读成 frago 落后了。 */}
        {fragoSource === 'local' ? (
          <div className="envc-note">{t('envCheck.localBuildNote')}</div>
        ) : null}

        <div className="envc-body">
          {groups.length === 0 && !loading ? (
            <div className="envc-empty">{t('envCheck.empty')}</div>
          ) : null}

          {groups.map(({ group, rows }) => (
            <section key={group} className="envc-group">
              <h3 className="envc-group-title">{t(`envCheck.group.${group}`)}</h3>
              <div className="envc-grid">
                {rows.map((item) => {
                  const tone = toneOf(item);
                  const job = stateOf(item.id);
                  const upgradable = isUpgradable(item, fragoSource);
                  return (
                    <div key={item.id} className={`envc-cell envc-cell--${tone}`}>
                      <div className="envc-cell-head">
                        <span className={`envc-dot envc-dot--${tone}`} aria-hidden="true" />
                        <span className="envc-cell-name" title={item.name}>
                          {item.name}
                        </span>
                        {item.required ? (
                          <span className="envc-tag">{t('envCheck.tag.required')}</span>
                        ) : null}
                      </div>

                      {/* 当前版本是这一格的主角：人来这儿是要知道「我现在跑的是哪一版」。 */}
                      <div className="envc-cell-current">
                        {item.installed ? item.current ?? '—' : t('envCheck.notInstalled')}
                      </div>

                      <div className="envc-cell-latest">
                        {item.latest
                          ? t('envCheck.latest', { version: item.latest })
                          : t('envCheck.latestUnknown')}
                      </div>

                      {/* 这一格自己那一轮升级的下场，压在版本号底下。跑完了留在原地不清掉
                          ——人回头看的时候要知道刚才这一格到底成没成。 */}
                      {job ? (
                        <div className={`envc-cell-job envc-cell-job--${job.state}`}>
                          {job.state === 'running' ? (
                            <>
                              <Loader2 size={11} className="cs-spin" />
                              {t('envCheck.job.running')}
                            </>
                          ) : null}
                          {job.state === 'pending' ? t('envCheck.job.pending') : null}
                          {job.state === 'ok' ? (
                            <>
                              <Check size={11} />
                              {job.message || t('envCheck.job.ok')}
                            </>
                          ) : null}
                          {job.state === 'skipped' || job.state === 'failed'
                            ? job.message || t(`envCheck.job.${job.state}`)
                            : null}
                        </div>
                      ) : null}

                      {upgradable && job?.state !== 'ok' ? (
                        <button
                          type="button"
                          className="envc-cell-upgrade"
                          onClick={() => void upgrade([item.id])}
                          disabled={busy}
                        >
                          <ArrowUp size={12} />
                          {item.installed
                            ? t('envCheck.upgradeOne')
                            : t('envCheck.installOne')}
                        </button>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
